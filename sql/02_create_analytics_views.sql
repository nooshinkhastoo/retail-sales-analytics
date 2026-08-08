-- ============================================================
-- Retail Analytics Pipeline
-- PostgreSQL Analytical Views
-- ============================================================

-- ============================================================
-- 1. Daily Revenue
-- ============================================================

CREATE OR REPLACE VIEW vw_daily_revenue AS
SELECT
    fs.sale_date,

    SUM(fs.gross_revenue) AS total_revenue,

    SUM(fs.net_revenue) AS net_revenue,

    SUM(fs.gross_profit) AS gross_profit,

    SUM(fs.quantity) AS total_quantity_sold,

    ROUND(
        (
            SUM(fs.gross_profit)
            / NULLIF(SUM(fs.net_revenue), 0)
        ) * 100,
        2
    ) AS gross_margin_percentage

FROM fact_sales fs

GROUP BY
    fs.sale_date

ORDER BY
    fs.sale_date;


-- ============================================================
-- 2. Product Revenue
-- ============================================================

CREATE OR REPLACE VIEW vw_product_revenue AS
SELECT
    fs.product_id,

    p.product_name,

    p.category_id,

    p.category_name,

    SUM(fs.gross_revenue) AS total_revenue,

    SUM(fs.net_revenue) AS net_revenue,

    SUM(fs.gross_profit) AS gross_profit,

    SUM(fs.quantity) AS total_quantity_sold,

    ROUND(
        (
            SUM(fs.gross_profit)
            / NULLIF(SUM(fs.net_revenue), 0)
        ) * 100,
        2
    ) AS gross_margin_percentage

FROM fact_sales fs

LEFT JOIN dim_products p
    ON fs.product_id = p.product_id

GROUP BY
    fs.product_id,
    p.product_name,
    p.category_id,
    p.category_name;


-- ============================================================
-- 3. Branch Revenue
-- ============================================================

CREATE OR REPLACE VIEW vw_branch_revenue AS
SELECT
    fs.branch_id,

    b.branch_name,

    b.branch_city,

    b.sales_channel,

    SUM(fs.gross_revenue) AS total_revenue,

    SUM(fs.net_revenue) AS net_revenue,

    SUM(fs.gross_profit) AS gross_profit,

    SUM(fs.quantity) AS total_quantity_sold,

    ROUND(
        (
            SUM(fs.gross_profit)
            / NULLIF(SUM(fs.net_revenue), 0)
        ) * 100,
        2
    ) AS gross_margin_percentage

FROM fact_sales fs

LEFT JOIN dim_branches b
    ON fs.branch_id = b.branch_id

GROUP BY
    fs.branch_id,
    b.branch_name,
    b.branch_city,
    b.sales_channel;


-- ============================================================
-- 4. Category Margin
-- ============================================================

CREATE OR REPLACE VIEW vw_category_margin AS
SELECT
    c.category_id,

    c.category_name,

    c.category_display_name,

    SUM(fs.gross_revenue) AS total_revenue,

    SUM(fs.net_revenue) AS net_revenue,

    SUM(fs.gross_profit) AS gross_profit,

    SUM(fs.quantity) AS total_quantity_sold,

    ROUND(
        (
            SUM(fs.gross_profit)
            / NULLIF(SUM(fs.net_revenue), 0)
        ) * 100,
        2
    ) AS gross_margin_percentage

FROM fact_sales fs

LEFT JOIN dim_products p
    ON fs.product_id = p.product_id

LEFT JOIN dim_categories c
    ON p.category_id = c.category_id

GROUP BY
    c.category_id,
    c.category_name,
    c.category_display_name;


-- ============================================================
-- 5. Customer Lifetime Value
-- ============================================================

CREATE OR REPLACE VIEW vw_customer_lifetime_value AS
SELECT
    fs.customer_id,

    c.customer_first_name,

    c.customer_last_name,

    c.customer_full_name,

    c.customer_city,

    COUNT(DISTINCT fs.sale_key) AS total_orders,

    SUM(fs.quantity) AS total_quantity_sold,

    SUM(fs.gross_revenue) AS total_revenue,

    SUM(fs.net_revenue) AS net_revenue,

    SUM(fs.gross_profit) AS gross_profit,

    ROUND(
        (
            SUM(fs.gross_profit)
            / NULLIF(SUM(fs.net_revenue), 0)
        ) * 100,
        2
    ) AS gross_margin_percentage

FROM fact_sales fs

LEFT JOIN dim_customers c
    ON fs.customer_id = c.customer_id

GROUP BY
    fs.customer_id,
    c.customer_first_name,
    c.customer_last_name,
    c.customer_full_name,
    c.customer_city;


-- ============================================================
-- 6. Stockout Risk
-- ============================================================

CREATE OR REPLACE VIEW vw_stockout_risk AS

SELECT
    snap.product_id,

    p.product_name,

    snap.branch_id,

    b.branch_name,

    snap.inventory_snapshot_date AS snapshot_date,

    snap.stock_quantity,

    snap.reorder_level,

    (
        snap.stock_quantity <= snap.reorder_level
    ) AS is_at_risk

FROM (
    SELECT
        inventory_snapshot_date,

        product_id,

        branch_id,

        stock_quantity,

        reorder_level,

        ROW_NUMBER() OVER (
            PARTITION BY
                product_id,
                branch_id

            ORDER BY
                inventory_snapshot_date DESC
        ) AS rn

    FROM fact_inventory_snapshot
) snap

LEFT JOIN dim_products p
    ON snap.product_id = p.product_id

LEFT JOIN dim_branches b
    ON snap.branch_id = b.branch_id

WHERE snap.rn = 1;