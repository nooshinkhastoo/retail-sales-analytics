from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# Project paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

REPORTS_DIR = BASE_DIR / "reports"
CHARTS_DIR = REPORTS_DIR / "charts"

ANALYSIS_QUERIES_PATH = (
    BASE_DIR
    / "sql"
    / "03_analysis_queries.sql"
)

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

CHARTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Analysis query sections
# ============================================================

ANALYSIS_SECTIONS = {
    "daily_sales_trend": "1. Daily Revenue Trend",
    "top_10_products": "2. Top 10 Products by Revenue",
    "top_10_branches": "3. Top 10 Branches by Revenue",
    "category_profitability": "4. Category-Level Profitability",
    "top_10_customers": "5. Top 10 Customers by Lifetime Value",
    "stockout_risk_products": (
        "6. Products Below Reorder Level / Stockout Risk"
    ),
}


# ============================================================
# Helper: load analysis queries
# ============================================================

def _load_analysis_queries():
    """
    Read sql/03_analysis_queries.sql and extract the six
    analytical SELECT statements.

    The SQL file is the single source of truth for
    analytical queries.
    """

    if not ANALYSIS_QUERIES_PATH.exists():
        raise FileNotFoundError(
            f"Analysis query file not found: "
            f"{ANALYSIS_QUERIES_PATH}"
        )

    sql_text = ANALYSIS_QUERIES_PATH.read_text(
        encoding="utf-8"
    )

    queries = {}

    current_query = None
    current_lines = []

    for line in sql_text.splitlines():
        stripped = line.strip()

        if stripped.startswith("--"):
            comment = stripped[2:].strip()

            for query_name, section_title in (
                ANALYSIS_SECTIONS.items()
            ):
                if comment == section_title:

                    if current_query is not None:
                        query = "\n".join(
                            current_lines
                        ).strip()

                        if query:
                            queries[current_query] = query

                    current_query = query_name
                    current_lines = []

                    break

            continue

        if current_query is not None:
            current_lines.append(line)

    if current_query is not None:
        query = "\n".join(
            current_lines
        ).strip()

        if query:
            queries[current_query] = query

    missing = [
        name
        for name in ANALYSIS_SECTIONS
        if name not in queries
        or not queries[name]
    ]

    if missing:
        raise ValueError(
            "Missing analysis queries in "
            f"{ANALYSIS_QUERIES_PATH}: "
            f"{', '.join(missing)}"
        )

    return queries


# ============================================================
# Helper: execute query and return DataFrame
# ============================================================

def _query_to_dataframe(conn, query):
    """
    Execute a PostgreSQL query and return the result
    as a Pandas DataFrame.
    """

    cursor = conn.cursor()

    try:
        cursor.execute(query)

        if cursor.description is None:
            return pd.DataFrame()

        columns = [
            description[0]
            for description in cursor.description
        ]

        rows = cursor.fetchall()

        return pd.DataFrame(
            rows,
            columns=columns,
        )

    finally:
        cursor.close()


# ============================================================
# Run analytical reports
# ============================================================

def run_reports(conn):
    """
    Execute analytical queries from:

        sql/03_analysis_queries.sql

    Results are:

        1. Returned as DataFrames
        2. Saved as CSV files under reports/

    No analytical SQL is duplicated here.
    """

    print()
    print("## Running analytical reports...")

    queries = _load_analysis_queries()

    results = {}

    for report_name, query in queries.items():

        dataframe = _query_to_dataframe(
            conn,
            query,
        )

        results[report_name] = dataframe

        output_path = (
            REPORTS_DIR
            / f"{report_name}.csv"
        )

        dataframe.to_csv(
            output_path,
            index=False,
        )

        print(
            f"{report_name}: "
            f"{len(dataframe):,} rows"
        )

        print(
            f"Saved: {output_path}"
        )

    return results


# ============================================================
# KPI queries
# ============================================================

