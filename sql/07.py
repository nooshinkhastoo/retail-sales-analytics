import pandas as pd
import psycopg2
from psycopg2 import sql, extras
import os
from datetime import datetime
import json

# ============================================
# تنظیمات اتصال به PostgreSQL
# ============================================
# می‌تونی از环境变量 استفاده کنی یا مستقیم وارد کنی
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'retail_analytics'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

print("="*60)
print("🚀 شروع قدم ۷: ایجاد اسکیما و بارگذاری در PostgreSQL")
print("="*60)
print(f"📡 اتصال به PostgreSQL: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
print(f"🗄️  دیتابیس: {DB_CONFIG['database']}")
print(f"👤 کاربر: {DB_CONFIG['user']}")
print("="*60)

# ============================================
# ۱. بارگذاری جداول نرمال‌شده
# ============================================
print("\n📌 ۱. بارگذاری جداول نرمال‌شده...")

tables = {
    'dim_categories': pd.read_csv('data/processed/dim_categories.csv'),
    'dim_products': pd.read_csv('data/processed/dim_products.csv'),
    'dim_customers': pd.read_csv('data/processed/dim_customers.csv'),
    'dim_branches': pd.read_csv('data/processed/dim_branches.csv'),
    'fact_sales': pd.read_csv('data/processed/fact_sales.csv'),
    'fact_inventory_snapshot': pd.read_csv('data/processed/fact_inventory_snapshot.csv')
}

print("✅ جداول با موفقیت بارگذاری شدند:")
for table_name, df in tables.items():
    print(f"   {table_name}: {len(df):,} رکورد")

# ============================================
# ۲. اتصال به PostgreSQL
# ============================================
print("\n📌 ۲. اتصال به PostgreSQL...")

try:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cursor = conn.cursor()
    print("✅ اتصال برقرار شد")
except Exception as e:
    print(f"❌ خطا در اتصال: {e}")
    print("\n💡 راهنمایی:")
    print("   ۱. مطمئن شو PostgreSQL در حال اجراست")
    print("   ۲. تنظیمات اتصال را بررسی کن")
    print("   ۳. اگر از Docker استفاده می‌کنی، مطمئن شو کانتینر در حال اجراست")
    exit()

# ============================================
# ۳. ایجاد اسکیما (حذف و ایجاد مجدد)
# ============================================
print("\n📌 ۳. ایجاد اسکیما...")

# ۳.۱ حذف جداول (به ترتیب معکوس برای رعایت وابستگی‌ها)
print("\n   🔄 حذف جداول قدیمی (در صورت وجود)...")

drop_table_queries = [
    "DROP TABLE IF EXISTS fact_inventory_snapshot CASCADE;",
    "DROP TABLE IF EXISTS fact_sales CASCADE;",
    "DROP TABLE IF EXISTS dim_customers CASCADE;",
    "DROP TABLE IF EXISTS dim_products CASCADE;",
    "DROP TABLE IF EXISTS dim_branches CASCADE;",
    "DROP TABLE IF EXISTS dim_categories CASCADE;"
]

for query in drop_table_queries:
    try:
        cursor.execute(query)
        print(f"   ✅ اجرا شد: {query[:50]}...")
    except Exception as e:
        print(f"   ⚠️ خطا: {e}")

# ۳.۲ ایجاد جداول
print("\n   🏗️  ایجاد جداول جدید...")

create_table_queries = [
    # dim_categories
    """
    CREATE TABLE dim_categories (
        category_id VARCHAR(10) PRIMARY KEY,
        category_name VARCHAR(100) NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    
    # dim_products
    """
    CREATE TABLE dim_products (
        product_id VARCHAR(50) PRIMARY KEY,
        product_name VARCHAR(200) NOT NULL,
        category_id VARCHAR(10) NOT NULL,
        category_name VARCHAR(100),
        unit_cost DECIMAL(10, 2) NOT NULL CHECK (unit_cost >= 0),
        unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_product_category FOREIGN KEY (category_id) 
            REFERENCES dim_categories(category_id) ON DELETE RESTRICT
    );
    """,
    
    # dim_customers
    """
    CREATE TABLE dim_customers (
        customer_id VARCHAR(50) PRIMARY KEY,
        customer_first_name VARCHAR(100) NOT NULL,
        customer_last_name VARCHAR(100) NOT NULL,
        customer_full_name VARCHAR(200) NOT NULL,
        customer_email VARCHAR(200),
        customer_phone VARCHAR(20),
        customer_city VARCHAR(100),
        customer_signup_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    
    # dim_branches
    """
    CREATE TABLE dim_branches (
        branch_id VARCHAR(50) PRIMARY KEY,
        branch_name VARCHAR(200) NOT NULL,
        branch_city VARCHAR(100),
        sales_channel VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    
    # fact_sales
    """
    CREATE TABLE fact_sales (
        sale_id VARCHAR(50) PRIMARY KEY,
        sale_date DATE NOT NULL,
        customer_id VARCHAR(50) NOT NULL,
        product_id VARCHAR(50) NOT NULL,
        branch_id VARCHAR(50) NOT NULL,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
        discount_percent DECIMAL(5, 2) DEFAULT 0 CHECK (discount_percent >= 0 AND discount_percent <= 100),
        payment_method VARCHAR(50),
        gross_revenue DECIMAL(15, 2) NOT NULL CHECK (gross_revenue >= 0),
        discount_amount DECIMAL(15, 2) DEFAULT 0 CHECK (discount_amount >= 0),
        net_revenue DECIMAL(15, 2) NOT NULL CHECK (net_revenue >= 0),
        total_cost DECIMAL(15, 2) NOT NULL CHECK (total_cost >= 0),
        gross_profit DECIMAL(15, 2) NOT NULL,
        margin_percent DECIMAL(5, 2) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_sale_customer FOREIGN KEY (customer_id) 
            REFERENCES dim_customers(customer_id) ON DELETE RESTRICT,
        CONSTRAINT fk_sale_product FOREIGN KEY (product_id) 
            REFERENCES dim_products(product_id) ON DELETE RESTRICT,
        CONSTRAINT fk_sale_branch FOREIGN KEY (branch_id) 
            REFERENCES dim_branches(branch_id) ON DELETE RESTRICT
    );
    """,
    
    # fact_inventory_snapshot
    """
    CREATE TABLE fact_inventory_snapshot (
        inventory_id SERIAL PRIMARY KEY,
        product_id VARCHAR(50) NOT NULL,
        branch_id VARCHAR(50) NOT NULL,
        inventory_snapshot_date DATE NOT NULL,
        stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
        reorder_level INTEGER NOT NULL CHECK (reorder_level >= 0),
        stockout_risk BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) 
            REFERENCES dim_products(product_id) ON DELETE RESTRICT,
        CONSTRAINT fk_inventory_branch FOREIGN KEY (branch_id) 
            REFERENCES dim_branches(branch_id) ON DELETE RESTRICT,
        CONSTRAINT unique_inventory_snapshot UNIQUE (product_id, branch_id, inventory_snapshot_date)
    );
    """
]

for query in create_table_queries:
    try:
        cursor.execute(query)
        print(f"   ✅ جدول ساخته شد")
    except Exception as e:
        print(f"   ❌ خطا: {e}")
        conn.rollback()
        exit()

# ۳.۳ ایجاد ایندکس‌ها برای بهبود عملکرد
print("\n   🔍 ایجاد ایندکس‌ها...")

index_queries = [
    "CREATE INDEX idx_fact_sales_date ON fact_sales(sale_date);",
    "CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_id);",
    "CREATE INDEX idx_fact_sales_product ON fact_sales(product_id);",
    "CREATE INDEX idx_fact_sales_branch ON fact_sales(branch_id);",
    "CREATE INDEX idx_fact_inventory_product ON fact_inventory_snapshot(product_id);",
    "CREATE INDEX idx_fact_inventory_branch ON fact_inventory_snapshot(branch_id);",
    "CREATE INDEX idx_fact_inventory_date ON fact_inventory_snapshot(inventory_snapshot_date);",
    "CREATE INDEX idx_products_category ON dim_products(category_id);"
]

for query in index_queries:
    try:
        cursor.execute(query)
        print(f"   ✅ ایندکس ایجاد شد: {query.split('ON')[1].strip().split('(')[0]}")
    except Exception as e:
        print(f"   ⚠️ خطا در ایجاد ایندکس: {e}")

conn.commit()
print("✅ اسکیما با موفقیت ایجاد شد")

# ============================================
# ۴. بارگذاری داده‌ها (به ترتیب وابستگی)
# ============================================
print("\n📌 ۴. بارگذاری داده‌ها...")

def insert_data(cursor, table_name, df, columns=None):
    """درج داده در جدول با استفاده از execute_values"""
    if df.empty:
        print(f"   ⚠️ جدول {table_name} خالی است")
        return 0
    
    if columns is None:
        columns = df.columns.tolist()
    
    # تبدیل DataFrame به لیست تاپل‌ها
    data = [tuple(row) for row in df[columns].values]
    
    # ساخت کوئری
    placeholders = ','.join(['%s'] * len(columns))
    column_names = ','.join(columns)
    query = f"INSERT INTO {table_name} ({column_names}) VALUES %s"
    
    try:
        extras.execute_values(cursor, query, data)
        return len(data)
    except Exception as e:
        print(f"   ❌ خطا در بارگذاری {table_name}: {e}")
        print(f"   📝 نمونه داده: {data[0] if data else 'No data'}")
        raise

# ۴.۱ بارگذاری dim_categories
print("\n   📤 بارگذاری dim_categories...")
try:
    inserted = insert_data(cursor, 'dim_categories', tables['dim_categories'], 
                          ['category_id', 'category_name'])
    print(f"   ✅ {inserted:,} رکورد درج شد")
except Exception as e:
    print(f"   ❌ خطا: {e}")
    conn.rollback()
    exit()

# ۴.۲ بارگذاری dim_products
print("\n   📤 بارگذاری dim_products...")
try:
    inserted = insert_data(cursor, 'dim_products', tables['dim_products'],
                          ['product_id', 'product_name', 'category_id', 'category_name', 
                           'unit_cost', 'unit_price'])
    print(f"   ✅ {inserted:,} رکورد درج شد")
except Exception as e:
    print(f"   ❌ خطا: {e}")
    conn.rollback()
    exit()

# ۴.۳ بارگذاری dim_customers
print("\n   📤 بارگذاری dim_customers...")
try:
    inserted = insert_data(cursor, 'dim_customers', tables['dim_customers'],
                          ['customer_id', 'customer_first_name', 'customer_last_name', 
                           'customer_full_name', 'customer_email', 'customer_phone', 
                           'customer_city', 'customer_signup_date'])
    print(f"   ✅ {inserted:,} رکورد درج شد")
except Exception as e:
    print(f"   ❌ خطا: {e}")
    conn.rollback()
    exit()

# ۴.۴ بارگذاری dim_branches
print("\n   📤 بارگذاری dim_branches...")
try:
    inserted = insert_data(cursor, 'dim_branches', tables['dim_branches'],
                          ['branch_id', 'branch_name', 'branch_city', 'sales_channel'])
    print(f"   ✅ {inserted:,} رکورد درج شد")
except Exception as e:
    print(f"   ❌ خطا: {e}")
    conn.rollback()
    exit()

# ۴.۵ بارگذاری fact_sales
print("\n   📤 بارگذاری fact_sales...")
try:
    inserted = insert_data(cursor, 'fact_sales', tables['fact_sales'],
                          ['sale_id', 'sale_date', 'customer_id', 'product_id', 
                           'branch_id', 'quantity', 'unit_price', 'discount_percent',
                           'payment_method', 'gross_revenue', 'discount_amount', 
                           'net_revenue', 'total_cost', 'gross_profit', 'margin_percent'])
    print(f"   ✅ {inserted:,} رکورد درج شد")
except Exception as e:
    print(f"   ❌ خطا: {e}")
    conn.rollback()
    exit()

# ۴.۶ بارگذاری fact_inventory_snapshot
print("\n   📤 بارگذاری fact_inventory_snapshot...")
try:
    inserted = insert_data(cursor, 'fact_inventory_snapshot', tables['fact_inventory_snapshot'],
                          ['product_id', 'branch_id', 'inventory_snapshot_date', 
                           'stock_quantity', 'reorder_level', 'stockout_risk'])
    print(f"   ✅ {inserted:,} رکورد درج شد")
except Exception as e:
    print(f"   ❌ خطا: {e}")
    conn.rollback()
    exit()

conn.commit()
print("✅ همه داده‌ها با موفقیت بارگذاری شدند")

# ============================================
# ۵. اعتبارسنجی پس از بارگذاری
# ============================================
print("\n📌 ۵. اعتبارسنجی پس از بارگذاری...")

validation_queries = [
    ("تعداد کل رکوردها در dim_categories", "SELECT COUNT(*) FROM dim_categories"),
    ("تعداد کل رکوردها در dim_products", "SELECT COUNT(*) FROM dim_products"),
    ("تعداد کل رکوردها در dim_customers", "SELECT COUNT(*) FROM dim_customers"),
    ("تعداد کل رکوردها در dim_branches", "SELECT COUNT(*) FROM dim_branches"),
    ("تعداد کل رکوردها در fact_sales", "SELECT COUNT(*) FROM fact_sales"),
    ("تعداد کل رکوردها در fact_inventory_snapshot", "SELECT COUNT(*) FROM fact_inventory_snapshot"),
    ("کل درآمد ناخالص", "SELECT SUM(gross_revenue) FROM fact_sales"),
    ("کل درآمد خالص", "SELECT SUM(net_revenue) FROM fact_sales"),
    ("کل سود", "SELECT SUM(gross_profit) FROM fact_sales"),
    ("میانگین margin", "SELECT AVG(margin_percent) FROM fact_sales"),
]

print("\n📊 آمار پس از بارگذاری:")
for label, query in validation_queries:
    try:
        cursor.execute(query)
        result = cursor.fetchone()[0]
        if isinstance(result, (int, float)):
            if result > 1000:
                print(f"   {label}: {result:,.2f}")
            else:
                print(f"   {label}: {result:,.0f}")
        else:
            print(f"   {label}: {result}")
    except Exception as e:
        print(f"   ⚠️ خطا در اجرای {label}: {e}")

# ============================================
# ۶. ذخیره اسکیما در فایل
# ============================================
print("\n📌 ۶. ذخیره اسکیما...")

# ایجاد دایرکتوری sql اگر وجود ندارد
os.makedirs('sql', exist_ok=True)

# خواندن اسکیما از دیتابیس
schema_query = """
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable,
    character_maximum_length
FROM information_schema.columns 
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
"""

try:
    cursor.execute(schema_query)
    schema_info = cursor.fetchall()
    
    # تبدیل به DataFrame
    schema_df = pd.DataFrame(schema_info, columns=['table_name', 'column_name', 'data_type', 'is_nullable', 'max_length'])
    
    # ذخیره در CSV
    schema_df.to_csv('sql/schema_export.csv', index=False)
    print("✅ اسکیما ذخیره شد: sql/schema_export.csv")
except Exception as e:
    print(f"⚠️ خطا در ذخیره اسکیما: {e}")

# ============================================
# ۷. بستن اتصال
# ============================================
cursor.close()
conn.close()
print("\n✅ اتصال به PostgreSQL بسته شد")

# ============================================
# ۸. گزارش نهایی
# ============================================
print("\n" + "="*60)
print("📊 گزارش نهایی قدم ۷")
print("="*60)

print("\n📋 جداول بارگذاری شده:")
for table_name, df in tables.items():
    print(f"   {table_name}: {len(df):,} رکورد")

print("\n📊 خلاصه داده‌ها:")
print(f"   تعداد کل مشتریان: {len(tables['dim_customers']):,}")
print(f"   تعداد کل محصولات: {len(tables['dim_products']):,}")
print(f"   تعداد کل دسته‌بندی‌ها: {len(tables['dim_categories']):,}")
print(f"   تعداد کل شعب: {len(tables['dim_branches']):,}")
print(f"   تعداد کل فروش‌ها: {len(tables['fact_sales']):,}")
print(f"   تعداد کل رکوردهای موجودی: {len(tables['fact_inventory_snapshot']):,}")

print("\n💾 فایل‌های ذخیره شده:")
print("   📁 sql/schema_export.csv - اسکیما")
print("   📁 data/processed/*.csv - داده‌های نرمال‌شده")

print("="*60)
print("✅ قدم ۷ با موفقیت انجام شد!")
print("🎉 داده‌ها با موفقیت در PostgreSQL بارگذاری شدند!")
print("="*60)

# ============================================
# ۹. نمایش نمونه کوئری‌های تست
# ============================================
print("\n📌 نمونه کوئری‌های تست:")
print("""
-- ۱. تعداد فروش به تفکیک دسته‌بندی
SELECT 
    c.category_name,
    COUNT(f.sale_id) as total_sales,
    SUM(f.net_revenue) as total_revenue
FROM fact_sales f
JOIN dim_products p ON f.product_id = p.product_id
JOIN dim_categories c ON p.category_id = c.category_id
GROUP BY c.category_name
ORDER BY total_revenue DESC;

-- ۲. ۱۰ مشتری برتر بر اساس ارزش
SELECT 
    cu.customer_full_name,
    COUNT(f.sale_id) as num_orders,
    SUM(f.net_revenue) as total_spent
FROM fact_sales f
JOIN dim_customers cu ON f.customer_id = cu.customer_id
GROUP BY cu.customer_full_name
ORDER BY total_spent DESC
LIMIT 10;

-- ۳. محصولات با ریسک اتمام موجودی
SELECT 
    p.product_name,
    i.stock_quantity,
    i.reorder_level,
    i.stockout_risk
FROM fact_inventory_snapshot i
JOIN dim_products p ON i.product_id = p.product_id
WHERE i.stockout_risk = TRUE
ORDER BY i.stock_quantity ASC
LIMIT 20;

-- ۴. روند فروش روزانه
SELECT 
    sale_date,
    COUNT(*) as num_transactions,
    SUM(net_revenue) as daily_revenue
FROM fact_sales
GROUP BY sale_date
ORDER BY sale_date;
""")
