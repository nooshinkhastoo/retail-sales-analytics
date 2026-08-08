-- ============================================================
-- Retail Analytics Pipeline
-- Analysis Queries
-- ============================================================


-- ============================================================
-- 1. Daily Revenue Trend
-- ============================================================

SELECT
    sale_date,
    total_revenue,
    net_revenue,
    gross_profit,
    total_quantity_sold,
    gross_margin_percentage
FROM vw_daily_revenue
ORDER BY sale_date;


-- ============================================================
-- 2. Top 10 Products by Revenue
-- ============================================================

SELECT
    product_id,
    product_name,
    category_id,
    category_name,
    total_revenue,
    net_revenue,
    gross_profit,
    total_quantity_sold,
    gross_margin_percentage
FROM vw_product_revenue
ORDER BY total_revenue DESC
LIMIT 10;


-- ============================================================
-- 3. Top 10 Branches by Revenue
-- ============================================================

SELECT
    branch_id,
    branch_name,
    branch_city,
    sales_channel,
    total_revenue,
    net_revenue,
    gross_profit,
    total_quantity_sold,
    gross_margin_percentage
FROM vw_branch_revenue
ORDER BY total_revenue DESC
LIMIT 10;


-- ============================================================
-- 4. Category-Level Profitability
-- ============================================================

SELECT
    category_id,
    category_name,
    category_display_name,
    total_revenue,
    net_revenue,
    gross_profit,
    total_quantity_sold,
    gross_margin_percentage
FROM vw_category_margin
ORDER BY gross_profit DESC;


-- ============================================================
-- 5. Top 10 Customers by Lifetime Value
-- ============================================================

SELECT
    customer_id,
    customer_first_name,
    customer_last_name,
    customer_full_name,
    customer_city,
    total_orders,
    total_quantity_sold,
    total_revenue,
    net_revenue,
    gross_profit,
    gross_margin_percentage
FROM vw_customer_lifetime_value
WHERE net_revenue IS NOT NULL
ORDER BY
    net_revenue DESC NULLS LAST
LIMIT 10;


-- ============================================================
-- 6. Products Below Reorder Level / Stockout Risk
-- ============================================================

SELECT
    product_id,
    product_name,
    branch_id,
    branch_name,
    snapshot_date,
    stock_quantity,
    reorder_level,
    is_at_risk
FROM vw_stockout_risk
WHERE is_at_risk = TRUE
ORDER BY
    stock_quantity ASC,
    product_id ASC;


-- ============================================================
-- 7. Revenue by Category
-- ============================================================

SELECT
    category_name,
    total_revenue,
    net_revenue,
    gross_profit,
    total_quantity_sold,
    gross_margin_percentage
FROM vw_category_margin
ORDER BY total_revenue DESC;


-- ============================================================
-- 8. Revenue by Branch
-- ============================================================

SELECT
    branch_id,
    branch_name,
    branch_city,
    sales_channel,
    total_revenue,
    net_revenue,
    gross_profit,
    total_quantity_sold,
    gross_margin_percentage
FROM vw_branch_revenue
ORDER BY total_revenue DESC;


-- ============================================================
-- 9. Top 10 Products by Quantity Sold
-- ============================================================

SELECT
    product_id,
    product_name,
    category_name,
    total_quantity_sold,
    total_revenue,
    net_revenue,
    gross_profit,
    gross_margin_percentage
FROM vw_product_revenue
ORDER BY total_quantity_sold DESC
LIMIT 10;


-- ============================================================
-- 10. Best Categories by Gross Margin
-- ============================================================

SELECT
    category_id,
    category_name,
    category_display_name,
    total_revenue,
    net_revenue,
    gross_profit,
    gross_margin_percentage
FROM vw_category_margin
ORDER BY gross_margin_percentage DESC NULLS LAST;


-- ============================================================
-- 11. Top 10 Customers by Gross Profit
-- ============================================================

SELECT
    customer_id,
    customer_full_name,
    customer_city,
    total_orders,
    total_quantity_sold,
    net_revenue,
    gross_profit,
    gross_margin_percentage
FROM vw_customer_lifetime_value
ORDER BY gross_profit DESC NULLS LAST
LIMIT 10;


-- ============================================================
-- 12. Stockout Risk Count by Branch
-- ============================================================

SELECT
    branch_id,
    branch_name,
    COUNT(*) AS stockout_risk_products
FROM vw_stockout_risk
WHERE is_at_risk = TRUE
GROUP BY
    branch_id,
    branch_name
ORDER BY
    stockout_risk_products DESC,
    branch_id;