def get_kpis(conn):
    """
    Calculate high-level business KPIs.

    These are summary metrics required by the project.
    """

    queries = {
        "total_sales": """
            SELECT COUNT(*)
            FROM fact_sales;
        """,

        "total_quantity_sold": """
            SELECT COALESCE(SUM(quantity), 0)
            FROM fact_sales;
        """,

        "total_gross_revenue": """
            SELECT COALESCE(SUM(gross_revenue), 0)
            FROM fact_sales;
        """,

        "total_net_revenue": """
            SELECT COALESCE(SUM(net_revenue), 0)
            FROM fact_sales;
        """,

        "total_gross_profit": """
            SELECT COALESCE(SUM(gross_profit), 0)
            FROM fact_sales;
        """,

        "average_margin": """
            SELECT
                CASE
                    WHEN COALESCE(SUM(net_revenue), 0) = 0
                    THEN 0
                    ELSE
                        COALESCE(SUM(gross_profit), 0)
                        / SUM(net_revenue) * 100
                END
            FROM fact_sales;
        """,

        "average_order_value": """
            SELECT
                CASE
                    WHEN COUNT(*) = 0
                    THEN 0
                    ELSE AVG(net_revenue)
                END
            FROM fact_sales;
        """,

        "total_customers": """
            SELECT COUNT(*)
            FROM dim_customers;
        """,

        "total_products": """
            SELECT COUNT(*)
            FROM dim_products;
        """,

        "total_categories": """
            SELECT COUNT(*)
            FROM dim_categories;
        """,

        "total_branches": """
            SELECT COUNT(*)
            FROM dim_branches;
        """,

        "total_inventory_snapshots": """
            SELECT COUNT(*)
            FROM fact_inventory_snapshot;
        """,

        "stockout_risk_count": """
            SELECT COUNT(*)
            FROM vw_stockout_risk
            WHERE is_at_risk = TRUE;
        """,
    }

    cursor = conn.cursor()
    kpis = {}

    try:
        for name, query in queries.items():

            cursor.execute(query)

            result = cursor.fetchone()[0]

            kpis[name] = result

        return kpis

    finally:
        cursor.close()


# ============================================================
# Chart 1: Daily revenue
# ============================================================

def create_daily_revenue_chart(daily_sales):
    """
    Create a daily revenue line chart.
    """

    if daily_sales.empty:
        return None

    dataframe = daily_sales.copy()

    dataframe["sale_date"] = pd.to_datetime(
        dataframe["sale_date"]
    )

    if "total_revenue" in dataframe.columns:
        revenue_column = "total_revenue"

    elif "net_revenue" in dataframe.columns:
        revenue_column = "net_revenue"

    elif "daily_revenue" in dataframe.columns:
        revenue_column = "daily_revenue"

    else:
        raise ValueError(
            "Daily sales query must contain "
            "'total_revenue', 'net_revenue', "
            "or 'daily_revenue'."
        )

    dataframe[revenue_column] = pd.to_numeric(
        dataframe[revenue_column],
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=[revenue_column]
    )

    if dataframe.empty:
        return None

    plt.figure(figsize=(12, 6))

    plt.plot(
        dataframe["sale_date"],
        dataframe[revenue_column],
    )

    plt.title("Daily Revenue Trend")
    plt.xlabel("Date")
    plt.ylabel("Revenue")

    plt.xticks(rotation=45)

    plt.tight_layout()

    output_path = (
        CHARTS_DIR
        / "daily_revenue.png"
    )

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Saved chart: {output_path}"
    )

    return output_path


# ============================================================
# Chart 2: Top 10 products
# ============================================================

def create_top_products_chart(top_products):
    """
    Create a bar chart for the top 10 products.
    """

    if top_products.empty:
        return None

    dataframe = top_products.copy()

    if "total_revenue" in dataframe.columns:
        revenue_column = "total_revenue"

    elif "net_revenue" in dataframe.columns:
        revenue_column = "net_revenue"

    else:
        raise ValueError(
            "Top products query must contain "
            "'total_revenue' or 'net_revenue'."
        )

    dataframe[revenue_column] = pd.to_numeric(
        dataframe[revenue_column],
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=[revenue_column]
    )

    if dataframe.empty:
        return None

    dataframe = dataframe.sort_values(
        revenue_column,
        ascending=True,
    )

    plt.figure(figsize=(10, 6))

    plt.barh(
        dataframe["product_name"],
        dataframe[revenue_column],
    )

    plt.title(
        "Top 10 Products by Revenue"
    )

    plt.xlabel("Revenue")
    plt.ylabel("Product")

    plt.tight_layout()

    output_path = (
        CHARTS_DIR
        / "top_10_products.png"
    )

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Saved chart: {output_path}"
    )

    return output_path


# ============================================================
# Chart 3: Revenue by branch
# ============================================================

