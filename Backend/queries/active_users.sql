-- queries/active_users.sql
-- Monthly Active Users: distinct customers with transaction in last 12 months
SELECT 
    DATE_TRUNC('month', transaction_date)::DATE as month,
    COUNT(DISTINCT customer_id) as active_users
FROM transactions
WHERE transaction_date >= DATE_TRUNC('month', NOW()) - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', transaction_date)
ORDER BY month DESC;
