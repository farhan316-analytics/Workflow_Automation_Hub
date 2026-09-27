from pathlib import Path
import os

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": os.getenv(
        "WORKFLOW_DB_HOST",
        "localhost"
    ),
    "port": os.getenv(
        "WORKFLOW_DB_PORT",
        "5432"
    ),
    "database": os.getenv(
        "WORKFLOW_DB_NAME",
        "workflow_automation"
    ),
    "user": os.getenv(
        "WORKFLOW_DB_USER",
        "postgres"
    ),
    "password": os.getenv(
        "WORKFLOW_DB_PASSWORD"
    ),
}


# ============================================================
# CONNECTION
# ============================================================

def get_connection():
    """
    Create a PostgreSQL connection.
    """

    if not DB_CONFIG["password"]:
        raise ValueError(
            "WORKFLOW_DB_PASSWORD environment variable "
            "is not set."
        )

    return psycopg2.connect(
        **DB_CONFIG
    )


# ============================================================
# LOAD ONE FILE
# ============================================================

def load_file(file_path):
    """
    Load one processed CSV into PostgreSQL.
    """

    file_path = Path(file_path)

    print()
    print("-" * 60)
    print(f"Loading: {file_path.name}")
    print("-" * 60)

    df = pd.read_csv(
        file_path
    )

    # Convert date
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce"
    ).dt.date

    # Convert NaN → None for PostgreSQL
    df = df.where(
        pd.notna(df),
        None
    )

    columns = [
        "transaction_id",
        "transaction_date",
        "store_id",
        "region",
        "customer_id",
        "product_id",
        "product_name",
        "category",
        "quantity",
        "unit_price",
        "discount_pct",
        "gross_amount",
        "discount_amount",
        "net_revenue",
        "payment_method",
        "sales_channel",
        "year",
        "month",
        "month_name",
        "day",
        "day_of_week",
        "is_weekend",
        "order_value",
        "revenue_per_unit",
    ]

    records = [
        tuple(row)
        for row in df[columns].itertuples(
            index=False,
            name=None
        )
    ]

    insert_sql = """
        INSERT INTO analytics.sales_transactions (
            transaction_id,
            transaction_date,
            store_id,
            region,
            customer_id,
            product_id,
            product_name,
            category,
            quantity,
            unit_price,
            discount_pct,
            gross_amount,
            discount_amount,
            net_revenue,
            payment_method,
            sales_channel,
            year,
            month,
            month_name,
            day,
            day_of_week,
            is_weekend,
            order_value,
            revenue_per_unit
        )
        VALUES %s
        ON CONFLICT (transaction_id)
        DO NOTHING;
    """

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            execute_values(
                cursor,
                insert_sql,
                records,
                page_size=1000
            )

            inserted_rows = cursor.rowcount

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()

    print(
        f"Input rows: {len(df):,}"
    )

    print(
        f"Rows inserted: {inserted_rows:,}"
    )

    print(
        "Status: SUCCESS"
    )

    return inserted_rows


# ============================================================
# LOAD ALL PROCESSED FILES
# ============================================================

def load_all_files():

    files = sorted(
        PROCESSED_DIR.glob(
            "processed_sales_*.csv"
        )
    )

    if not files:
        raise FileNotFoundError(
            "No processed sales files found."
        )

    print("=" * 60)
    print("POSTGRESQL SALES LOADER")
    print("=" * 60)

    print(
        f"Processed files found: "
        f"{len(files)}"
    )

    total_inserted = 0

    for file_path in files:

        inserted = load_file(
            file_path
        )

        total_inserted += inserted

    print()
    print("=" * 60)
    print("DATABASE LOAD COMPLETE")
    print("=" * 60)

    print(
        f"Files processed: "
        f"{len(files):,}"
    )

    print(
        f"Total rows inserted: "
        f"{total_inserted:,}"
    )

    return total_inserted


# ============================================================
# DATABASE VERIFICATION
# ============================================================

def verify_database():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_rows,
                    COUNT(DISTINCT transaction_id)
                    AS unique_transactions,
                    MIN(transaction_date)
                    AS first_date,
                    MAX(transaction_date)
                    AS last_date,
                    SUM(net_revenue)
                    AS total_revenue
                FROM analytics.sales_transactions;
                """
            )

            result = cursor.fetchone()

    finally:

        connection.close()

    print()
    print("=" * 60)
    print("DATABASE VERIFICATION")
    print("=" * 60)

    print(
        f"Total rows: "
        f"{result[0]:,}"
    )

    print(
        f"Unique transactions: "
        f"{result[1]:,}"
    )

    print(
        f"First date: "
        f"{result[2]}"
    )

    print(
        f"Last date: "
        f"{result[3]}"
    )

    print(
        f"Total revenue: "
        f"AED {result[4]:,.2f}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    load_all_files()

    verify_database()