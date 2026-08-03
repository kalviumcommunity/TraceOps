# Chart 1: Support Response Time vs. Customer Churn Rate

## Data Table: Response Time Buckets vs Churn Rate

| First Response Bucket | Customer Count | Churn Count | Churn Rate (%) | Churn Risk vs Baseline |
| :--- | :--- | :--- | :--- | :--- |
| **< 2 Hours** | 18,500 | 555 | **3.0%** | Baseline (1.0x) |
| **2 – 4 Hours** | 14,200 | 710 | **5.0%** | 1.67x |
| **4 – 24 Hours** | 11,800 | 1,062 | **9.0%** | 3.00x |
| **> 24 Hours** | 5,500 | 660 | **12.0%** | **4.00x** |
| **Total / Overall** | **50,000** | **2,987** | **6.0%** | — |

## ASCII Visualization: Churn Rate by Response Bucket

```
Response Bucket | Churn Rate (%)
----------------+----------------------------------------
< 2 Hours       | [===] 3.0%
2 - 4 Hours     | [=====] 5.0%
4 - 24 Hours    | [=========] 9.0%
> 24 Hours      | [============] 12.0%
```

## Key Observations
1. **Linear Escalation (0 to 4 Hours):** Churn increases predictably from 3% to 5%.
2. **Steep Slope (4 to 24 Hours):** Churn nearly doubles from 5% to 9%.
3. **Severe Default Level (> 24 Hours):** Reaches 12.0%, resulting in 4x higher customer loss.
