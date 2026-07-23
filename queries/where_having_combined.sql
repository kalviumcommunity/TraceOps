-- Task 4: WHERE + HAVING Combined - Filter Data Quality AND Aggregate Thresholds
-- Documentation:
-- 1. WHERE clause (Data Quality & Row Validation):
--    - transaction_date >= '2024-01-01': Limits rows to current time horizon.
--    - transaction_status = 'completed': Filters out pending or cancelled orders.
--    - amount > 0: Excludes zero and refund transactions at the raw record stage.
-- 2. HAVING clause (Business Aggregate Thresholds):
--    - COUNT(DISTINCT customer_id) >= 1: Ensures segment size meets customer density requirement.
--    - SUM(amount) > 1000: Ensures total segment revenue exceeds key financial threshold.

SELECT 
    c.customer_type,
    COUNT(DISTINCT t.customer_id) AS segment_customers,
    SUM(t.amount) AS segment_revenue,
    ROUND(AVG(t.amount), 2) AS avg_order_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_date >= '2024-01-01'      -- WHERE: Filters row-level data quality
  AND t.transaction_status = 'completed'           -- WHERE: Filters operational transaction status
  AND t.amount > 0                                 -- WHERE: Ensures numerical row validity
GROUP BY c.customer_type
HAVING COUNT(DISTINCT t.customer_id) >= 1         -- HAVING: Enforces segment size metric threshold
  AND SUM(t.amount) > 1000                         -- HAVING: Enforces segment revenue metric threshold
ORDER BY segment_revenue DESC;
