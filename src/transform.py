import pandas as pd

from config import (
    PROCESSED_DIR,
    REJECTED_DIR,
)


# ============================================================
# Helper functions
# ============================================================

def clean_text(series):
    """
    Clean text values.

    Operations:
    - convert to pandas string type
    - strip leading/trailing whitespace
    - convert common missing strings to pandas NA
    """

    series = (
        series
        .astype("string")
        .str.strip()
    )

    series = series.replace(
        {
            "": pd.NA,
            "nan": pd.NA,
            "None": pd.NA,
            "none": pd.NA,
            "NA": pd.NA,
            "N/A": pd.NA,
            "null": pd.NA,
            "NULL": pd.NA,
        }
    )

    return series


def normalize_city(series):
    """
    Normalize city names.

    Example:
        tehran -> Tehran
        TEHRAN -> Tehran
        shiraz -> Shiraz
    """

    return (
        clean_text(series)
        .str.replace(
            "_",
            " ",
            regex=False,
        )
        .str.replace(
            "-",
            " ",
            regex=False,
        )
        .str.replace(
            r"\s+",
            " ",
            regex=True,
        )
        .str.strip()
        .str.title()
    )


def normalize_category(series):
    """
    Normalize category names.

    Example:
        home_appliances -> Home Appliances
        HOME-APPLIANCES -> Home Appliances
    """

    return (
        clean_text(series)
        .str.replace(
            "_",
            " ",
            regex=False,
        )
        .str.replace(
            "-",
            " ",
            regex=False,
        )
        .str.replace(
            r"\s+",
            " ",
            regex=True,
        )
        .str.strip()
        .str.title()
    )


def convert_missing_values(dataframe):
    """
    Convert pandas missing values to Python None.

    This prevents psycopg2 errors such as:
        can't adapt type 'NAType'
    """

    dataframe = dataframe.astype(object)

    return dataframe.where(
        pd.notna(dataframe),
        None,
    )


def parse_mixed_date(series):
    """
    Parse mixed date formats used by the raw dataset.

    Supported formats include:
        YYYY-MM-DD
        YYYY/MM/DD
        DD-MM-YYYY
        MM/DD/YYYY
    """

    values = clean_text(series)

    result = pd.Series(
        pd.NaT,
        index=series.index,
        dtype="datetime64[ns]",
    )

    # --------------------------------------------------------
    # YYYY-MM-DD / YYYY/MM/DD
    # --------------------------------------------------------

    year_first_mask = (
        values.notna()
        & values.str.match(
            r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$",
            na=False,
        )
    )

    if year_first_mask.any():
        result.loc[
            year_first_mask
        ] = pd.to_datetime(
            values.loc[
                year_first_mask
            ],
            format="mixed",
            errors="coerce",
        )

    # --------------------------------------------------------
    # DD-MM-YYYY
    # --------------------------------------------------------

    dash_mask = (
        values.notna()
        & values.str.match(
            r"^\d{1,2}-\d{1,2}-\d{4}$",
            na=False,
        )
    )

    if dash_mask.any():
        result.loc[
            dash_mask
        ] = pd.to_datetime(
            values.loc[
                dash_mask
            ],
            format="%d-%m-%Y",
            errors="coerce",
        )

    # --------------------------------------------------------
    # MM/DD/YYYY
    # --------------------------------------------------------

    slash_mask = (
        values.notna()
        & values.str.match(
            r"^\d{1,2}/\d{1,2}/\d{4}$",
            na=False,
        )
    )

    if slash_mask.any():
        result.loc[
            slash_mask
        ] = pd.to_datetime(
            values.loc[
                slash_mask
            ],
            format="%m/%d/%Y",
            errors="coerce",
        )

    return result.dt.date


def most_common_value(series):
    """
    Return the most frequent non-null value.

    Used for entity conflict resolution.
    """

    values = series.dropna()

    if values.empty:
        return None

    counts = values.value_counts()

    return counts.index[0]


