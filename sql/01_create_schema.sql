-- ============================================================
-- Retail Analytics Pipeline
-- PostgreSQL Schema
-- ============================================================


-- ============================================================
-- Dimension Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_categories (
    category_id           VARCHAR(20) PRIMARY KEY,
    category_name         VARCHAR(100) NOT NULL UNIQUE,
    category_display_name VARCHAR(100) NOT NULL
);


CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id          VARCHAR(20) PRIMARY KEY,
    customer_first_name  VARCHAR(100),
    customer_last_name   VARCHAR(100),
    customer_full_name   VARCHAR(200),
    customer_email       VARCHAR(200) UNIQUE,
    customer_phone       VARCHAR(30),
    customer_city        VARCHAR(100),
    customer_signup_date DATE
);


CREATE TABLE IF NOT EXISTS dim_products (
    product_id    VARCHAR(20) PRIMARY KEY,
    product_name  VARCHAR(200) NOT NULL,

    category_id VARCHAR(20) NOT NULL
        REFERENCES dim_categories(category_id),

    category_name VARCHAR(100),

    unit_cost NUMERIC(12,2)
        CHECK (unit_cost >= 0),

    unit_price NUMERIC(12,2)
        CHECK (unit_price >= 0)
);


CREATE TABLE IF NOT EXISTS dim_branches (
    branch_id     VARCHAR(20) PRIMARY KEY,
    branch_name   VARCHAR(200) NOT NULL,
    branch_city   VARCHAR(100),

    sales_channel VARCHAR(20)
        CHECK (
            sales_channel IN (
                'online',
                'store',
                'mobile',
                'partner'
            )
        )
);


-- ============================================================
-- Fact Sales
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_sales (
    sale_key BIGINT PRIMARY KEY,

    sale_id VARCHAR(20) NOT NULL UNIQUE,

    sale_date DATE NOT NULL,

    customer_id VARCHAR(20) NOT NULL
        REFERENCES dim_customers(customer_id),

    product_id VARCHAR(20) NOT NULL
        REFERENCES dim_products(product_id),

    branch_id VARCHAR(20) NOT NULL
        REFERENCES dim_branches(branch_id),

    payment_method VARCHAR(20) NOT NULL,

    quantity INTEGER NOT NULL
        CHECK (quantity > 0),

    unit_price NUMERIC(12,2) NOT NULL
        CHECK (unit_price >= 0),

    discount_percent NUMERIC(5,2) NOT NULL
        CHECK (
            discount_percent >= 0
            AND discount_percent <= 100
        ),

    gross_revenue NUMERIC(14,2) NOT NULL
        CHECK (gross_revenue >= 0),

    discount_amount NUMERIC(14,2) NOT NULL
        CHECK (discount_amount >= 0),

    net_revenue NUMERIC(14,2) NOT NULL
        CHECK (net_revenue >= 0),

    total_cost NUMERIC(14,2) NOT NULL
        CHECK (total_cost >= 0),

    gross_profit NUMERIC(14,2),

    margin_percentage NUMERIC(8,2)
);


-- ============================================================
-- Fact Inventory Snapshot
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_inventory_snapshot (
    inventory_snapshot_date DATE NOT NULL,

    product_id VARCHAR(20) NOT NULL
        REFERENCES dim_products(product_id),

    branch_id VARCHAR(20) NOT NULL
        REFERENCES dim_branches(branch_id),

    stock_quantity INTEGER NOT NULL
        CHECK (stock_quantity >= 0),

    reorder_level INTEGER NOT NULL
        CHECK (reorder_level >= 0),

    stockout_risk BOOLEAN NOT NULL,

    PRIMARY KEY (
        inventory_snapshot_date,
        product_id,
        branch_id
    )
);


-- ============================================================
-- Analytics Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_sales_date
ON fact_sales(sale_date);


CREATE INDEX IF NOT EXISTS idx_sales_customer
ON fact_sales(customer_id);


CREATE INDEX IF NOT EXISTS idx_sales_product
ON fact_sales(product_id);


CREATE INDEX IF NOT EXISTS idx_sales_branch
ON fact_sales(branch_id);


CREATE INDEX IF NOT EXISTS idx_inventory_product
ON fact_inventory_snapshot(product_id);


CREATE INDEX IF NOT EXISTS idx_inventory_branch
ON fact_inventory_snapshot(branch_id);


CREATE INDEX IF NOT EXISTS idx_inventory_date
ON fact_inventory_snapshot(inventory_snapshot_date);