from pathlib import Path
import os

import pandas as pd
import psycopg2


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
# DATABASE CONNECTION
# ============================================================

def get_connection():

    if not DB_CONFIG["password"]:
        raise ValueError(
            "WORKFLOW_DB_PASSWORD environment variable "
            "is not set."
        )

    return psycopg2.connect(
        **DB_CONFIG
    )


# ============================================================
# LOAD DAILY TRANSACTION DATA
# ============================================================

def load_daily_transactions():

    connection = get_connection()

    query = """
        SELECT
            transaction_id,
            transaction_date,
            customer_id,
            quantity,
            net_revenue
        FROM analytics.sales_transactions
        ORDER BY transaction_date;
    """

    try:

        df = pd.read_sql_query(
            query,
            connection
        )

    finally:

        connection.close()

    if df.empty:
        raise ValueError(
            "No transaction data found."
        )

    return df


# ============================================================
# CALCULATE DAILY KPIs
# ============================================================

def calculate_daily_kpis(df):

    data = df.copy()

    data["transaction_date"] = pd.to_datetime(
        data["transaction_date"]
    )

    daily = (
        data
        .groupby("transaction_date")
        .agg(
            revenue=(
                "net_revenue",
                "sum"
            ),

            orders=(
                "transaction_id",
                "nunique"
            ),

            units_sold=(
                "quantity",
                "sum"
            ),

            unique_customers=(
                "customer_id",
                "nunique"
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # AVERAGE ORDER VALUE
    # --------------------------------------------------------

    daily["average_order_value"] = (
        daily["revenue"]
        / daily["orders"]
    )

    # --------------------------------------------------------
    # AVERAGE UNITS PER ORDER
    # --------------------------------------------------------

    daily["average_units_per_order"] = (
        daily["units_sold"]
        / daily["orders"]
    )

    # --------------------------------------------------------
    # GROWTH METRICS
    # --------------------------------------------------------

    daily = daily.sort_values(
        "transaction_date"
    ).reset_index(drop=True)

    daily["revenue_growth_pct"] = (
        daily["revenue"]
        .pct_change()
        .mul(100)
    )

    daily["order_growth_pct"] = (
        daily["orders"]
        .pct_change()
        .mul(100)
    )

    # First day has no previous day
    daily["revenue_growth_pct"] = (
        daily["revenue_growth_pct"]
        .fillna(0)
    )

    daily["order_growth_pct"] = (
        daily["order_growth_pct"]
        .fillna(0)
    )

    # --------------------------------------------------------
    # ROUND NUMERIC VALUES
    # --------------------------------------------------------

    numeric_columns = [
        "revenue",
        "average_order_value",
        "average_units_per_order",
        "revenue_growth_pct",
        "order_growth_pct",
    ]

    for column in numeric_columns:

        daily[column] = daily[column].round(2)

    return daily


# ============================================================
# WRITE KPI RESULTS TO POSTGRESQL
# ============================================================

def write_daily_kpis(daily):

    connection = get_connection()

    delete_sql = """
        DELETE FROM analytics.daily_kpis
        WHERE kpi_date = ANY(%s);
    """

    insert_sql = """
        INSERT INTO analytics.daily_kpis (
            kpi_date,
            revenue,
            orders,
            units_sold,
            average_order_value,
            average_units_per_order,
            unique_customers,
            revenue_growth_pct,
            order_growth_pct
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        );
    """

    try:

        with connection.cursor() as cursor:

            dates = [
                row.transaction_date.date()
                for row in daily.itertuples()
            ]

            cursor.execute(
                delete_sql,
                (dates,)
            )

            records = [
                (
                    row.transaction_date.date(),
                    float(row.revenue),
                    int(row.orders),
                    int(row.units_sold),
                    float(
                        row.average_order_value
                    ),
                    float(
                        row.average_units_per_order
                    ),
                    int(row.unique_customers),
                    float(
                        row.revenue_growth_pct
                    ),
                    float(
                        row.order_growth_pct
                    ),
                )
                for row in daily.itertuples()
            ]

            cursor.executemany(
                insert_sql,
                records
            )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()

    return len(daily)


# ============================================================
# VERIFY KPI TABLE
# ============================================================

def verify_kpis():

    connection = get_connection()

    query = """
        SELECT
            COUNT(*) AS days,
            MIN(kpi_date) AS first_date,
            MAX(kpi_date) AS last_date,
            SUM(revenue) AS total_revenue,
            SUM(orders) AS total_orders,
            SUM(units_sold) AS total_units
        FROM analytics.daily_kpis;
    """

    try:

        with connection.cursor() as cursor:

            cursor.execute(query)

            result = cursor.fetchone()

    finally:

        connection.close()

    return result


# ============================================================
# PRINT LATEST KPI
# ============================================================

def print_latest_kpi():

    connection = get_connection()

    query = """
        SELECT
            kpi_date,
            revenue,
            orders,
            units_sold,
            average_order_value,
            average_units_per_order,
            unique_customers,
            revenue_growth_pct,
            order_growth_pct
        FROM analytics.daily_kpis
        ORDER BY kpi_date DESC
        LIMIT 1;
    """

    try:

        with connection.cursor() as cursor:

            cursor.execute(query)

            result = cursor.fetchone()

    finally:

        connection.close()

    print()
    print("=" * 60)
    print("LATEST DAILY KPI")
    print("=" * 60)

    print(
        f"Date: "
        f"{result[0]}"
    )

    print(
        f"Revenue: "
        f"AED {result[1]:,.2f}"
    )

    print(
        f"Orders: "
        f"{result[2]:,}"
    )

    print(
        f"Units sold: "
        f"{result[3]:,}"
    )

    print(
        f"Average order value: "
        f"AED {result[4]:,.2f}"
    )

    print(
        f"Average units/order: "
        f"{result[5]:.2f}"
    )

    print(
        f"Unique customers: "
        f"{result[6]:,}"
    )

    print(
        f"Revenue growth: "
        f"{result[7]:.2f}%"
    )

    print(
        f"Order growth: "
        f"{result[8]:.2f}%"
    )


# ============================================================
# MAIN KPI WORKFLOW
# ============================================================

def run_kpi_engine():

    print("=" * 60)
    print("WORKFLOW AUTOMATION HUB")
    print("AUTOMATED KPI ENGINE")
    print("=" * 60)

    print()
    print("Loading transaction data...")

    transactions = load_daily_transactions()

    print(
        f"Transactions loaded: "
        f"{len(transactions):,}"
    )

    print()
    print("Calculating daily KPIs...")

    daily = calculate_daily_kpis(
        transactions
    )

    print(
        f"Days calculated: "
        f"{len(daily):,}"
    )

    print()
    print("Writing KPIs to PostgreSQL...")

    rows_written = write_daily_kpis(
        daily
    )

    print(
        f"KPI rows written: "
        f"{rows_written:,}"
    )

    verification = verify_kpis()

    print()
    print("=" * 60)
    print("KPI DATABASE VERIFICATION")
    print("=" * 60)

    print(
        f"Days: "
        f"{verification[0]:,}"
    )

    print(
        f"First date: "
        f"{verification[1]}"
    )

    print(
        f"Last date: "
        f"{verification[2]}"
    )

    print(
        f"Total revenue: "
        f"AED {verification[3]:,.2f}"
    )

    print(
        f"Total orders: "
        f"{verification[4]:,}"
    )

    print(
        f"Total units: "
        f"{verification[5]:,}"
    )

    print_latest_kpi()

    print()
    print("=" * 60)
    print("KPI ENGINE STATUS: SUCCESS")
    print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    run_kpi_engine()