def build_dimension(
    dataframe,
    group_column,
    columns,
):
    """
    Build a dimension table using the most common value
    for conflicting descriptive attributes.

    This avoids blindly keeping the first occurrence
    when repeated entity records contain conflicting values.
    """

    records = []

    for entity_id, group in dataframe.groupby(
        group_column,
        dropna=False,
        sort=True,
    ):

        if pd.isna(entity_id):
            continue

        record = {
            group_column: entity_id,
        }

        for column in columns:
            record[column] = most_common_value(
                group[column]
            )

        records.append(record)

    return pd.DataFrame(records)


# ============================================================
# Required input columns
# ============================================================

def validate_input_columns(dataframe):
    """
    Verify that the raw CSV contains all required columns.
    """

    required_columns = [
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
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Raw dataset is missing required columns: "
            f"{missing_columns}"
        )


# ============================================================
# Save helper
# ============================================================

def save_processed_outputs(
    dim_categories,
    dim_products,
    dim_customers,
    dim_branches,
    fact_sales,
    fact_inventory_snapshot,
):
    """
    Save normalized processed CSV outputs.
    """

    outputs = {
        "dim_categories.csv": dim_categories,
        "dim_products.csv": dim_products,
        "dim_customers.csv": dim_customers,
        "dim_branches.csv": dim_branches,
        "fact_sales.csv": fact_sales,
        "fact_inventory_snapshot.csv": fact_inventory_snapshot,
    }

    for filename, dataframe in outputs.items():

        path = PROCESSED_DIR / filename

        dataframe.to_csv(
            path,
            index=False,
        )

        print(
            f"Saved processed file: {path}"
        )


# ============================================================
# Transform data
# ============================================================

