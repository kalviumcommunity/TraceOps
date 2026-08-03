-- Table & Aggregation: agg_daily_metrics
-- Purpose: Pre-aggregated summary table for daily order volume and total revenue metrics
-- Business Metric: Daily aggregated revenue and order counts for fast dashboard serving
-- Updated: Periodic batch refresh on schedule (e.g. daily/hourly ETL process)
-- Used by: Executive overview dashboard, financial daily reporting
--
-- Columns:
--   aggregation_date: Calendar date of the metric aggregation grain
--   metric_name: Standardized business metric identifier (e.g., 'total_revenue')
--   metric_value: Pre-computed numeric total for the metric on aggregation_date
--   row_count: Count of underlying raw transactions aggregated into this metric
--   updated_at: Timestamp when aggregation calculation was generated

CREATE TABLE IF NOT EXISTS agg_daily_metrics (
    aggregation_date DATE,
    metric_name VARCHAR(100),
    metric_value NUMERIC,
    row_count INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Aggregation Population Query
INSERT INTO agg_daily_metrics (aggregation_date, metric_name, metric_value, row_count, updated_at)
SELECT 
    DATE(o.order_date) AS aggregation_date,
    'total_revenue' AS metric_name,
    SUM(o.order_amount) AS metric_value,
    COUNT(*) AS row_count,
    CURRENT_TIMESTAMP AS updated_at
FROM orders o
GROUP BY DATE(o.order_date);
