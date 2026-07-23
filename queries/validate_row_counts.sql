-- Row Count & Distinct Key Validation Query
-- Compares row counts and distinct customer keys to analyze join multiplicity

SELECT 
    'customers' as table_name, 
    COUNT(DISTINCT customer_id) as distinct_keys, 
    COUNT(*) as total_rows
FROM customers

UNION ALL

SELECT 
    'orders', 
    COUNT(DISTINCT customer_id), 
    COUNT(*)
FROM orders

UNION ALL

SELECT 
    'joined_left', 
    COUNT(DISTINCT c.customer_id), 
    COUNT(*)
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id;