def transform_data(dataframe):
    """
    Transform the denormalized raw retail dataset into
    normalized dimension and fact tables.
    """

    print()
    print("## Starting transformation...")
    print()

    # --------------------------------------------------------
    # Copy input
    # --------------------------------------------------------

    df = dataframe.copy()

    input_rows = len(df)

    # --------------------------------------------------------
    # Normalize column names
    # --------------------------------------------------------

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    validate_input_columns(df)

    # --------------------------------------------------------
    # Remove exact duplicate rows
    # --------------------------------------------------------

    duplicate_count = int(
        df.duplicated().sum()
    )

    df = (
        df
        .drop_duplicates()
        .copy()
    )

    # ========================================================
    # Clean text columns
    # ========================================================

    text_columns = [
        "sale_id",

        "customer_id",
        "customer_first_name",
        "customer_last_name",
        "customer_email",
        "customer_phone",

        "product_id",
        "product_name",

        "branch_id",
        "branch_name",

        "sales_channel",
        "payment_method",
    ]

    for column in text_columns:

        df[column] = clean_text(
            df[column]
        )

    # --------------------------------------------------------
    # Normalize customer city
    # --------------------------------------------------------

    df["customer_city"] = normalize_city(
        df["customer_city"]
    )

    # --------------------------------------------------------
    # Normalize branch city
    # --------------------------------------------------------

    df["branch_city"] = normalize_city(
        df["branch_city"]
    )

    # --------------------------------------------------------
    # Normalize category
    # --------------------------------------------------------

    df["category_name"] = normalize_category(
        df["category_name"]
    )

    # --------------------------------------------------------
    # Normalize product name
    # --------------------------------------------------------

    df["product_name"] = (
        clean_text(
            df["product_name"]
        )
        .str.replace(
            r"\s+",
            " ",
            regex=True,
        )
        .str.strip()
    )

    # --------------------------------------------------------
    # Normalize customer names
    # --------------------------------------------------------

    df["customer_first_name"] = (
        clean_text(
            df["customer_first_name"]
        )
        .str.title()
    )

    df["customer_last_name"] = (
        clean_text(
            df["customer_last_name"]
        )
        .str.title()
    )

    # --------------------------------------------------------
    # Normalize email
    # --------------------------------------------------------

    df["customer_email"] = (
        clean_text(
            df["customer_email"]
        )
        .str.lower()
    )

    # --------------------------------------------------------
    # Normalize sales channel
    # --------------------------------------------------------

    df["sales_channel"] = (
        clean_text(
            df["sales_channel"]
        )
        .str.lower()
    )

    # --------------------------------------------------------
    # Normalize payment method
    # --------------------------------------------------------

    df["payment_method"] = (
        clean_text(
            df["payment_method"]
        )
        .str.lower()
    )

    # ========================================================
    # Convert dates
    # ========================================================

    df["sale_date"] = parse_mixed_date(
        df["sale_date"]
    )

    df["customer_signup_date"] = (
        parse_mixed_date(
            df["customer_signup_date"]
        )
    )

    df["inventory_snapshot_date"] = (
        parse_mixed_date(
            df["inventory_snapshot_date"]
        )
    )

    # ========================================================
    # Convert numeric columns
    # ========================================================

    numeric_columns = [
        "quantity",
        "unit_cost",
        "unit_price",
        "discount_percent",
        "stock_quantity",
        "reorder_level",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # ========================================================
    # REJECTION LOG
    # ========================================================

    rejection_reason = pd.Series(
        "",
        index=df.index,
        dtype="string",
    )

    def reject(mask, reason):

        mask = mask.fillna(False)

        target = (
            mask
            & (
                rejection_reason
                == ""
            )
        )

        rejection_reason.loc[
            target
        ] = reason

    # ========================================================
    # SALES VALIDATION
    # ========================================================

    # --------------------------------------------------------
    # Required identifiers
    # --------------------------------------------------------

    reject(
        df["sale_id"].isna(),
        "missing_sale_id",
    )

    reject(
        df["sale_date"].isna(),
        "invalid_sale_date",
    )

    reject(
        df["customer_id"].isna(),
        "missing_customer_id",
    )

    reject(
        df["product_id"].isna(),
        "missing_product_id",
    )

    reject(
        df["branch_id"].isna(),
        "missing_branch_id",
    )

    # --------------------------------------------------------
    # Product fields
    # --------------------------------------------------------

    reject(
        df["product_name"].isna(),
        "missing_product_name",
    )

    reject(
        df["category_name"].isna(),
        "missing_category_name",
    )

    # --------------------------------------------------------
    # Branch fields
    # --------------------------------------------------------

    reject(
        df["branch_name"].isna(),
        "missing_branch_name",
    )

    reject(
        df["branch_city"].isna(),
        "missing_branch_city",
    )

    # --------------------------------------------------------
    # Sales channel
    # --------------------------------------------------------

    reject(
        df["sales_channel"].isna(),
        "missing_sales_channel",
    )

    reject(
        df["sales_channel"].notna()
        & ~df["sales_channel"].isin(
            [
                "online",
                "store",
                "mobile",
                "partner",
            ]
        ),
        "invalid_sales_channel",
    )

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    reject(
        df["quantity"].isna(),
        "missing_quantity",
    )

    reject(
        df["quantity"].notna()
        & (
            df["quantity"] <= 0
        ),
        "invalid_quantity",
    )

    # --------------------------------------------------------
    # Unit cost
    # --------------------------------------------------------

    reject(
        df["unit_cost"].isna(),
        "missing_unit_cost",
    )

    reject(
        df["unit_cost"].notna()
        & (
            df["unit_cost"] < 0
        ),
        "invalid_unit_cost",
    )

    # --------------------------------------------------------
    # Unit price
    # --------------------------------------------------------

    reject(
        df["unit_price"].isna(),
        "missing_unit_price",
    )

    reject(
        df["unit_price"].notna()
        & (
            df["unit_price"] < 0
        ),
        "invalid_unit_price",
    )

    # --------------------------------------------------------
    # Discount
    # --------------------------------------------------------

    reject(
        df["discount_percent"].isna(),
        "missing_discount_percent",
    )

    reject(
        df["discount_percent"].notna()
        & (
            (df["discount_percent"] < 0)
            | (
                df["discount_percent"] > 100
            )
        ),
        "invalid_discount_percent",
    )

    # --------------------------------------------------------
    # Payment method
    # --------------------------------------------------------

    reject(
        df["payment_method"].isna(),
        "missing_payment_method",
    )

    # --------------------------------------------------------
    # Duplicate sale ID
    # --------------------------------------------------------

    duplicate_sale_id_mask = (
        df["sale_id"].notna()
        & df["sale_id"].duplicated(
            keep="first"
        )
    )

    reject(
        duplicate_sale_id_mask,
        "duplicate_sale_id",
    )

    # ========================================================
    # Split sales into valid / rejected
    # ========================================================

    rejected_sales_mask = (
        rejection_reason != ""
    )

    rejected_sales = df.loc[
        rejected_sales_mask
    ].copy()

    rejected_sales[
        "rejection_reason"
    ] = rejection_reason.loc[
        rejected_sales_mask
    ]

    valid = df.loc[
        ~rejected_sales_mask
    ].copy()

    # ========================================================
    # Financial calculations
    # ========================================================

    valid["unit_cost"] = (
        valid["unit_cost"]
        .round(2)
    )

    valid["unit_price"] = (
        valid["unit_price"]
        .round(2)
    )

    valid["discount_percent"] = (
        valid["discount_percent"]
        .round(2)
    )

    valid["gross_revenue"] = (
        valid["quantity"]
        * valid["unit_price"]
    ).round(2)

    valid["discount_amount"] = (
        valid["gross_revenue"]
        * valid["discount_percent"]
        / 100
    ).round(2)

    valid["net_revenue"] = (
        valid["gross_revenue"]
        - valid["discount_amount"]
    ).round(2)

    valid["total_cost"] = (
        valid["quantity"]
        * valid["unit_cost"]
    ).round(2)

    valid["gross_profit"] = (
        valid["net_revenue"]
        - valid["total_cost"]
    ).round(2)

    valid["margin_percent"] = 0.0

    positive_revenue = (
        valid["net_revenue"] > 0
    )

    valid.loc[
        positive_revenue,
        "margin_percent",
    ] = (
        valid.loc[
            positive_revenue,
            "gross_profit",
        ]
        / valid.loc[
            positive_revenue,
            "net_revenue",
        ]
        * 100
    ).round(2)

    # ========================================================
    # DIMENSION: CATEGORIES
    # ========================================================

    category_names = (
        valid["category_name"]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    dim_categories = pd.DataFrame(
        {
            "category_id": [
                f"CAT{i:03d}"
                for i in range(
                    1,
                    len(category_names) + 1,
                )
            ],
            "category_name": category_names,
        }
    )

    dim_categories[
        "category_display_name"
    ] = (
        dim_categories[
            "category_name"
        ]
        .str.replace(
            "_",
            " ",
            regex=False,
        )
        .str.replace(
            "-",
            " ",
            regex=False,
        )
        .str.title()
    )

    category_lookup = dict(
        zip(
            dim_categories[
                "category_name"
            ],
            dim_categories[
                "category_id"
            ],
        )
    )

    valid["category_id"] = (
        valid["category_name"]
        .map(category_lookup)
    )

    # ========================================================
    # DIMENSION: PRODUCTS
    # ========================================================

    dim_products = build_dimension(
        valid,
        "product_id",
        [
            "product_name",
            "category_id",
            "category_name",
            "unit_cost",
            "unit_price",
        ],
    )

    dim_products = (
        dim_products
        .sort_values("product_id")
        .reset_index(drop=True)
    )

    # ========================================================
    # DIMENSION: CUSTOMERS
    # ========================================================

    dim_customers = build_dimension(
        valid,
        "customer_id",
        [
            "customer_first_name",
            "customer_last_name",
            "customer_email",
            "customer_phone",
            "customer_city",
            "customer_signup_date",
        ],
    )

    dim_customers = (
        dim_customers
        .sort_values("customer_id")
        .reset_index(drop=True)
    )

    dim_customers[
        "customer_full_name"
    ] = (
        dim_customers[
            [
                "customer_first_name",
                "customer_last_name",
            ]
        ]
        .fillna("")
        .astype(str)
        .apply(
            lambda row: " ".join(
                value.strip()
                for value in row
                if value.strip()
            ),
            axis=1,
        )
    )

    dim_customers = dim_customers[
        [
            "customer_id",
            "customer_first_name",
            "customer_last_name",
            "customer_full_name",
            "customer_email",
            "customer_phone",
            "customer_city",
            "customer_signup_date",
        ]
    ]

    # ========================================================
    # DIMENSION: BRANCHES
    # ========================================================

    dim_branches = build_dimension(
        valid,
        "branch_id",
        [
            "branch_name",
            "branch_city",
            "sales_channel",
        ],
    )

    dim_branches = (
        dim_branches
        .sort_values("branch_id")
        .reset_index(drop=True)
    )

    # ========================================================
    # FACT: SALES
    # ========================================================

    fact_sales = valid[
        [
            "sale_id",
            "sale_date",
            "customer_id",
            "product_id",
            "branch_id",
            "payment_method",
            "quantity",
            "unit_price",
            "discount_percent",
            "gross_revenue",
            "discount_amount",
            "net_revenue",
            "total_cost",
            "gross_profit",
            "margin_percent",
        ]
    ].copy()

    fact_sales.insert(
        0,
        "sale_key",
        range(
            1,
            len(fact_sales) + 1,
        ),
    )

    fact_sales = fact_sales.rename(
        columns={
            "margin_percent": "margin_percentage",
        }
    )

    # ========================================================
    # FACT: INVENTORY SNAPSHOT
    # ========================================================

    inventory = df[
        [
            "sale_id",
            "product_id",
            "branch_id",
            "inventory_snapshot_date",
            "stock_quantity",
            "reorder_level",
        ]
    ].copy()

    inventory_rejection_reason = pd.Series(
        "",
        index=inventory.index,
        dtype="string",
    )

    def reject_inventory(
        mask,
        reason,
    ):

        mask = mask.fillna(False)

        target = (
            mask
            & (
                inventory_rejection_reason
                == ""
            )
        )

        inventory_rejection_reason.loc[
            target
        ] = reason

    reject_inventory(
        inventory["product_id"].isna(),
        "inventory_missing_product_id",
    )

    reject_inventory(
        inventory["branch_id"].isna(),
        "inventory_missing_branch_id",
    )

    reject_inventory(
        inventory[
            "inventory_snapshot_date"
        ].isna(),
        "invalid_inventory_snapshot_date",
    )

    reject_inventory(
        inventory[
            "stock_quantity"
        ].isna(),
        "missing_stock_quantity",
    )

    reject_inventory(
        inventory[
            "stock_quantity"
        ].notna()
        & (
            inventory[
                "stock_quantity"
            ] < 0
        ),
        "negative_stock_quantity",
    )

    reject_inventory(
        inventory[
            "reorder_level"
        ].isna(),
        "missing_reorder_level",
    )

    reject_inventory(
        inventory[
            "reorder_level"
        ].notna()
        & (
            inventory[
                "reorder_level"
            ] < 0
        ),
        "negative_reorder_level",
    )

    inventory_rejected_mask = (
        inventory_rejection_reason
        != ""
    )

    rejected_inventory = inventory.loc[
        inventory_rejected_mask
    ].copy()

    rejected_inventory[
        "rejection_reason"
    ] = inventory_rejection_reason.loc[
        inventory_rejected_mask
    ]

    inventory_valid = inventory.loc[
        ~inventory_rejected_mask
    ].copy()

    inventory_valid[
        "stockout_risk"
    ] = (
        inventory_valid[
            "stock_quantity"
        ]
        <= inventory_valid[
            "reorder_level"
        ]
    )

    fact_inventory_snapshot = (
        inventory_valid[
            [
                "inventory_snapshot_date",
                "product_id",
                "branch_id",
                "stock_quantity",
                "reorder_level",
                "stockout_risk",
            ]
        ]
        .drop_duplicates(
            subset=[
                "inventory_snapshot_date",
                "product_id",
                "branch_id",
            ],
            keep="first",
        )
        .sort_values(
            [
                "inventory_snapshot_date",
                "product_id",
                "branch_id",
            ]
        )
        .reset_index(drop=True)
    )

    # ========================================================
    # Combine rejected records
    # ========================================================

    rejected_sales[
        "record_type"
    ] = "sale"

    rejected_inventory[
        "record_type"
    ] = "inventory"

    rejected_sales[
        "rejection_source"
    ] = "sales_validation"

    rejected_inventory[
        "rejection_source"
    ] = "inventory_validation"

    rejected = pd.concat(
        [
            rejected_sales,
            rejected_inventory,
        ],
        ignore_index=True,
        sort=False,
    )

    # ========================================================
    # Convert missing values
    # ========================================================

    dim_categories = convert_missing_values(
        dim_categories
    )

    dim_products = convert_missing_values(
        dim_products
    )

    dim_customers = convert_missing_values(
        dim_customers
    )

    dim_branches = convert_missing_values(
        dim_branches
    )

    fact_sales = convert_missing_values(
        fact_sales
    )

    fact_inventory_snapshot = (
        convert_missing_values(
            fact_inventory_snapshot
        )
    )

    rejected = convert_missing_values(
        rejected
    )

    # ========================================================
    # Save normalized outputs
    # ========================================================

    save_processed_outputs(
        dim_categories=dim_categories,
        dim_products=dim_products,
        dim_customers=dim_customers,
        dim_branches=dim_branches,
        fact_sales=fact_sales,
        fact_inventory_snapshot=(
            fact_inventory_snapshot
        ),
    )

    # ========================================================
    # Save rejected records
    # ========================================================

    rejected_path = (
        REJECTED_DIR
        / "rejected_records.csv"
    )

    rejected.to_csv(
        rejected_path,
        index=False,
    )

    # ========================================================
    # Transformation summary
    # ========================================================

    print()
    print("## Transformation completed")
    print()

    print(
        f"Input rows: "
        f"{input_rows:,}"
    )

    print(
        f"Exact duplicates removed: "
        f"{duplicate_count:,}"
    )

    print(
        f"Valid sales rows: "
        f"{len(valid):,}"
    )

    print(
        f"Rejected sale rows: "
        f"{len(rejected_sales):,}"
    )

    print(
        f"Rejected inventory rows: "
        f"{len(rejected_inventory):,}"
    )

    print(
        f"Total rejected records: "
        f"{len(rejected):,}"
    )

    print(
        f"Categories: "
        f"{len(dim_categories):,}"
    )

    print(
        f"Products: "
        f"{len(dim_products):,}"
    )

    print(
        f"Customers: "
        f"{len(dim_customers):,}"
    )

    print(
        f"Branches: "
        f"{len(dim_branches):,}"
    )

    print(
        f"Fact sales: "
        f"{len(fact_sales):,}"
    )

    print(
        f"Inventory snapshots: "
        f"{len(fact_inventory_snapshot):,}"
    )

    print(
        f"Rejected records saved: "
        f"{rejected_path}"
    )

    # ========================================================
    # Return normalized tables
    # ========================================================

    return {
        "dim_categories": dim_categories,
        "dim_products": dim_products,
        "dim_customers": dim_customers,
        "dim_branches": dim_branches,
        "fact_sales": fact_sales,
        "fact_inventory_snapshot": (
            fact_inventory_snapshot
        ),
        "rejected": rejected,
    }