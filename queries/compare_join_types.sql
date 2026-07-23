-- Task 3: Compare Join Types (INNER, LEFT, FULL OUTER)

-- 1. INNER JOIN (Matched records only)
SELECT 
    c.customer_id, 
    o.order_id, 
    o.order_amount
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id;

-- 2. LEFT JOIN (All customers, matched orders)
SELECT 
    c.customer_id, 
    o.order_id, 
    o.order_amount
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id;

-- 3. FULL OUTER JOIN (All customers and all orders)
SELECT 
    c.customer_id, 
    o.order_id, 
    o.order_amount
FROM customers c
FULL OUTER JOIN orders o ON c.customer_id = o.customer_id;