def create_branch_revenue_chart(branch_revenue):
    """
    Create a bar chart for the top branches by revenue.
    """

    if branch_revenue.empty:
        return None

    dataframe = branch_revenue.copy()

    if "total_revenue" in dataframe.columns:
        revenue_column = "total_revenue"

    elif "net_revenue" in dataframe.columns:
        revenue_column = "net_revenue"

    else:
        raise ValueError(
            "Branch query must contain "
            "'total_revenue' or 'net_revenue'."
        )

    dataframe[revenue_column] = pd.to_numeric(
        dataframe[revenue_column],
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=[revenue_column]
    )

    if dataframe.empty:
        return None

    dataframe = dataframe.sort_values(
        revenue_column,
        ascending=True,
    )

    plt.figure(figsize=(12, 8))

    plt.barh(
        dataframe["branch_name"],
        dataframe[revenue_column],
    )

    plt.title(
        "Top Branches by Revenue"
    )

    plt.xlabel("Revenue")
    plt.ylabel("Branch")

    plt.tight_layout()

    output_path = (
        CHARTS_DIR
        / "revenue_by_branch.png"
    )

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Saved chart: {output_path}"
    )

    return output_path


# ============================================================
# Chart 4: Category gross margin
# ============================================================

def create_category_margin_chart(category_margin):
    """
    Create a bar chart for category gross margin.
    """

    if category_margin.empty:
        return None

    dataframe = category_margin.copy()

    if "gross_margin_percentage" in dataframe.columns:
        margin_column = "gross_margin_percentage"

    elif "gross_margin_percent" in dataframe.columns:
        margin_column = "gross_margin_percent"

    else:
        raise ValueError(
            "Category query must contain "
            "'gross_margin_percentage' "
            "or 'gross_margin_percent'."
        )

    dataframe[margin_column] = pd.to_numeric(
        dataframe[margin_column],
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=[margin_column]
    )

    if dataframe.empty:
        return None

    dataframe = dataframe.sort_values(
        margin_column,
        ascending=True,
    )

    plt.figure(figsize=(10, 8))

    plt.barh(
        dataframe["category_name"],
        dataframe[margin_column],
    )

    plt.title(
        "Gross Margin by Category"
    )

    plt.xlabel("Gross Margin (%)")
    plt.ylabel("Category")

    plt.tight_layout()

    output_path = (
        CHARTS_DIR
        / "category_gross_margin.png"
    )

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Saved chart: {output_path}"
    )

    return output_path


# ============================================================
# Chart 5: Stockout risk
# ============================================================

