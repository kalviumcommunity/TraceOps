-- Task 5: ORDER BY Ranking - Surface Top Performers
-- Documentation:
-- 1. GROUP BY c.customer_type, c.industry: Slices metrics across segment type and industry vertical.
-- 2. RANK() OVER (ORDER BY SUM(t.amount) DESC): Ranks business segments based on total aggregated revenue.
-- 3. HAVING COUNT(DISTINCT t.customer_id) >= 1: Filters out low-volume statistical noise.
-- 4. ORDER BY total_revenue DESC LIMIT 20: Sorts top performers first and limits output size.

SELECT 
    c.customer_type,
    c.industry,
    COUNT(DISTINCT t.customer_id) AS customers,
    SUM(t.amount) AS total_revenue,
    ROUND(AVG(t.amount), 2) AS avg_order,
    RANK() OVER (ORDER BY SUM(t.amount) DESC) AS revenue_rank
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_date >= '2024-01-01'
  AND t.transaction_status = 'completed'
  AND t.amount > 0
GROUP BY c.customer_type, c.industry
HAVING COUNT(DISTINCT t.customer_id) >= 1
ORDER BY total_revenue DESC
LIMIT 20;  -- Top N segment ranking
