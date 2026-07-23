-- Task 4: Multi-Table Join
-- Joins customers, orders, order_items, and products tables
-- Slices Enterprise customers and calculates line item total revenue

SELECT 
    c.customer_id,
    c.customer_type,
    o.order_id,
    o.order_date,
    oi.product_id,
    p.product_name,
    oi.quantity,
    oi.unit_price,
    (oi.quantity * oi.unit_price) as line_total
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE c.customer_type = 'Enterprise'
ORDER BY o.order_date DESC;
