from pathlib import Path
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MASTER_DIR = PROJECT_ROOT / "data" / "master"
INCOMING_DIR = PROJECT_ROOT / "data" / "incoming"

MASTER_DIR.mkdir(parents=True, exist_ok=True)
INCOMING_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

START_DATE = "2026-08-01"
END_DATE = "2026-09-23"

TARGET_TRANSACTIONS = 120_000


# ============================================================
# MASTER DATA DIMENSIONS
# ============================================================

STORES = [
    "DXB-001",
    "DXB-002",
    "DXB-003",
    "DXB-004",
    "DXB-005",
]

REGIONS = {
    "DXB-001": "Dubai",
    "DXB-002": "Dubai",
    "DXB-003": "Dubai",
    "DXB-004": "Dubai",
    "DXB-005": "Dubai",
}

PRODUCTS = {
    "P001": ("Laptop", "Electronics", 2800),
    "P002": ("Smartphone", "Electronics", 1800),
    "P003": ("Headphones", "Electronics", 350),
    "P004": ("Monitor", "Electronics", 900),
    "P005": ("Keyboard", "Accessories", 180),
    "P006": ("Mouse", "Accessories", 100),
    "P007": ("Office Chair", "Furniture", 650),
    "P008": ("Desk", "Furniture", 800),
    "P009": ("Backpack", "Accessories", 220),
    "P010": ("Printer", "Office", 700),
    "P011": ("Notebook", "Stationery", 25),
    "P012": ("Pen Pack", "Stationery", 15),
    "P013": ("USB Drive", "Accessories", 45),
    "P014": ("Power Bank", "Electronics", 150),
    "P015": ("Tablet", "Electronics", 1200),
}

PAYMENT_METHODS = [
    "Card",
    "Cash",
    "Apple Pay",
    "Bank Transfer",
]

SALES_CHANNELS = [
    "Store",
    "Online",
]

CUSTOMER_COUNT = 8_000


# ============================================================
# GENERATE MASTER DATA
# ============================================================

def generate_master_data():
    print("=" * 60)
    print("WORKFLOW AUTOMATION HUB - DATA GENERATOR")
    print("=" * 60)

    dates = pd.date_range(
        start=START_DATE,
        end=END_DATE,
        freq="D"
    )

    print(f"Date range: {dates.min().date()} → {dates.max().date()}")
    print(f"Target transactions: {TARGET_TRANSACTIONS:,}")

    # Generate transaction dates
    transaction_dates = rng.choice(
        dates,
        size=TARGET_TRANSACTIONS,
        replace=True
    )

    # Store distribution
    store_ids = rng.choice(
        STORES,
        size=TARGET_TRANSACTIONS,
        p=[0.24, 0.21, 0.20, 0.18, 0.17]
    )

    # Products
    product_ids = rng.choice(
        list(PRODUCTS.keys()),
        size=TARGET_TRANSACTIONS,
        replace=True
    )

    customer_ids = rng.integers(
        1,
        CUSTOMER_COUNT + 1,
        size=TARGET_TRANSACTIONS
    )

    quantities = rng.choice(
        [1, 2, 3, 4, 5, 6],
        size=TARGET_TRANSACTIONS,
        p=[0.52, 0.25, 0.12, 0.06, 0.03, 0.02]
    )

    payment_methods = rng.choice(
        PAYMENT_METHODS,
        size=TARGET_TRANSACTIONS,
        p=[0.48, 0.20, 0.22, 0.10]
    )

    sales_channels = rng.choice(
        SALES_CHANNELS,
        size=TARGET_TRANSACTIONS,
        p=[0.72, 0.28]
    )

    # Product information
    product_names = np.array([
        PRODUCTS[p][0] for p in product_ids
    ])

    categories = np.array([
        PRODUCTS[p][1] for p in product_ids
    ])

    base_prices = np.array([
        PRODUCTS[p][2] for p in product_ids
    ], dtype=float)

    # Natural price variation
    unit_prices = base_prices * rng.normal(
        loc=1.0,
        scale=0.06,
        size=TARGET_TRANSACTIONS
    )

    unit_prices = np.maximum(unit_prices, 5)

    discount_pct = rng.choice(
        [0, 5, 10, 15, 20],
        size=TARGET_TRANSACTIONS,
        p=[0.35, 0.25, 0.22, 0.13, 0.05]
    )

    gross_amount = quantities * unit_prices

    discount_amount = gross_amount * (
        discount_pct / 100
    )

    net_revenue = gross_amount - discount_amount

    transaction_ids = np.array([
        f"TXN-{i:07d}"
        for i in range(1, TARGET_TRANSACTIONS + 1)
    ])

    df = pd.DataFrame({
        "transaction_id": transaction_ids,
        "transaction_date": pd.to_datetime(transaction_dates),
        "store_id": store_ids,
        "region": [REGIONS[s] for s in store_ids],
        "customer_id": [
            f"CUST-{c:05d}"
            for c in customer_ids
        ],
        "product_id": product_ids,
        "product_name": product_names,
        "category": categories,
        "quantity": quantities,
        "unit_price": np.round(unit_prices, 2),
        "discount_pct": discount_pct,
        "gross_amount": np.round(gross_amount, 2),
        "discount_amount": np.round(discount_amount, 2),
        "net_revenue": np.round(net_revenue, 2),
        "payment_method": payment_methods,
        "sales_channel": sales_channels,
    })

    df = df.sort_values(
        ["transaction_date", "transaction_id"]
    ).reset_index(drop=True)

    master_path = MASTER_DIR / "master_sales.csv"

    df.to_csv(
        master_path,
        index=False
    )

    print()
    print("MASTER DATA CREATED")
    print("-" * 60)
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Revenue: AED {df['net_revenue'].sum():,.2f}")
    print(f"Products: {df['product_id'].nunique():,}")
    print(f"Stores: {df['store_id'].nunique():,}")
    print(f"Customers: {df['customer_id'].nunique():,}")
    print(f"Saved: {master_path}")

    return df


