def run_quality_checks(conn):
    """
    Run post-load data quality checks.

    These checks validate:

    - row counts
    - primary key uniqueness
    - required key fields
    - foreign key relationships
    - numeric constraints
    - financial calculations
    - inventory constraints
    - business aggregates
    """

    validation_queries = [

        # ====================================================
        # Row counts
        # ====================================================

        (
            "dim_categories row count",
            """
            SELECT COUNT(*)
            FROM dim_categories
            """,
        ),

        (
            "dim_products row count",
            """
            SELECT COUNT(*)
            FROM dim_products
            """,
        ),

        (
            "dim_customers row count",
            """
            SELECT COUNT(*)
            FROM dim_customers
            """,
        ),

        (
            "dim_branches row count",
            """
            SELECT COUNT(*)
            FROM dim_branches
            """,
        ),

        (
            "fact_sales row count",
            """
            SELECT COUNT(*)
            FROM fact_sales
            """,
        ),

        (
            "fact_inventory_snapshot row count",
            """
            SELECT COUNT(*)
            FROM fact_inventory_snapshot
            """,
        ),

        # ====================================================
        # Primary key / uniqueness checks
        # ====================================================

        (
            "Duplicate category_id",
            """
            SELECT COUNT(*)
            FROM (
                SELECT category_id
                FROM dim_categories
                GROUP BY category_id
                HAVING COUNT(*) > 1
            ) duplicates
            """,
        ),

        (
            "Duplicate product_id",
            """
            SELECT COUNT(*)
            FROM (
                SELECT product_id
                FROM dim_products
                GROUP BY product_id
                HAVING COUNT(*) > 1
            ) duplicates
            """,
        ),

        (
            "Duplicate customer_id",
            """
            SELECT COUNT(*)
            FROM (
                SELECT customer_id
                FROM dim_customers
                GROUP BY customer_id
                HAVING COUNT(*) > 1
            ) duplicates
            """,
        ),

        (
            "Duplicate branch_id",
            """
            SELECT COUNT(*)
            FROM (
                SELECT branch_id
                FROM dim_branches
                GROUP BY branch_id
                HAVING COUNT(*) > 1
            ) duplicates
            """,
        ),

        (
            "Duplicate sale_id",
            """
            SELECT COUNT(*)
            FROM (
                SELECT sale_id
                FROM fact_sales
                GROUP BY sale_id
                HAVING COUNT(*) > 1
            ) duplicates
            """,
        ),

        (
            "Duplicate sale_key",
            """
            SELECT COUNT(*)
            FROM (
                SELECT sale_key
                FROM fact_sales
                GROUP BY sale_key
                HAVING COUNT(*) > 1
            ) duplicates
            """,
        ),

        # ====================================================
        # Required key checks
        # ====================================================

        (
            "NULL sale_id",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE sale_id IS NULL
            """,
        ),

        (
            "NULL customer_id",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE customer_id IS NULL
            """,
        ),

        (
            "NULL product_id",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE product_id IS NULL
            """,
        ),

        (
            "NULL branch_id",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE branch_id IS NULL
            """,
        ),

        # ====================================================
        # Foreign key checks
        # ====================================================

        (
            "Orphan product references",
            """
            SELECT COUNT(*)
            FROM fact_sales fs
            LEFT JOIN dim_products dp
                ON fs.product_id = dp.product_id
            WHERE dp.product_id IS NULL
            """,
        ),

        (
            "Orphan customer references",
            """
            SELECT COUNT(*)
            FROM fact_sales fs
            LEFT JOIN dim_customers dc
                ON fs.customer_id = dc.customer_id
            WHERE dc.customer_id IS NULL
            """,
        ),

        (
            "Orphan branch references",
            """
            SELECT COUNT(*)
            FROM fact_sales fs
            LEFT JOIN dim_branches db
                ON fs.branch_id = db.branch_id
            WHERE db.branch_id IS NULL
            """,
        ),

        (
            "Orphan category references",
            """
            SELECT COUNT(*)
            FROM dim_products dp
            LEFT JOIN dim_categories dc
                ON dp.category_id = dc.category_id
            WHERE dc.category_id IS NULL
            """,
        ),

        (
            "Orphan inventory product references",
            """
            SELECT COUNT(*)
            FROM fact_inventory_snapshot fis
            LEFT JOIN dim_products dp
                ON fis.product_id = dp.product_id
            WHERE dp.product_id IS NULL
            """,
        ),

        (
            "Orphan inventory branch references",
            """
            SELECT COUNT(*)
            FROM fact_inventory_snapshot fis
            LEFT JOIN dim_branches db
                ON fis.branch_id = db.branch_id
            WHERE db.branch_id IS NULL
            """,
        ),

        # ====================================================
        # Required field checks
        # ====================================================

        (
            "NULL sale_date",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE sale_date IS NULL
            """,
        ),

        (
            "NULL payment_method",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE payment_method IS NULL
            """,
        ),

        # ====================================================
        # Numeric constraints
        # ====================================================

        (
            "Invalid quantity",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE quantity <= 0
               OR quantity IS NULL
            """,
        ),

        (
            "Invalid unit price",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE unit_price < 0
               OR unit_price IS NULL
            """,
        ),

        (
            "Invalid discount percent",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE discount_percent < 0
               OR discount_percent > 100
               OR discount_percent IS NULL
            """,
        ),

        (
            "Invalid gross revenue",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE gross_revenue < 0
               OR gross_revenue IS NULL
            """,
        ),

        (
            "Invalid discount amount",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE discount_amount < 0
               OR discount_amount IS NULL
            """,
        ),

        (
            "Invalid net revenue",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE net_revenue < 0
               OR net_revenue IS NULL
            """,
        ),

        (
            "Invalid total cost",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE total_cost < 0
               OR total_cost IS NULL
            """,
        ),

        (
            "Invalid inventory stock quantity",
            """
            SELECT COUNT(*)
            FROM fact_inventory_snapshot
            WHERE stock_quantity < 0
               OR stock_quantity IS NULL
            """,
        ),

        (
            "Invalid reorder level",
            """
            SELECT COUNT(*)
            FROM fact_inventory_snapshot
            WHERE reorder_level < 0
               OR reorder_level IS NULL
            """,
        ),

        (
            "NULL stockout risk",
            """
            SELECT COUNT(*)
            FROM fact_inventory_snapshot
            WHERE stockout_risk IS NULL
            """,
        ),

        # ====================================================
        # Revenue calculation checks
        # ====================================================

        (
            "Incorrect gross revenue",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE ABS(
                gross_revenue
                - ROUND(
                    quantity * unit_price,
                    2
                )
            ) > 0.01
            """,
        ),

        (
            "Incorrect discount amount",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE ABS(
                discount_amount
                - ROUND(
                    gross_revenue
                    * discount_percent
                    / 100,
                    2
                )
            ) > 0.01
            """,
        ),

        (
            "Incorrect net revenue",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE ABS(
                net_revenue
                - ROUND(
                    gross_revenue
                    - discount_amount,
                    2
                )
            ) > 0.01
            """,
        ),

        (
            "Incorrect total cost",
            """
            SELECT COUNT(*)
            FROM fact_sales fs
            JOIN dim_products dp
                ON fs.product_id = dp.product_id
            WHERE ABS(
                fs.total_cost
                - ROUND(
                    fs.quantity * dp.unit_cost,
                    2
                )
            ) > 0.01
            """,
        ),

        (
            "Incorrect gross profit",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE ABS(
                gross_profit
                - ROUND(
                    net_revenue - total_cost,
                    2
                )
            ) > 0.01
            """,
        ),

        (
            "Incorrect margin percentage",
            """
            SELECT COUNT(*)
            FROM fact_sales
            WHERE net_revenue > 0
              AND ABS(
                    margin_percentage
                    - ROUND(
                        (
                            gross_profit
                            / net_revenue
                        ) * 100,
                        2
                    )
                  ) > 0.01
            """,
        ),

        # ====================================================
        # Inventory checks
        # ====================================================

        (
            "Duplicate inventory snapshots",
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    product_id,
                    branch_id,
                    inventory_snapshot_date
                FROM fact_inventory_snapshot
                GROUP BY
                    product_id,
                    branch_id,
                    inventory_snapshot_date
                HAVING COUNT(*) > 1
            ) duplicates
            """,
        ),

        # ====================================================
        # Business aggregates
        # ====================================================

        (
            "Total gross revenue",
            """
            SELECT SUM(gross_revenue)
            FROM fact_sales
            """,
        ),

        (
            "Total net revenue",
            """
            SELECT SUM(net_revenue)
            FROM fact_sales
            """,
        ),

        (
            "Total gross profit",
            """
            SELECT SUM(gross_profit)
            FROM fact_sales
            """,
        ),

        (
            "Average margin",
            """
            SELECT AVG(margin_percentage)
            FROM fact_sales
            """,
        ),
    ]

    cursor = conn.cursor()

    results = {}

    try:
        for label, query in validation_queries:

            cursor.execute(query)

            result = cursor.fetchone()[0]

            results[label] = result

            print(
                f"{label}: {result}"
            )

        return results

    finally:
        cursor.close()