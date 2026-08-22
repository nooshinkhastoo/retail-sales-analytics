from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2 import extras


# ============================================================
# Project paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SCHEMA_PATH = (
    BASE_DIR
    / "sql"
    / "01_create_schema.sql"
)

VIEWS_PATH = (
    BASE_DIR
    / "sql"
    / "02_create_analytics_views.sql"
)


# ============================================================
# PostgreSQL connection
# ============================================================

def get_connection(config):
    """
    Create and return a PostgreSQL connection.

    Expected config format:

        {
            "dsn": DATABASE_URL
        }
    """

    dsn = config["dsn"]

    conn = psycopg2.connect(dsn)

    print("PostgreSQL connection established")

    return conn


# ============================================================
# Execute SQL file
# ============================================================

def execute_sql_file(conn, sql_path):
    """
    Execute a PostgreSQL SQL file.
    """

    if not sql_path.exists():
        raise FileNotFoundError(
            f"SQL file not found: {sql_path}"
        )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    cursor = conn.cursor()

    try:
        cursor.execute(sql)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()


# ============================================================
# Create schema
# ============================================================

def create_schema(conn):
    """
    Execute the PostgreSQL schema script.

    Schema definition:

        sql/01_create_schema.sql
    """

    print()
    print("## Starting PostgreSQL schema creation...")
    print()

    execute_sql_file(
        conn,
        SCHEMA_PATH,
    )

    print(
        "PostgreSQL schema created successfully."
    )


# ============================================================
# Create analytical views
# ============================================================

def create_analytics_views(conn):
    """
    Create all analytical views.

    View definitions:

        sql/02_create_analytics_views.sql

    Views are created after all tables have been loaded,
    because the views depend on the tables and their data.
    """

    print()
    print("## Creating analytical views...")
    print()

    execute_sql_file(
        conn,
        VIEWS_PATH,
    )

    print(
        "Analytical views created successfully."
    )


# ============================================================
# Drop existing tables
# ============================================================

def drop_existing_tables(conn):
    """
    Remove existing analytical tables before loading.

    CASCADE also removes dependent views.
    """

    print()
    print("Dropping existing tables...")

    drop_queries = [
        """
        DROP TABLE IF EXISTS
            fact_inventory_snapshot
        CASCADE;
        """,

        """
        DROP TABLE IF EXISTS
            fact_sales
        CASCADE;
        """,

        """
        DROP TABLE IF EXISTS
            dim_products
        CASCADE;
        """,

        """
        DROP TABLE IF EXISTS
            dim_customers
        CASCADE;
        """,

        """
        DROP TABLE IF EXISTS
            dim_branches
        CASCADE;
        """,

        """
        DROP TABLE IF EXISTS
            dim_categories
        CASCADE;
        """,
    ]

    cursor = conn.cursor()

    try:
        for query in drop_queries:
            cursor.execute(query)

        conn.commit()

        print(
            "Existing tables dropped successfully."
        )

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()


# ============================================================
# Prepare DataFrame values for PostgreSQL
# ============================================================

def prepare_dataframe(dataframe, columns):
    """
    Prepare selected DataFrame columns for PostgreSQL insertion.

    pandas can use pd.NA, NaN, and NaT for missing values.

    They are converted to Python None so that psycopg2
    sends them as SQL NULL.
    """

    selected = dataframe[columns].copy()

    selected = selected.astype(object).where(
        pd.notna(selected),
        None,
    )

    return selected


# ============================================================
# Insert DataFrame
# ============================================================

def insert_dataframe(
    cursor,
    table_name,
    dataframe,
    columns,
):
    """
    Insert a pandas DataFrame into PostgreSQL.

    Uses psycopg2.extras.execute_values for efficient
    bulk insertion.
    """

    if dataframe.empty:
        print(
            f"{table_name}: 0 rows inserted "
            "(DataFrame is empty)"
        )

        return 0

    # --------------------------------------------------------
    # Validate DataFrame columns
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise KeyError(
            f"{table_name}: missing DataFrame columns: "
            f"{missing_columns}"
        )

    # --------------------------------------------------------
    # Prepare values
    # --------------------------------------------------------

    prepared = prepare_dataframe(
        dataframe,
        columns,
    )

    data = [
        tuple(row)
        for row in prepared.itertuples(
            index=False,
            name=None,
        )
    ]

    # --------------------------------------------------------
    # Build INSERT query
    # --------------------------------------------------------

    column_names = ", ".join(columns)

    query = f"""
        INSERT INTO {table_name} ({column_names})
        VALUES %s
    """

    # --------------------------------------------------------
    # Bulk insert
    # --------------------------------------------------------

    extras.execute_values(
        cursor,
        query,
        data,
        page_size=10_000,
    )

    return len(data)