# ============================================================
# CREATE DAILY INCOMING FILES
# ============================================================

def create_daily_files(df):
    print()
    print("=" * 60)
    print("CREATING DAILY INCOMING FILES")
    print("=" * 60)

    # Clear old generated incoming files
    for file in INCOMING_DIR.glob("*.csv"):
        file.unlink()

    dates = sorted(
        df["transaction_date"].dt.date.unique()
    )

    for date in dates:
        daily = df[
            df["transaction_date"].dt.date == date
        ].copy()

        filename = (
            f"sales_{pd.Timestamp(date):%Y-%m-%d}.csv"
        )

        daily.to_csv(
            INCOMING_DIR / filename,
            index=False
        )

        print(
            f"{filename} → {len(daily):,} rows"
        )

    print()
    print(f"Daily files created: {len(dates)}")


# ============================================================
# CONTROLLED TEST CASES
# ============================================================

def create_test_files(df):
    print()
    print("=" * 60)
    print("CREATING AUTOMATION TEST FILES")
    print("=" * 60)

    latest_date = df["transaction_date"].max()

    latest_data = df[
        df["transaction_date"] == latest_date
    ].copy()

    if latest_data.empty:
        latest_data = df.tail(1).copy()

    # --------------------------------------------------------
    # 1. VALID FILE
    # --------------------------------------------------------

    valid = latest_data.copy()

    valid.to_csv(
        INCOMING_DIR / "test_valid.csv",
        index=False
    )

    # --------------------------------------------------------
    # 2. DUPLICATE FILE
    # --------------------------------------------------------

    duplicate = pd.concat(
        [
            latest_data,
            latest_data.head(10)
        ],
        ignore_index=True
    )

    duplicate.to_csv(
        INCOMING_DIR / "test_duplicate.csv",
        index=False
    )

    # --------------------------------------------------------
    # 3. MISSING COLUMN
    # --------------------------------------------------------

    missing_column = latest_data.drop(
        columns=["net_revenue"]
    )

    missing_column.to_csv(
        INCOMING_DIR / "test_missing_column.csv",
        index=False
    )

    # --------------------------------------------------------
    # 4. MISSING VALUES
    # --------------------------------------------------------

    missing_values = latest_data.copy()

    if len(missing_values) >= 10:
        missing_values.loc[
            missing_values.index[:10],
            "product_id"
        ] = np.nan

        missing_values.loc[
            missing_values.index[:10],
            "net_revenue"
        ] = np.nan

    missing_values.to_csv(
        INCOMING_DIR / "test_missing_values.csv",
        index=False
    )

    # --------------------------------------------------------
    # 5. INVALID AMOUNT
    # --------------------------------------------------------

    invalid_amount = latest_data.copy()

    if len(invalid_amount) >= 5:
        invalid_amount.loc[
            invalid_amount.index[:5],
            "net_revenue"
        ] = -999

    invalid_amount.to_csv(
        INCOMING_DIR / "test_invalid_amount.csv",
        index=False
    )

    # --------------------------------------------------------
    # 6. REVENUE DROP SCENARIO
    # --------------------------------------------------------

    revenue_drop = latest_data.copy()

    if len(revenue_drop) > 0:
        revenue_drop["net_revenue"] = (
            revenue_drop["net_revenue"] * 0.55
        ).round(2)

    revenue_drop.to_csv(
        INCOMING_DIR / "test_revenue_drop.csv",
        index=False
    )

    test_files = [
        "test_valid.csv",
        "test_duplicate.csv",
        "test_missing_column.csv",
        "test_missing_values.csv",
        "test_invalid_amount.csv",
        "test_revenue_drop.csv",
    ]

    print()
    print("TEST FILES CREATED")

    for filename in test_files:
        path = INCOMING_DIR / filename
        test_df = pd.read_csv(path)

        print(
            f"{filename:<30} "
            f"{len(test_df):>8,} rows"
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    master_df = generate_master_data()
    create_daily_files(master_df)
    create_test_files(master_df)

    print()
    print("=" * 60)
    print("DATA GENERATION COMPLETED SUCCESSFULLY")
    print("=" * 60)