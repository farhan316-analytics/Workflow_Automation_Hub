from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INCOMING_DIR = PROJECT_ROOT / "data" / "incoming"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# TRANSFORMATION
# ============================================================

def transform_sales_data(df):
    """
    Transform validated sales data into
    analytics-ready format.
    """

    data = df.copy()

    # --------------------------------------------------------
    # STANDARDIZE COLUMN NAMES
    # --------------------------------------------------------

    data.columns = (
        data.columns
        .str.strip()
        .str.lower()
    )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    data["transaction_date"] = pd.to_datetime(
        data["transaction_date"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # NUMERIC COLUMNS
    # --------------------------------------------------------

    numeric_columns = [
        "quantity",
        "unit_price",
        "discount_pct",
        "gross_amount",
        "discount_amount",
        "net_revenue",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # TEXT STANDARDIZATION
    # --------------------------------------------------------

    text_columns = [
        "transaction_id",
        "store_id",
        "region",
        "customer_id",
        "product_id",
        "product_name",
        "category",
        "payment_method",
        "sales_channel",
    ]

    for column in text_columns:
        data[column] = (
            data[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------------
    # REMOVE DUPLICATE TRANSACTIONS
    # --------------------------------------------------------

    before_duplicates = len(data)

    data = data.drop_duplicates(
        subset=["transaction_id"],
        keep="first"
    )

    duplicates_removed = (
        before_duplicates - len(data)
    )

    # --------------------------------------------------------
    # RECALCULATE FINANCIAL VALUES
    # --------------------------------------------------------

    data["gross_amount"] = (
        data["quantity"]
        * data["unit_price"]
    ).round(2)

    data["discount_amount"] = (
        data["gross_amount"]
        * data["discount_pct"]
        / 100
    ).round(2)

    data["net_revenue"] = (
        data["gross_amount"]
        - data["discount_amount"]
    ).round(2)

    # --------------------------------------------------------
    # TIME FEATURES
    # --------------------------------------------------------

    data["year"] = (
        data["transaction_date"]
        .dt.year
    )

    data["month"] = (
        data["transaction_date"]
        .dt.month
    )

    data["month_name"] = (
        data["transaction_date"]
        .dt.month_name()
    )

    data["day"] = (
        data["transaction_date"]
        .dt.day
    )

    data["day_of_week"] = (
        data["transaction_date"]
        .dt.day_name()
    )

    data["is_weekend"] = (
        data["transaction_date"]
        .dt.dayofweek >= 5
    )

    # --------------------------------------------------------
    # BUSINESS METRICS
    # --------------------------------------------------------

    data["order_value"] = (
        data["net_revenue"]
    ).round(2)

    data["revenue_per_unit"] = (
        data["net_revenue"]
        / data["quantity"]
    ).round(2)

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    data = data.sort_values(
        [
            "transaction_date",
            "transaction_id"
        ]
    ).reset_index(drop=True)

    return data, duplicates_removed


# ============================================================
# PROCESS ONE FILE
# ============================================================

def process_file(file_path):
    """
    Load and transform one CSV file.
    """

    file_path = Path(file_path)

    print()
    print("-" * 60)
    print(f"Processing: {file_path.name}")
    print("-" * 60)

    df = pd.read_csv(file_path)

    original_rows = len(df)

    transformed_df, duplicates_removed = (
        transform_sales_data(df)
    )

    output_file = (
        PROCESSED_DIR
        / f"processed_{file_path.name}"
    )

    transformed_df.to_csv(
        output_file,
        index=False
    )

    print(
        f"Input rows:       {original_rows:,}"
    )

    print(
        f"Duplicates removed: "
        f"{duplicates_removed:,}"
    )

    print(
        f"Output rows:      "
        f"{len(transformed_df):,}"
    )

    print(
        f"Revenue:          "
        f"AED {transformed_df['net_revenue'].sum():,.2f}"
    )

    print(
        f"Output: {output_file}"
    )

    return {
        "input_file": file_path.name,
        "input_rows": original_rows,
        "duplicates_removed": duplicates_removed,
        "output_rows": len(transformed_df),
        "output_file": str(output_file),
        "revenue": float(
            transformed_df["net_revenue"].sum()
        ),
    }


# ============================================================
# PROCESS ALL DAILY SALES FILES
# ============================================================

def process_daily_files():

    files = sorted(
        INCOMING_DIR.glob(
            "sales_*.csv"
        )
    )

    if not files:
        raise FileNotFoundError(
            "No daily sales files found."
        )

    results = []

    print("=" * 60)
    print("WORKFLOW AUTOMATION HUB")
    print("ETL TRANSFORMATION ENGINE")
    print("=" * 60)

    print(
        f"Daily files found: {len(files)}"
    )

    for file_path in files:

        result = process_file(
            file_path
        )

        results.append(result)

    return results


# ============================================================
# SUMMARY
# ============================================================

def print_summary(results):

    summary = pd.DataFrame(
        results
    )

    print()
    print("=" * 60)
    print("ETL TRANSFORMATION SUMMARY")
    print("=" * 60)

    print(
        f"Files processed: "
        f"{len(summary):,}"
    )

    print(
        f"Input rows: "
        f"{summary['input_rows'].sum():,}"
    )

    print(
        f"Duplicates removed: "
        f"{summary['duplicates_removed'].sum():,}"
    )

    print(
        f"Output rows: "
        f"{summary['output_rows'].sum():,}"
    )

    print(
        f"Total revenue: "
        f"AED {summary['revenue'].sum():,.2f}"
    )

    print()
    print("ETL STATUS: SUCCESS")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    results = process_daily_files()

    print_summary(
        results
    )