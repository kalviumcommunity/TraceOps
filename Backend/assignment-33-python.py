"""
Assignment 33: SQL Views & Aggregation Layer Design
Submission Python script demonstrating creation and querying of SQL views and pre-aggregated tables.
"""

import time
import pandas as pd
from sqlalchemy import create_engine, text

# Setup Database Engine
engine = create_engine("sqlite:///analytics.db")

def execute_sql(sql_query: str):
    """Utility function to execute DDL / DML SQL statements."""
    with engine.connect() as conn:
        conn.execute(text(sql_query))
        conn.commit()

# Ensure base table schema compatibility
with engine.connect() as conn:
    result = conn.execute(text("PRAGMA table_info(customers)")).fetchall()
    cols = [r[1] for r in result]
    if 'deleted_at' not in cols:
        conn.execute(text("ALTER TABLE customers ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL"))
        conn.commit()

# Task 1: Create Two SQL Views
print("--- Task 1: Create Views ---")
view1_sql = """
CREATE VIEW IF NOT EXISTS vw_active_customers AS
SELECT 
    c.customer_id,
    c.customer_name,
    c.customer_segment AS segment,
    COUNT(DISTINCT o.order_id) AS order_count_30d,
    COALESCE(SUM(o.order_amount), 0) AS revenue_30d,
    MAX(o.order_date) AS last_order_date,
    CAST(JULIANDAY('now') - JULIANDAY(MAX(o.order_date)) AS INTEGER) AS days_since_order
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
    AND o.order_date >= DATE('now', '-30 days')
WHERE c.deleted_at IS NULL
GROUP BY c.customer_id, c.customer_name, c.customer_segment;
"""

view2_sql = """
CREATE VIEW IF NOT EXISTS vw_product_performance AS
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    COALESCE(SUM(oi.quantity), 0) AS units_sold,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_revenue,
    COALESCE(AVG(oi.unit_price), 0) AS avg_unit_price,
    MAX(o.order_date) AS last_sold_date
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE oi.quantity > 0
GROUP BY p.product_id, p.product_name, p.category;
"""

execute_sql(view1_sql)
execute_sql(view2_sql)

# Query views to confirm they work
active_customers = pd.read_sql("SELECT * FROM vw_active_customers LIMIT 10", engine)
custom_metric = pd.read_sql("SELECT * FROM vw_product_performance LIMIT 10", engine)

print("View 1 columns:", active_customers.columns.tolist())
print("View 2 columns:", custom_metric.columns.tolist())

# Task 2: Create One Pre-Aggregated Summary Table
print("\n--- Task 2: Create Pre-Aggregated Summary Table ---")
execute_sql("DROP TABLE IF EXISTS agg_daily_metrics;")

create_table_sql = """
CREATE TABLE agg_daily_metrics (
    aggregation_date DATE,
    metric_name VARCHAR(100),
    metric_value NUMERIC,
    row_count INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
execute_sql(create_table_sql)

populate_sql = """
INSERT INTO agg_daily_metrics (aggregation_date, metric_name, metric_value, row_count, updated_at)
SELECT 
    DATE(o.order_date) AS aggregation_date,
    'total_revenue' AS metric_name,
    SUM(o.order_amount) AS metric_value,
    COUNT(*) AS row_count,
    CURRENT_TIMESTAMP AS updated_at
FROM orders o
GROUP BY DATE(o.order_date);
"""
execute_sql(populate_sql)

# Verify
agg_data = pd.read_sql("SELECT * FROM agg_daily_metrics ORDER BY aggregation_date DESC LIMIT 10", engine)
print(f"Aggregated {len(agg_data)} rows")
print(agg_data)

# Measure query latency
start = time.time()
result = pd.read_sql("SELECT metric_name, SUM(metric_value) FROM agg_daily_metrics GROUP BY metric_name", engine)
elapsed = time.time() - start
print(f"Query time: {elapsed*1000:.2f}ms")

# Task 3: Query Views & Aggregated Tables from Python
print("\n--- Task 3: Query Views & Aggregated Tables ---")

# Query View 1: Active Customers
active_cust_df = pd.read_sql("""
    SELECT 
        customer_id, 
        customer_name, 
        revenue_30d,
        days_since_order
    FROM vw_active_customers
    ORDER BY revenue_30d DESC
    LIMIT 20
""", engine)

print("Top 20 Active Customers:")
print(active_cust_df.head())

# Query View 2: Custom Metric (Product Performance)
custom_result = pd.read_sql("""
    SELECT * FROM vw_product_performance
    LIMIT 20
""", engine)

print("\nProduct Performance Results:")
print(custom_result.head())

# Query Pre-Aggregated Table
agg_result = pd.read_sql("""
    SELECT 
        aggregation_date,
        metric_name,
        metric_value
    FROM agg_daily_metrics
    ORDER BY aggregation_date DESC
    LIMIT 30
""", engine)

print("\nDaily Aggregated Metrics:")
print(agg_result.head())

# Filtering Capability Example: Revenue by Segment
active_by_segment = pd.read_sql("""
    SELECT 
        segment,
        COUNT(*) as customer_count,
        SUM(revenue_30d) as total_segment_revenue,
        AVG(revenue_30d) as avg_customer_revenue
    FROM vw_active_customers
    GROUP BY segment
    ORDER BY total_segment_revenue DESC
""", engine)

print("\nRevenue by Segment:")
print(active_by_segment)
