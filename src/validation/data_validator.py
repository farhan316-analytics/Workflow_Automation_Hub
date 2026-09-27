from pathlib import Path
import pandas as pd

from src.ingestion.file_ingestion import (
    REQUIRED_COLUMNS,
    load_csv,
)


# ============================================================
# VALIDATION CONFIGURATION
# ============================================================

REQUIRED_NUMERIC_COLUMNS = [
    "quantity",
    "unit_price",
    "discount_pct",
    "gross_amount",
    "discount_amount",
    "net_revenue",
]

ALLOWED_PAYMENT_METHODS = {
    "Card",
    "Cash",
    "Apple Pay",
    "Bank Transfer",
}

ALLOWED_SALES_CHANNELS = {
    "Store",
    "Online",
}

CRITICAL_COLUMNS = [
    "transaction_id",
    "transaction_date",
    "store_id",
    "product_id",
    "quantity",
    "unit_price",
    "net_revenue",
]


# ============================================================
# VALIDATOR
# ============================================================

class DataValidator:

    def __init__(self, dataframe):
        self.df = dataframe.copy()

        self.errors = []
        self.warnings = []

    # --------------------------------------------------------
    # ERROR / WARNING HELPERS
    # --------------------------------------------------------

    def add_error(self, message):
        self.errors.append(message)

    def add_warning(self, message):
        self.warnings.append(message)

    # --------------------------------------------------------
    # SCHEMA VALIDATION
    # --------------------------------------------------------

    def validate_schema(self):

        missing_columns = [
            column
            for column in REQUIRED_COLUMNS
            if column not in self.df.columns
        ]

        if missing_columns:
            self.add_error(
                "Missing required columns: "
                + ", ".join(missing_columns)
            )

    # --------------------------------------------------------
    # EMPTY FILE
    # --------------------------------------------------------

    def validate_not_empty(self):

        if self.df.empty:
            self.add_error(
                "Input file contains no records."
            )

    # --------------------------------------------------------
    # DUPLICATE TRANSACTIONS
    # --------------------------------------------------------

    def validate_duplicates(self):

        if "transaction_id" not in self.df.columns:
            return

        duplicate_count = self.df[
            "transaction_id"
        ].duplicated().sum()

        if duplicate_count > 0:
            self.add_warning(
                f"{duplicate_count:,} duplicate "
                "transaction IDs detected."
            )

    # --------------------------------------------------------
    # MISSING VALUES
    # --------------------------------------------------------

    def validate_missing_values(self):

        available_columns = [
            column
            for column in CRITICAL_COLUMNS
            if column in self.df.columns
        ]

        for column in available_columns:

            missing_count = self.df[column].isna().sum()

            if missing_count == 0:
                continue

            percentage = (
                missing_count / len(self.df)
            ) * 100

            message = (
                f"{column}: {missing_count:,} "
                f"missing values ({percentage:.2f}%)."
            )

            if percentage > 10:
                self.add_error(
                    "Critical missing-value level — "
                    + message
                )
            else:
                self.add_warning(message)

    # --------------------------------------------------------
    # NUMERIC VALIDATION
    # --------------------------------------------------------

    def validate_numeric_columns(self):

        for column in REQUIRED_NUMERIC_COLUMNS:

            if column not in self.df.columns:
                continue

            numeric_values = pd.to_numeric(
                self.df[column],
                errors="coerce"
            )

            invalid_count = (
                numeric_values.isna()
                & self.df[column].notna()
            ).sum()

            if invalid_count > 0:
                self.add_error(
                    f"{column}: {invalid_count:,} "
                    "non-numeric values detected."
                )

    # --------------------------------------------------------
    # NEGATIVE VALUES
    # --------------------------------------------------------

    def validate_negative_values(self):

        if "quantity" in self.df.columns:

            negative_quantity = (
                pd.to_numeric(
                    self.df["quantity"],
                    errors="coerce"
                ) < 0
            ).sum()

            if negative_quantity > 0:
                self.add_error(
                    f"{negative_quantity:,} negative "
                    "quantity values detected."
                )

        if "net_revenue" in self.df.columns:

            negative_revenue = (
                pd.to_numeric(
                    self.df["net_revenue"],
                    errors="coerce"
                ) < 0
            ).sum()

            if negative_revenue > 0:
                self.add_error(
                    f"{negative_revenue:,} negative "
                    "revenue values detected."
                )

    # --------------------------------------------------------
    # DATE VALIDATION
    # --------------------------------------------------------

    def validate_dates(self):

        if "transaction_date" not in self.df.columns:
            return

        parsed_dates = pd.to_datetime(
            self.df["transaction_date"],
            errors="coerce"
        )

        invalid_dates = parsed_dates.isna().sum()

        if invalid_dates > 0:
            self.add_error(
                f"{invalid_dates:,} invalid transaction "
                "dates detected."
            )

    # --------------------------------------------------------
    # PAYMENT METHOD
    # --------------------------------------------------------

    def validate_payment_methods(self):

        if "payment_method" not in self.df.columns:
            return

        invalid = (
            ~self.df["payment_method"]
            .isin(ALLOWED_PAYMENT_METHODS)
            & self.df["payment_method"].notna()
        ).sum()

        if invalid > 0:
            self.add_warning(
                f"{invalid:,} unrecognized payment "
                "methods detected."
            )

    # --------------------------------------------------------
    # SALES CHANNEL
    # --------------------------------------------------------

    def validate_sales_channels(self):

        if "sales_channel" not in self.df.columns:
            return

        invalid = (
            ~self.df["sales_channel"]
            .isin(ALLOWED_SALES_CHANNELS)
            & self.df["sales_channel"].notna()
        ).sum()

        if invalid > 0:
            self.add_warning(
                f"{invalid:,} unrecognized sales "
                "channels detected."
            )

    # --------------------------------------------------------
    # RUN ALL VALIDATIONS
    # --------------------------------------------------------

    def validate(self):

        self.validate_schema()

        # If schema is broken, still run safe checks.
        self.validate_not_empty()
        self.validate_duplicates()
        self.validate_missing_values()
        self.validate_numeric_columns()
        self.validate_negative_values()
        self.validate_dates()
        self.validate_payment_methods()
        self.validate_sales_channels()

        if self.errors:
            status = "FAILED"
        elif self.warnings:
            status = "WARNING"
        else:
            status = "PASSED"

        return {
            "status": status,
            "rows_received": len(self.df),
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


# ============================================================
# VALIDATE FILE
# ============================================================

def validate_file(file_path):

    result = load_csv(file_path)

    validator = DataValidator(
        result["data"]
    )

    validation_result = validator.validate()

    validation_result.update({
        "file_name": result["file_name"],
        "file_path": result["file_path"],
        "duration_seconds": result[
            "duration_seconds"
        ],
    })

    return validation_result


# ============================================================
# PRINT RESULT
# ============================================================

def print_validation_result(result):

    print()
    print("=" * 60)
    print(
        f"VALIDATION: {result['file_name']}"
    )
    print("=" * 60)

    print(
        f"Status: {result['status']}"
    )

    print(
        f"Rows received: "
        f"{result['rows_received']:,}"
    )

    print(
        f"Errors: "
        f"{result['error_count']}"
    )

    print(
        f"Warnings: "
        f"{result['warning_count']}"
    )

    if result["errors"]:

        print()
        print("ERRORS:")

        for error in result["errors"]:
            print(f"❌ {error}")

    if result["warnings"]:

        print()
        print("WARNINGS:")

        for warning in result["warnings"]:
            print(f"⚠ {warning}")


# ============================================================
# TEST ALL INCOMING FILES
# ============================================================

if __name__ == "__main__":

    project_root = Path(__file__).resolve().parents[2]

    incoming_dir = (
        project_root
        / "data"
        / "incoming"
    )

    files = sorted(
        incoming_dir.glob("*.csv")
    )

    print("=" * 60)
    print("DATA QUALITY VALIDATION ENGINE")
    print("=" * 60)

    for file_path in files:

        result = validate_file(
            file_path
        )

        print_validation_result(
            result
        )