def create_stockout_risk_chart(stockout_products):
    """
    Create a stockout risk chart.

    Supports three possible result structures:

    1. Detailed product-level stockout data:
       stock_quantity + reorder_level

    2. Branch-level stockout risk:
       branch_name + stockout_risk_products

    3. Product-level risk data:
       product_name

    A generic fallback is used otherwise.
    """

    if stockout_products.empty:
        return None

    dataframe = stockout_products.copy()

    output_path = (
        CHARTS_DIR
        / "stockout_risk.png"
    )

    # --------------------------------------------------------
    # Case 1:
    # Detailed stockout data is available.
    # --------------------------------------------------------

    if (
        "stock_quantity" in dataframe.columns
        and "reorder_level" in dataframe.columns
    ):

        dataframe["stock_quantity"] = pd.to_numeric(
            dataframe["stock_quantity"],
            errors="coerce",
        )

        dataframe["reorder_level"] = pd.to_numeric(
            dataframe["reorder_level"],
            errors="coerce",
        )

        dataframe = dataframe.dropna(
            subset=[
                "stock_quantity",
                "reorder_level",
            ]
        )

        if dataframe.empty:
            return None

        dataframe = dataframe.head(10)

        dataframe = dataframe.sort_values(
            "reorder_level",
            ascending=True,
        )

        plt.figure(figsize=(10, 7))

        positions = range(
            len(dataframe)
        )

        plt.barh(
            positions,
            dataframe["reorder_level"],
            alpha=0.6,
            label="Reorder Level",
        )

        plt.barh(
            positions,
            dataframe["stock_quantity"],
            alpha=0.9,
            label="Current Stock",
        )

        product_labels = (
            dataframe["product_name"]
            if "product_name" in dataframe.columns
            else dataframe["product_id"]
        )

        plt.yticks(
            positions,
            product_labels,
        )

        plt.title(
            "Stockout Risk - "
            "Current Stock vs Reorder Level"
        )

        plt.xlabel("Quantity")
        plt.ylabel("Product")

        plt.legend()

        plt.tight_layout()

        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close()

        print(
            f"Saved chart: {output_path}"
        )

        return output_path

    # --------------------------------------------------------
    # Case 2:
    # Current SQL returns branch-level stockout risk.
    # --------------------------------------------------------

    if (
        "branch_name" in dataframe.columns
        and "stockout_risk_products"
        in dataframe.columns
    ):

        dataframe[
            "stockout_risk_products"
        ] = pd.to_numeric(
            dataframe[
                "stockout_risk_products"
            ],
            errors="coerce",
        )

        dataframe = dataframe.dropna(
            subset=[
                "stockout_risk_products"
            ]
        )

        if dataframe.empty:
            return None

        dataframe = dataframe.sort_values(
            "stockout_risk_products",
            ascending=True,
        )

        dataframe = dataframe.tail(10)

        plt.figure(figsize=(10, 7))

        plt.barh(
            dataframe["branch_name"],
            dataframe[
                "stockout_risk_products"
            ],
        )

        plt.title(
            "Top 10 Branches by Stockout Risk"
        )

        plt.xlabel(
            "Number of Stockout-Risk Products"
        )

        plt.ylabel("Branch")

        plt.tight_layout()

        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close()

        print(
            f"Saved chart: {output_path}"
        )

        return output_path

    # --------------------------------------------------------
    # Case 3:
    # Query returns product-level risk information.
    # --------------------------------------------------------

    if "product_name" in dataframe.columns:

        risk_counts = (
            dataframe
            .groupby("product_name")
            .size()
            .sort_values(ascending=True)
            .tail(10)
        )

        plt.figure(figsize=(10, 7))

        plt.barh(
            risk_counts.index,
            risk_counts.values,
        )

        plt.title(
            "Stockout Risk by Product"
        )

        plt.xlabel(
            "Number of At-Risk Records"
        )

        plt.ylabel("Product")

        plt.tight_layout()

        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close()

        print(
            f"Saved chart: {output_path}"
        )

        return output_path

    # --------------------------------------------------------
    # Case 4:
    # Generic fallback.
    # --------------------------------------------------------

    plt.figure(figsize=(10, 6))

    plt.bar(
        ["At-Risk Records"],
        [len(dataframe)],
    )

    plt.title(
        "Stockout Risk"
    )

    plt.ylabel(
        "Number of At-Risk Records"
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Saved chart: {output_path}"
    )

    return output_path


# ============================================================
# Generate all charts
# ============================================================

def create_charts(results):
    """
    Generate all required Matplotlib charts.
    """

    print()
    print("## Creating analytical charts...")

    chart_paths = {}

    chart_paths["daily_revenue"] = (
        create_daily_revenue_chart(
            results["daily_sales_trend"]
        )
    )

    chart_paths["top_10_products"] = (
        create_top_products_chart(
            results["top_10_products"]
        )
    )

    chart_paths["revenue_by_branch"] = (
        create_branch_revenue_chart(
            results["top_10_branches"]
        )
    )

    chart_paths["category_gross_margin"] = (
        create_category_margin_chart(
            results["category_profitability"]
        )
    )

    chart_paths["stockout_risk"] = (
        create_stockout_risk_chart(
            results["stockout_risk_products"]
        )
    )

    return chart_paths


# ============================================================
# Helper: safe numeric conversion
# ============================================================

def _to_float(value):
    """
    Convert a database/Pandas value to float.
    """

    if value is None:
        return 0.0

    try:
        return float(value)

    except (TypeError, ValueError):
        return 0.0


def _to_int(value):
    """
    Convert a database/Pandas value to int.
    """

    if value is None:
        return 0

    try:
        return int(value)

    except (TypeError, ValueError):
        return 0


# ============================================================
# Create summary report
# ============================================================

