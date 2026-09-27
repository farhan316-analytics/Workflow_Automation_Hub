from pathlib import Path
from datetime import datetime
import pandas as pd


REQUIRED_COLUMNS = [
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
]


def discover_files(input_dir):
    """
    Discover CSV files waiting in the incoming directory.
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Incoming directory does not exist: {input_path}"
        )

    return sorted(input_path.glob("*.csv"))


def load_csv(file_path):
    """
    Load a CSV file into a pandas DataFrame.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if file_path.suffix.lower() != ".csv":
        raise ValueError(
            f"Unsupported file type: {file_path.suffix}"
        )

    started_at = datetime.now()

    df = pd.read_csv(file_path)

    finished_at = datetime.now()

    return {
        "file_path": str(file_path),
        "file_name": file_path.name,
        "data": df,
        "rows": len(df),
        "columns": len(df.columns),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": (
            finished_at - started_at
        ).total_seconds(),
    }


def inspect_file(file_path):
    """
    Return basic metadata about an incoming file.
    """
    result = load_csv(file_path)

    return {
        "file_name": result["file_name"],
        "rows": result["rows"],
        "columns": result["columns"],
        "column_names": list(
            result["data"].columns
        ),
        "duration_seconds": result[
            "duration_seconds"
        ],
    }


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    incoming_dir = project_root / "data" / "incoming"

    files = discover_files(incoming_dir)

    print("=" * 60)
    print("INCOMING FILE DISCOVERY")
    print("=" * 60)

    print(f"Files discovered: {len(files)}")

    for file in files:
        metadata = inspect_file(file)

        print(
            f"{metadata['file_name']:<35}"
            f"{metadata['rows']:>10,} rows"
        )