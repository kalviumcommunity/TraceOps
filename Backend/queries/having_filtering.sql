-- Task 3: HAVING Filtering - Filter Aggregate Groups After Grouping
-- Documentation:
-- 1. WHERE vs HAVING Distinction:
--    - WHERE filters individual row-level records BEFORE aggregation takes place.
--    - HAVING filters summary metrics AFTER the database engine calculates GROUP BY aggregates.
-- 2. Business Logic:
--    - HAVING SUM(amount) > 10000: Retains only customer accounts with >$10k total spending.
--    - HAVING COUNT(*) >= 5: Retains only frequent buyers with 5 or more completed purchases.

SELECT 
    customer_id,
    COUNT(*) AS transaction_count,
    SUM(amount) AS annual_revenue
FROM transactions
WHERE transaction_date >= '2024-01-01'  -- WHERE filters rows prior to aggregation
  AND transaction_status = 'completed'
GROUP BY customer_id
HAVING SUM(amount) > 10000              -- HAVING filters total group revenue
  AND COUNT(*) >= 5                     -- HAVING filters aggregate purchase frequency
ORDER BY annual_revenue DESC;
