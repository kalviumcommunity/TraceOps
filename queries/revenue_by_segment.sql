-- queries/revenue_by_segment.sql
-- Monthly Revenue by Segment with order count, revenue, AOV, and per-customer revenue metrics
SELECT 
    c.customer_type,
    DATE_TRUNC('month', t.transaction_date)::DATE as month,
    COUNT(DISTINCT t.order_id) as order_count,
    SUM(t.amount) as monthly_revenue,
    ROUND(AVG(t.amount), 2) as avg_order_value,
    COUNT(DISTINCT t.customer_id) as unique_customers,
    ROUND(SUM(t.amount) / COUNT(DISTINCT t.customer_id), 2) as revenue_per_customer
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_date >= DATE_TRUNC('month', NOW()) - INTERVAL '12 months'
GROUP BY c.customer_type, DATE_TRUNC('month', t.transaction_date)
ORDER BY month DESC, monthly_revenue DESC;