def create_summary_report(
    conn,
    results=None,
    chart_paths=None,
):
    """
    Create the final business summary report.
    """

    if results is None:
        results = run_reports(conn)

    if chart_paths is None:
        chart_paths = create_charts(results)

    kpis = get_kpis(conn)

    # --------------------------------------------------------
    # DataFrames
    # --------------------------------------------------------

    category_sales = results[
        "category_profitability"
    ]

    top_customers = results[
        "top_10_customers"
    ]

    stockout_products = results[
        "stockout_risk_products"
    ]

    daily_sales = results[
        "daily_sales_trend"
    ]

    top_products = results[
        "top_10_products"
    ]

    branch_revenue = results[
        "top_10_branches"
    ]

    # --------------------------------------------------------
    # Category
    # --------------------------------------------------------

    top_category_name = "N/A"
    top_category_revenue = 0.0

    best_margin_category_name = "N/A"
    best_margin = 0.0

    if not category_sales.empty:

        category_sales = category_sales.copy()

        revenue_column = (
            "net_revenue"
            if "net_revenue"
            in category_sales.columns
            else "total_revenue"
        )

        category_sales[
            revenue_column
        ] = pd.to_numeric(
            category_sales[
                revenue_column
            ],
            errors="coerce",
        )

        category_sales = (
            category_sales.dropna(
                subset=[revenue_column]
            )
        )

        if not category_sales.empty:

            top_category = (
                category_sales
                .sort_values(
                    revenue_column,
                    ascending=False,
                )
                .iloc[0]
            )

            top_category_name = str(
                top_category[
                    "category_name"
                ]
            )

            top_category_revenue = (
                _to_float(
                    top_category[
                        revenue_column
                    ]
                )
            )

        if (
            "gross_margin_percentage"
            in category_sales.columns
        ):

            category_sales[
                "gross_margin_percentage"
            ] = pd.to_numeric(
                category_sales[
                    "gross_margin_percentage"
                ],
                errors="coerce",
            )

            margin_data = (
                category_sales.dropna(
                    subset=[
                        "gross_margin_percentage"
                    ]
                )
            )

            if not margin_data.empty:

                best_margin_category = (
                    margin_data
                    .sort_values(
                        "gross_margin_percentage",
                        ascending=False,
                    )
                    .iloc[0]
                )

                best_margin_category_name = (
                    str(
                        best_margin_category[
                            "category_name"
                        ]
                    )
                )

                best_margin = _to_float(
                    best_margin_category[
                        "gross_margin_percentage"
                    ]
                )

    # --------------------------------------------------------
    # Customer
    # --------------------------------------------------------

    top_customer_name = "N/A"
    top_customer_spent = 0.0
    top_customer_orders = 0

    if not top_customers.empty:

        top_customer = (
            top_customers.iloc[0]
        )

        if (
            "customer_full_name"
            in top_customers.columns
        ):

            top_customer_name = str(
                top_customer[
                    "customer_full_name"
                ]
            )

        if (
            "net_revenue"
            in top_customers.columns
        ):

            top_customer_spent = (
                _to_float(
                    top_customer[
                        "net_revenue"
                    ]
                )
            )

        elif (
            "total_revenue"
            in top_customers.columns
        ):

            top_customer_spent = (
                _to_float(
                    top_customer[
                        "total_revenue"
                    ]
                )
            )

        if (
            "total_orders"
            in top_customers.columns
        ):

            top_customer_orders = (
                _to_int(
                    top_customer[
                        "total_orders"
                    ]
                )
            )

    # --------------------------------------------------------
    # Product
    # --------------------------------------------------------

    top_product_name = "N/A"
    top_product_revenue = 0.0

    if not top_products.empty:

        top_product = (
            top_products.iloc[0]
        )

        top_product_name = str(
            top_product[
                "product_name"
            ]
        )

        if (
            "total_revenue"
            in top_products.columns
        ):

            top_product_revenue = (
                _to_float(
                    top_product[
                        "total_revenue"
                    ]
                )
            )

        elif (
            "net_revenue"
            in top_products.columns
        ):

            top_product_revenue = (
                _to_float(
                    top_product[
                        "net_revenue"
                    ]
                )
            )

    # --------------------------------------------------------
    # Branch
    # --------------------------------------------------------

    top_branch_name = "N/A"
    top_branch_revenue = 0.0

    if not branch_revenue.empty:

        top_branch = (
            branch_revenue.iloc[0]
        )

        top_branch_name = str(
            top_branch[
                "branch_name"
            ]
        )

        if (
            "total_revenue"
            in branch_revenue.columns
        ):

            top_branch_revenue = (
                _to_float(
                    top_branch[
                        "total_revenue"
                    ]
                )
            )

        elif (
            "net_revenue"
            in branch_revenue.columns
        ):

            top_branch_revenue = (
                _to_float(
                    top_branch[
                        "net_revenue"
                    ]
                )
            )

    # --------------------------------------------------------
    # Daily sales
    # --------------------------------------------------------

    best_day_date = "N/A"
    best_day_revenue = 0.0

    lowest_day_date = "N/A"
    lowest_day_revenue = 0.0

    if not daily_sales.empty:

        daily_sales = daily_sales.copy()

        if (
            "total_revenue"
            in daily_sales.columns
        ):

            daily_revenue_column = (
                "total_revenue"
            )

        elif (
            "net_revenue"
            in daily_sales.columns
        ):

            daily_revenue_column = (
                "net_revenue"
            )

        elif (
            "daily_revenue"
            in daily_sales.columns
        ):

            daily_revenue_column = (
                "daily_revenue"
            )

        else:

            daily_revenue_column = None

        if daily_revenue_column is not None:

            daily_sales[
                daily_revenue_column
            ] = pd.to_numeric(
                daily_sales[
                    daily_revenue_column
                ],
                errors="coerce",
            )

            daily_sales = (
                daily_sales.dropna(
                    subset=[
                        daily_revenue_column
                    ]
                )
            )

            if not daily_sales.empty:

                best_day = (
                    daily_sales.loc[
                        daily_sales[
                            daily_revenue_column
                        ].idxmax()
                    ]
                )

                lowest_day = (
                    daily_sales.loc[
                        daily_sales[
                            daily_revenue_column
                        ].idxmin()
                    ]
                )

                best_day_date = str(
                    best_day[
                        "sale_date"
                    ]
                )

                best_day_revenue = (
                    _to_float(
                        best_day[
                            daily_revenue_column
                        ]
                    )
                )

                lowest_day_date = str(
                    lowest_day[
                        "sale_date"
                    ]
                )

                lowest_day_revenue = (
                    _to_float(
                        lowest_day[
                            daily_revenue_column
                        ]
                    )
                )

    # --------------------------------------------------------
    # Stockout
    # --------------------------------------------------------

    stockout_count = _to_int(
        kpis[
            "stockout_risk_count"
        ]
    )

    # --------------------------------------------------------
    # Branch-level stockout summary
    # --------------------------------------------------------

    top_stockout_branch_name = "N/A"
    top_stockout_branch_count = 0

    if not stockout_products.empty:

        if (
            "branch_name"
            in stockout_products.columns
            and
            "stockout_risk_products"
            in stockout_products.columns
        ):

            stockout_products = (
                stockout_products.copy()
            )

            stockout_products[
                "stockout_risk_products"
            ] = pd.to_numeric(
                stockout_products[
                    "stockout_risk_products"
                ],
                errors="coerce",
            )

            stockout_products = (
                stockout_products.dropna(
                    subset=[
                        "stockout_risk_products"
                    ]
                )
            )

            if not stockout_products.empty:

                top_stockout_branch = (
                    stockout_products
                    .sort_values(
                        "stockout_risk_products",
                        ascending=False,
                    )
                    .iloc[0]
                )

                top_stockout_branch_name = str(
                    top_stockout_branch[
                        "branch_name"
                    ]
                )

                top_stockout_branch_count = (
                    _to_int(
                        top_stockout_branch[
                            "stockout_risk_products"
                        ]
                    )
                )

    # --------------------------------------------------------
    # Build Markdown
    # --------------------------------------------------------

    summary = f"""# Retail Analytics Report

## 1. Executive Summary

The Retail Analytics Pipeline transformed the retail transaction
dataset into a normalized analytical model, loaded the resulting
data into PostgreSQL, performed data-quality checks, and generated
analytical reports and visualizations.

The analytical database currently contains:

- **{_to_int(kpis["total_sales"]):,} sales transactions**
- **{_to_int(kpis["total_customers"]):,} customers**
- **{_to_int(kpis["total_products"]):,} products**
- **{_to_int(kpis["total_categories"]):,} categories**
- **{_to_int(kpis["total_branches"]):,} branches**
- **{_to_int(kpis["total_inventory_snapshots"]):,} inventory snapshots**

---

## 2. Key Performance Indicators

| KPI | Value |
| --- | ---: |
| Total sales transactions | {_to_int(kpis["total_sales"]):,} |
| Total quantity sold | {_to_int(kpis["total_quantity_sold"]):,} |
| Gross revenue | ${_to_float(kpis["total_gross_revenue"]):,.2f} |
| Net revenue | ${_to_float(kpis["total_net_revenue"]):,.2f} |
| Gross profit | ${_to_float(kpis["total_gross_profit"]):,.2f} |
| Gross margin | {_to_float(kpis["average_margin"]):.2f}% |
| Average order value | ${_to_float(kpis["average_order_value"]):,.2f} |
| Customers | {_to_int(kpis["total_customers"]):,} |
| Products | {_to_int(kpis["total_products"]):,} |
| Categories | {_to_int(kpis["total_categories"]):,} |
| Branches | {_to_int(kpis["total_branches"]):,} |
| Inventory snapshots | {_to_int(kpis["total_inventory_snapshots"]):,} |

---

## 3. Sales by Category

The highest-revenue category is **{top_category_name}**,
generating **${top_category_revenue:,.2f}** in net revenue.

### Top Categories

| Category | Revenue | Gross Profit | Gross Margin |
| --- | ---: | ---: | ---: |
"""

    if not category_sales.empty:

        revenue_column = (
            "net_revenue"
            if "net_revenue" in category_sales.columns
            else "total_revenue"
        )

        for _, row in category_sales.iterrows():

            gross_profit = (
                _to_float(
                    row["gross_profit"]
                )
                if "gross_profit" in category_sales.columns
                else 0.0
            )

            margin = (
                _to_float(
                    row["gross_margin_percentage"]
                )
                if "gross_margin_percentage"
                in category_sales.columns
                else 0.0
            )

            summary += (
                f"| {row['category_name']} | "
                f"${_to_float(row[revenue_column]):,.2f} | "
                f"${gross_profit:,.2f} | "
                f"{margin:.2f}% |\n"
            )

    summary += f"""
---

## 4. Top Products

The highest-revenue product is **{top_product_name}**,
generating **${top_product_revenue:,.2f}** in revenue.

### Top 10 Products by Revenue

| Product | Quantity Sold | Revenue |
| --- | ---: | ---: |
"""

    if not top_products.empty:

        for _, row in top_products.iterrows():

            quantity = (
                _to_int(
                    row["total_quantity_sold"]
                )
                if "total_quantity_sold"
                in top_products.columns
                else 0
            )

            revenue = (
                _to_float(
                    row["total_revenue"]
                )
                if "total_revenue"
                in top_products.columns
                else _to_float(
                    row["net_revenue"]
                )
            )

            summary += (
                f"| {row['product_name']} | "
                f"{quantity:,} | "
                f"${revenue:,.2f} |\n"
            )

    summary += f"""
---

## 5. Revenue by Branch

The highest-revenue branch is **{top_branch_name}**,
generating **${top_branch_revenue:,.2f}** in revenue.

### Top Branches

| Branch | City | Channel | Revenue |
| --- | --- | --- | ---: |
"""

    if not branch_revenue.empty:

        for _, row in branch_revenue.iterrows():

            revenue = (
                _to_float(
                    row["total_revenue"]
                )
                if "total_revenue"
                in branch_revenue.columns
                else _to_float(
                    row["net_revenue"]
                )
            )

            city = (
                row["branch_city"]
                if "branch_city"
                in branch_revenue.columns
                else ""
            )

            channel = (
                row["sales_channel"]
                if "sales_channel"
                in branch_revenue.columns
                else ""
            )

            summary += (
                f"| {row['branch_name']} | "
                f"{city} | "
                f"{channel} | "
                f"${revenue:,.2f} |\n"
            )

    summary += f"""
---

## 6. Category Profitability

The category with the highest gross margin is
**{best_margin_category_name}**, with a gross margin of
**{best_margin:.2f}%**.

---

## 7. Top Customers

The highest-value customer is **{top_customer_name}**,
with total spending of **${top_customer_spent:,.2f}**
across **{top_customer_orders:,} transactions**.

### Top 10 Customers

| Customer | Orders | Total Spent |
| --- | ---: | ---: |
"""

    if not top_customers.empty:

        for _, row in top_customers.iterrows():

            spent = (
                _to_float(
                    row["net_revenue"]
                )
                if "net_revenue"
                in top_customers.columns
                else _to_float(
                    row["total_revenue"]
                )
            )

            orders = (
                _to_int(
                    row["total_orders"]
                )
                if "total_orders"
                in top_customers.columns
                else 0
            )

            summary += (
                f"| {row['customer_full_name']} | "
                f"{orders:,} | "
                f"${spent:,.2f} |\n"
            )

    summary += f"""
---

## 8. Inventory Risk

The inventory analysis identified
**{stockout_count:,} inventory records**
marked as having stockout risk.

The branch with the highest number of stockout-risk products is
**{top_stockout_branch_name}**, with
**{top_stockout_branch_count:,} stockout-risk products**.

Products at or below their reorder level should be reviewed
for replenishment.

### Stockout Risk by Branch

| Branch | Stockout-Risk Products |
| --- | ---: |
"""

    if not stockout_products.empty:

        if (
            "branch_name" in stockout_products.columns
            and
            "stockout_risk_products"
            in stockout_products.columns
        ):

            for _, row in stockout_products.iterrows():

                count = _to_int(
                    row[
                        "stockout_risk_products"
                    ]
                )

                summary += (
                    f"| {row['branch_name']} | "
                    f"{count:,} |\n"
                )

        elif "product_name" in stockout_products.columns:

            for _, row in (
                stockout_products
                .head(20)
                .iterrows()
            ):

                if (
                    "stock_quantity"
                    in stockout_products.columns
                    and
                    "reorder_level"
                    in stockout_products.columns
                ):

                    details = (
                        f"Stock: "
                        f"{_to_int(row['stock_quantity']):,}; "
                        f"Reorder level: "
                        f"{_to_int(row['reorder_level']):,}"
                    )

                else:

                    details = (
                        "At-risk inventory record"
                    )

                summary += (
                    f"| {row.get('product_name', 'N/A')} | "
                    f"{details} |\n"
                )

    summary += f"""
---

## 9. Daily Sales Trend

The daily sales report contains
**{len(daily_sales):,} days** of sales activity.

The highest-revenue day was **{best_day_date}**,
with revenue of **${best_day_revenue:,.2f}**.

The lowest-revenue day was **{lowest_day_date}**,
with revenue of **${lowest_day_revenue:,.2f}**.

---

## 10. Data Quality

The pipeline includes post-load validation checks covering:

- Row counts
- Primary key uniqueness
- Required key fields
- Foreign key relationships
- Numeric constraints
- Revenue calculations
- Discount calculations
- Cost calculations
- Gross profit calculations
- Inventory constraints
- Duplicate inventory snapshots

Validation results should be reviewed from the dedicated
data-quality validation output before reporting the pipeline
as fully validated.

---

## 11. Generated Analytical Reports

The following CSV reports are generated:

- `daily_sales_trend.csv`
- `top_10_products.csv`
- `top_10_branches.csv`
- `category_profitability.csv`
- `top_10_customers.csv`
- `stockout_risk_products.csv`

---

## 12. Generated Visualizations

The pipeline generates the following Matplotlib charts:

- `charts/daily_revenue.png`
- `charts/top_10_products.png`
- `charts/revenue_by_branch.png`
- `charts/category_gross_margin.png`
- `charts/stockout_risk.png`

---

## 13. Conclusion

The Retail Analytics Pipeline transforms the raw retail transaction
export into a structured PostgreSQL analytical database.

The resulting analytical outputs provide visibility into:

- Sales performance
- Product performance
- Branch performance
- Category profitability
- Customer lifetime value
- Inventory stockout risk
- Daily revenue trends

The project therefore provides the required ETL, data-quality,
SQL analytics, reporting, and visualization components.
"""

    output_path = (
        REPORTS_DIR
        / "summary_report.md"
    )

    output_path.write_text(
        summary,
        encoding="utf-8",
    )

    print(
        f"Saved: {output_path}"
    )

    return output_path


# ============================================================
# Main report pipeline
# ============================================================

def run_all_reports(conn):
    """
    Run all analytical reports, charts,
    and the final summary report.
    """

    print()
    print("## Starting analytical reports...")

    # --------------------------------------------------------
    # 1. SQL analytical reports
    # --------------------------------------------------------

    results = run_reports(conn)

    # --------------------------------------------------------
    # 2. Charts
    # --------------------------------------------------------

    chart_paths = create_charts(
        results
    )

    # --------------------------------------------------------
    # 3. Summary report
    # --------------------------------------------------------

    summary_path = create_summary_report(
        conn,
        results=results,
        chart_paths=chart_paths,
    )

    return {
        "reports": results,
        "charts": chart_paths,
        "summary": summary_path,
    }


# ============================================================
# Backward-compatible entry point
# ============================================================

def run_reports_and_summary(conn):
    """
    Backward-compatible helper.

    Runs reports, charts, and summary.
    """

    return run_all_reports(conn)