# ============================================================
# Load data
# ============================================================

def load_data(conn, tables):
    """
    Load normalized DataFrames into PostgreSQL.

    Loading order:

        1. Drop existing tables
        2. Create schema
        3. Load dimensions
        4. Load fact tables
        5. Create analytical views
        6. Commit transaction
    """

    print()
    print("## Starting PostgreSQL load...")
    print()

    cursor = conn.cursor()

    try:

        # ====================================================
        # 1. Drop existing tables
        # ====================================================

        drop_existing_tables(conn)

        # ====================================================
        # 2. Create schema
        # ====================================================

        print()
        print("Creating tables...")

        create_schema(conn)

        # ====================================================
        # 3. Load dimensions
        # ====================================================

        print()
        print("Loading dimensions...")

        # ----------------------------------------------------
        # dim_categories
        # ----------------------------------------------------

        inserted = insert_dataframe(
            cursor,
            "dim_categories",
            tables["dim_categories"],
            [
                "category_id",
                "category_name",
                "category_display_name",
            ],
        )

        print(
            f"dim_categories: "
            f"{inserted:,} rows inserted"
        )

        # ----------------------------------------------------
        # dim_products
        # ----------------------------------------------------

        inserted = insert_dataframe(
            cursor,
            "dim_products",
            tables["dim_products"],
            [
                "product_id",
                "product_name",
                "category_id",
                "category_name",
                "unit_cost",
                "unit_price",
            ],
        )

        print(
            f"dim_products: "
            f"{inserted:,} rows inserted"
        )

        # ----------------------------------------------------
        # dim_customers
        # ----------------------------------------------------

        inserted = insert_dataframe(
            cursor,
            "dim_customers",
            tables["dim_customers"],
            [
                "customer_id",
                "customer_first_name",
                "customer_last_name",
                "customer_full_name",
                "customer_email",
                "customer_phone",
                "customer_city",
                "customer_signup_date",
            ],
        )

        print(
            f"dim_customers: "
            f"{inserted:,} rows inserted"
        )

        # ----------------------------------------------------
        # dim_branches
        # ----------------------------------------------------

        inserted = insert_dataframe(
            cursor,
            "dim_branches",
            tables["dim_branches"],
            [
                "branch_id",
                "branch_name",
                "branch_city",
                "sales_channel",
            ],
        )

        print(
            f"dim_branches: "
            f"{inserted:,} rows inserted"
        )

        # ====================================================
        # 4. Load fact tables
        # ====================================================

        print()
        print("Loading facts...")

        # ----------------------------------------------------
        # fact_sales
        # ----------------------------------------------------

        inserted = insert_dataframe(
            cursor,
            "fact_sales",
            tables["fact_sales"],
            [
                "sale_key",
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
                "margin_percentage",
            ],
        )

        print(
            f"fact_sales: "
            f"{inserted:,} rows inserted"
        )

        # ----------------------------------------------------
        # fact_inventory_snapshot
        # ----------------------------------------------------

        inserted = insert_dataframe(
            cursor,
            "fact_inventory_snapshot",
            tables["fact_inventory_snapshot"],
            [
                "inventory_snapshot_date",
                "product_id",
                "branch_id",
                "stock_quantity",
                "reorder_level",
                "stockout_risk",
            ],
        )

        print(
            f"fact_inventory_snapshot: "
            f"{inserted:,} rows inserted"
        )

        # ====================================================
        # 5. Create analytical views
        # ====================================================

        create_analytics_views(conn)

        # ====================================================
        # 6. Commit transaction
        # ====================================================

        conn.commit()

        print()
        print("All data loaded successfully.")

    except Exception:
        conn.rollback()

        print()
        print("PostgreSQL load failed.")

        raise

    finally:
        cursor.close()