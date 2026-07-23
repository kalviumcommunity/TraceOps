-- Task 2: GROUP BY and Aggregation - Multi-Dimensional Slicing
-- Documentation:
-- 1. GROUP BY c.customer_type, STRFTTIME('%Y-%m-01', t.transaction_date): Groups data across 2 key dimensions (Customer Type & Monthly Grain).
-- 2. Uses 4 aggregate functions: COUNT(DISTINCT customer_id), COUNT(*), SUM(amount), AVG(amount).
-- 3. WHERE clause filters row-level input data FIRST before the engine groups records into summary buckets.

SELECT 
    c.customer_type,
    strftime('%Y-%m-01', t.transaction_date) AS month,
    COUNT(DISTINCT t.customer_id) AS unique_customers,
    COUNT(*) AS transaction_count,
    SUM(t.amount) AS monthly_revenue,
    AVG(t.amount) AS avg_transaction
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_date >= '2024-01-01'  -- WHERE filters raw rows before GROUP BY aggregation
  AND t.transaction_status = 'completed'
GROUP BY c.customer_type, strftime('%Y-%m-01', t.transaction_date)
ORDER BY month DESC, monthly_revenue DESC;
