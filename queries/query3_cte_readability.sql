-- ==============================================================================
-- Query 3: Refactored - Use CTEs for Readability and Modular Testing
-- ==============================================================================
-- Business Question: What is the average transaction value and total revenue by customer segment for 2024?
-- Performance & Maintainability Improvement: Replaces nested subqueries with named,
-- independently testable CTE steps that execute top-to-bottom like a story.
-- ==============================================================================

WITH recent_transactions AS (
    -- Step 1: Filter to recent 2024 data and select only required columns
    SELECT transaction_id, amount, customer_id
    FROM transactions
    WHERE transaction_date >= '2024-01-01'
),
customer_with_segment AS (
    -- Step 2: Join recent transactions with customer segment dimensions
    SELECT 
        rt.transaction_id,
        rt.amount,
        c.customer_segment
    FROM recent_transactions rt
    JOIN customers c ON rt.customer_id = c.id
),
segment_metrics AS (
    -- Step 3: Calculate segment-level aggregated performance metrics
    SELECT 
        customer_segment,
        COUNT(DISTINCT transaction_id) as transaction_count,
        AVG(amount) as avg_transaction_value,
        SUM(amount) as total_revenue
    FROM customer_with_segment
    GROUP BY customer_segment
)
SELECT 
    customer_segment,
    avg_transaction_value,
    transaction_count,
    total_revenue
FROM segment_metrics
ORDER BY avg_transaction_value DESC;
