-- View: vw_active_customers
-- Purpose: Identify customers with recent activity (rolling 30-day window)
-- Business metric: Active customer count, rolling 30-day revenue, and order recency
-- Updated: Automatically recalculated on demand upon every query invocation
-- Used by: Customer success dashboard, retention & churn monitoring pipelines
--
-- Columns:
--   customer_id: Unique identifier for customer
--   customer_name: Full display name of customer
--   segment: Customer business tier/segment (Enterprise, SMB, Startup)
--   order_count_30d: Count of distinct orders placed in the last 30 days
--   revenue_30d: Total order revenue generated in the last 30 days
--   last_order_date: Date of most recent order placed by customer
--   days_since_order: Days elapsed between current date and last order date

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
