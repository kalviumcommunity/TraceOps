-- ==============================================================================
-- Query 2: Refactored - Apply Filters Before JOINs (Early Filtering Pattern)
-- ==============================================================================
-- Business Question: What high-value (> $100) transactions occurred in 2024 for US customers?
-- Performance Improvement: Filters millions of transaction rows BEFORE joining
-- customer and product tables, reducing intermediate cartesian/join memory space.
-- ==============================================================================

WITH filtered_transactions AS (
    -- Step 1: Filter transactions BEFORE performing expensive table joins
    SELECT 
        transaction_id,
        customer_id,
        product_id,
        amount,
        transaction_date
    FROM transactions
    WHERE transaction_date >= '2024-01-01'
      AND amount > 100
)
SELECT 
    ft.transaction_id,
    ft.amount,
    c.customer_name,
    p.product_name
FROM filtered_transactions ft
JOIN customers c ON ft.customer_id = c.id
JOIN products p ON ft.product_id = p.id
WHERE c.country = 'USA'
LIMIT 5000;
