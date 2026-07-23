-- Task 1: LEFT JOIN with Row Count Validation
-- All customers with their orders (some have multiple, some have none)
-- Preserves all customer records while aggregating order history

SELECT 
    c.customer_id,
    c.customer_type,
    COUNT(DISTINCT o.order_id) as order_count,
    COALESCE(SUM(o.order_amount), 0.0) as total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_type
ORDER BY total_spent DESC NULLS LAST;
