# SQL Business Metrics Query Design Guide

## Overview & The Real Scenario
When business metrics (such as Monthly Active Users, Revenue per Segment, and Signup Conversion Funnel) are recomputed in separate Jupyter notebooks or ephemeral Python scripts, teams inevitably calculate conflicting numbers. Finance, Sales, and Product arrive at different KPIs for the same period.

**The Solution:**
Define metrics once in standard `.sql` files stored under `queries/`. Python scripts, business intelligence tools, and data pipelines execute the same stored SQL query files. One definition, one file, one source of truth.

---

## 1. Metric Query Catalog

### Task 1: Monthly Active Users (`queries/monthly_active_users.sql`)
Calculates unique active customers per month with customer segment breakdowns using `FILTER` conditional aggregations over a rolling 12-month window:

```sql
-- queries/monthly_active_users.sql
SELECT 
    DATE_TRUNC('month', transaction_date)::DATE as month,
    COUNT(DISTINCT customer_id) as active_users,
    COUNT(DISTINCT customer_id) FILTER (WHERE customer_type='Enterprise') as enterprise_users,
    COUNT(DISTINCT customer_id) FILTER (WHERE customer_type='SMB') as smb_users
FROM transactions
WHERE transaction_date >= DATE_TRUNC('month', NOW()) - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', transaction_date)
ORDER BY month DESC;
```

---

### Task 2: Revenue by Segment (`queries/revenue_by_segment.sql`)
Joins `transactions` and `customers` to compute segment-level revenue, order counts, average order values, and revenue per customer:

```sql
-- queries/revenue_by_segment.sql
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
```

---

### Task 3: Funnel Conversion (`queries/conversion_funnel.sql`)
Tracks daily signup funnel progression and computes conversion percentages:

```sql
-- queries/conversion_funnel.sql
SELECT 
    DATE_TRUNC('day', u.created_at)::DATE as signup_date,
    COUNT(*) as signups,
    COUNT(*) FILTER (WHERE u.email_verified_at IS NOT NULL) as email_verified,
    COUNT(*) FILTER (WHERE u.first_purchase_at IS NOT NULL) as first_purchase,
    ROUND(100.0 * COUNT(*) FILTER (WHERE u.first_purchase_at IS NOT NULL) / COUNT(*), 1) as conversion_pct
FROM users u
WHERE u.created_at >= NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', u.created_at)
ORDER BY signup_date DESC;
```

---

## 2. Python Integration & Validation

### Loading & Executing Queries (`load_query`)
```python
from scripts.sql_business_metrics import load_query, execute_metrics_pipeline

# Load SQL from queries/
mau_query = load_query('monthly_active_users')

# Execute queries into DataFrames
mau_df, revenue_df, funnel_df = execute_metrics_pipeline(engine)
```

### Result Validation (`validate_metrics`)
Enforces strict quality assertions:
- **Null check**: Ensures zero null values across all columns.
- **Range bounds**: Confirms `monthly_revenue > 0` and `0.0 <= conversion_pct <= 100.0`.
- **Logical consistency**: Verifies `order_count > 0` whenever revenue is recorded.

```python
from scripts.sql_business_metrics import validate_metrics

validate_metrics(mau_df, revenue_df, funnel_df)
# Output: ✓ All metrics validated
```

---

## 3. Execution & Testing

Run the full Python pipeline:
```bash
python scripts/sql_business_metrics.py
```

Run unit test suite:
```bash
python -m pytest tests/test_sql_business_metrics.py
```
