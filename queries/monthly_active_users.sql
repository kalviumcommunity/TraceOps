-- queries/monthly_active_users.sql
-- Monthly Active Users: distinct customers with transactions breakdown by customer segment
SELECT 
    DATE_TRUNC('month', transaction_date)::DATE as month,
    COUNT(DISTINCT customer_id) as active_users,
    COUNT(DISTINCT customer_id) FILTER (WHERE customer_type='Enterprise') as enterprise_users,
    COUNT(DISTINCT customer_id) FILTER (WHERE customer_type='SMB') as smb_users
FROM transactions
WHERE transaction_date >= DATE_TRUNC('month', NOW()) - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', transaction_date)
ORDER BY month DESC;
