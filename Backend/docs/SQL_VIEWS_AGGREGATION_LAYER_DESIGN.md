# SQL Views & Aggregation Layer Design

## Executive Summary

As data teams scale, computing metrics independently across dashboards leads to **metric drift**, where the same metric yields conflicting numbers across departments (e.g. Sales vs. Customer Success vs. Operations). 

This project implements a **Clean Data Layer** in SQLite/SQLAlchemy for **TraceOps**:
1. **SQL Views (`vw_`)**: Named queries that act as the single source of truth for business metric definitions without storing data on disk.
2. **Pre-Aggregated Summary Tables (`agg_`)**: Physical tables storing pre-computed metrics with an `updated_at` audit timestamp to deliver instant dashboard load times.
3. **Version Control & Naming Conventions**: All SQL object definitions are committed as `.sql` files in standard repository paths with documentation headers.

---

## Architecture & Data Layer Components

```
                +---------------------------------------+
                |           Raw Database Tables         |
                |   (customers, orders, products, etc)  |
                +-------------------+-------------------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
          v                                                   v
+-------------------------------+               +-------------------------------+
|      SQL Views (vw_)          |               | Pre-Aggregated Tables (agg_)  |
|  (Logic Only - Fresh Data)    |               | (Physical Table - Fast Read)  |
| - vw_active_customers         |               | - agg_daily_metrics           |
| - vw_product_performance      |               |   (Populated via Batch ETL)   |
+---------------+---------------+               +---------------+---------------+
                |                                                   |
                +-------------------------+-------------------------+
                                          |
                                          v
                        +-----------------------------------+
                        |   Python Analytics & Dashboards   |
                        | (Streamlit, Pandas, Data APIs)    |
                        +-----------------------------------+
```

---

## 1. Views Implemented

### View 1: `vw_active_customers`
- **File**: `database/views/vw_active_customers.sql`
- **Purpose**: Defines rolling 30-day active customer engagement and revenue metrics.
- **Query Logic**:
  ```sql
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
  ```

### View 2: `vw_product_performance`
- **File**: `database/views/vw_product_performance.sql`
- **Purpose**: Evaluates product sales volume, gross revenue, and average unit pricing across product categories.
- **Query Logic**:
  ```sql
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
  ```

---

## 2. Pre-Aggregated Table Implemented

### Summary Table: `agg_daily_metrics`
- **File**: `database/aggregations/agg_daily_metrics.sql`
- **Purpose**: Stores daily metric summaries (total revenue, transaction row count) to eliminate scanning millions of order rows during dashboard render.
- **Table Schema & Population**:
  ```sql
  CREATE TABLE IF NOT EXISTS agg_daily_metrics (
      aggregation_date DATE,
      metric_name VARCHAR(100),
      metric_value NUMERIC,
      row_count INTEGER,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  INSERT INTO agg_daily_metrics (aggregation_date, metric_name, metric_value, row_count, updated_at)
  SELECT 
      DATE(o.order_date) AS aggregation_date,
      'total_revenue' AS metric_name,
      SUM(o.order_amount) AS metric_value,
      COUNT(*) AS row_count,
      CURRENT_TIMESTAMP AS updated_at
  FROM orders o
  GROUP BY DATE(o.order_date);
  ```

---

## 3. Bonus / Follow-Up Questions Answered

### Q1: When a view definition changes, do existing dashboards automatically use the new definition? Why or why not?
**Answer**: 
Yes. Views in SQL databases store only query execution logic, not actual physical row data. When you issue a `CREATE OR REPLACE VIEW` or modify a view definition, the database engine updates the internal metadata definition. When any downstream dashboard, Python script, or notebook executes `SELECT * FROM vw_...`, the database dynamically executes the updated view logic. No dashboard code modifications or cache purges are required.

### Q2: If an aggregated table is computed once per hour, what happens to data between refresh cycles? How would you handle real-time metrics?
**Answer**: 
- **Between Refresh Cycles**: Data inside pre-aggregated tables represents a snapshot at the time of the last refresh batch (`updated_at`). Transactions occurring between refresh cycles are not yet included in `agg_` tables.
- **Handling Real-Time Metrics**: A **Hybrid (Lambda) Query Pattern** is used:
  ```sql
  -- Combine historical batch pre-aggregations with live in-progress hour query
  SELECT aggregation_date, metric_name, SUM(metric_value) AS total_revenue
  FROM agg_daily_metrics
  WHERE aggregation_date < CURRENT_DATE
  GROUP BY aggregation_date, metric_name
  UNION ALL
  SELECT DATE(order_date) AS aggregation_date, 'total_revenue' AS metric_name, SUM(order_amount) AS total_revenue
  FROM orders
  WHERE order_date >= CURRENT_DATE
  GROUP BY DATE(order_date);
  ```
  Alternatively, modern databases support **Incremental Materialized Views** or streaming tools (dbt mesh / Flink) for continuous near-real-time updates.

### Q3: How would you test that a view or aggregated table is correct before releasing it to dashboards?
**Answer**: 
1. **Reconciliation / Balance Audits**: Run assertion queries comparing `SUM(metric_value)` from `agg_daily_metrics` directly against raw `SUM(order_amount)` from `orders`. The delta must equal exactly zero.
2. **Schema & Constraint Validation**: Verify non-null constraints on primary keys and dimensions (`customer_id`, `aggregation_date`) and check range bounds (e.g. `revenue >= 0`, `order_count >= 0`).
3. **Automated Unit Tests**: Execute automated `pytest` suites verifying table structure, row counts, column names, and query latency benchmarks before merging PRs.
