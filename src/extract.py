from pathlib import Path

import pandas as pd

from config import RAW_INPUT_PATH


# ============================================================
# Required source columns
# ============================================================

REQUIRED_COLUMNS = {
    "sale_id",
    "sale_date",
    "customer_id",
    "customer_first_name",
    "customer_last_name",
    "customer_email",
    "customer_phone",
    "customer_city",
    "customer_signup_date",
    "product_id",
    "product_name",
    "category_name",
    "unit_cost",
    "unit_price",
    "branch_id",
    "branch_name",
    "branch_city",
    "sales_channel",
    "quantity",
    "discount_percent",
    "payment_method",
    "inventory_snapshot_date",
    "stock_quantity",
    "reorder_level",
}


# ============================================================
# Profiling
# ============================================================

def create_profiling_summary(df):
    """
    Create an initial profiling summary for the raw dataset.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw transaction data.

    Returns
    -------
    dict
        Profiling information including row count, column count,
        null counts, duplicate count, and numeric statistics.
    """

    numeric_columns = df.select_dtypes(
        include=["number"]
    ).columns

    numeric_statistics = {}

    if len(numeric_columns) > 0:
        numeric_statistics = (
            df[numeric_columns]
            .describe()
            .transpose()
            .round(2)
            .to_dict("index")
        )

    profiling = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "null_counts": df.isnull().sum().to_dict(),
        "duplicate_count": int(df.duplicated().sum()),
        "numeric_statistics": numeric_statistics,
    }

    return profiling


# ============================================================
# Required column validation
# ============================================================

def validate_required_columns(df):
    """
    Validate that all required columns exist in the raw dataset.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw transaction data.

    Raises
    ------
    ValueError
        If one or more required columns are missing.
    """

    actual_columns = set(df.columns)

    missing_columns = sorted(
        REQUIRED_COLUMNS - actual_columns
    )

    if missing_columns:
        raise ValueError(
            "Raw dataset is missing required columns: "
            + ", ".join(missing_columns)
        )


# ============================================================
# Main extraction function
# ============================================================

def extract_data():
    """
    Read and profile the raw retail transaction CSV file.

    Returns
    -------
    tuple
        A tuple containing:

        - pandas.DataFrame
            Raw transaction data.
        - dict
            Initial profiling summary.
    """

    if not RAW_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Raw input file not found: {RAW_INPUT_PATH}"
        )

    print("Reading raw data...")
    print(f"Input file: {RAW_INPUT_PATH}")

    df = pd.read_csv(RAW_INPUT_PATH)

    print(
        f"Raw data loaded: {len(df):,} rows"
    )

    print(
        f"Raw data columns: {len(df.columns):,}"
    )

    # --------------------------------------------------------
    # Validate required columns
    # --------------------------------------------------------

    validate_required_columns(df)

    print(
        "Required column validation: PASSED"
    )

    # --------------------------------------------------------
    # Create profiling summary
    # --------------------------------------------------------

    profiling = create_profiling_summary(df)

    print("\n## Raw Data Profiling")

    print(
        f"Rows: {profiling['row_count']:,}"
    )

    print(
        f"Columns: {profiling['column_count']:,}"
    )

    print(
        f"Duplicate rows: {profiling['duplicate_count']:,}"
    )

    null_columns = {
        column: count
        for column, count in profiling["null_counts"].items()
        if count > 0
    }

    if null_columns:
        print("\nColumns containing null values:")

        for column, count in null_columns.items():
            print(
                f"  {column}: {count:,}"
            )
    else:
        print(
            "\nNull values: none"
        )

    if profiling["numeric_statistics"]:
        print(
            "\nNumeric column statistics:"
        )

        for column, statistics in (
            profiling["numeric_statistics"].items()
        ):
            print(
                f"  {column}: "
                f"min={statistics.get('min')}, "
                f"max={statistics.get('max')}, "
                f"mean={statistics.get('mean')}"
            )

    return df, profiling
