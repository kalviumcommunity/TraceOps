-- Task 2: Detect Unmatched Keys
-- Identify records on either side of the join relationship that do not match

-- 1. Customers with NO orders (Unmatched on Right)
SELECT 
    c.customer_id, 
    c.customer_type, 
    c.signup_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL
ORDER BY c.signup_date;

-- 2. Orders with NO matching customer (Orphaned records / Unmatched on Left)
SELECT 
    o.order_id, 
    o.customer_id, 
    o.order_date,
    o.order_amount
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
ORDER BY o.order_date;
