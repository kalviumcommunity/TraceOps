-- Task 1: WHERE Filtering - Filter Data Quality Issues Before Grouping
-- Documentation:
-- 1. WHERE transaction_date >= '2024-01-01': Ensures analysis is restricted to the current relevant financial year.
-- 2. WHERE amount > 0: Excludes refund transactions, zero-amount items, or error entries to reflect gross valid revenue.
-- 3. WHERE transaction_status = 'completed': Excludes pending, failed, or processing orders before grouping occurs.

SELECT 
    customer_id,
    SUM(amount) AS annual_revenue,
    COUNT(*) AS transaction_count
FROM transactions
WHERE transaction_date >= '2024-01-01'  -- Date range filter for analytical relevance
  AND amount > 0                         -- Filter out refunds and invalid zero transactions
  AND transaction_status = 'completed'   -- Include completed transactions only
GROUP BY customer_id
ORDER BY annual_revenue DESC;
