# KPI Data Sources & Lineage Documentation
## Assignment 2.47 – KPI Card & Summary Metric Design

This document records the exact data source, compute function, SQL view reference,
validation cross-check, and comparison-period logic for every KPI card displayed on
the dashboard.

> **Rule:** No KPI value is hardcoded. Every number is computed at runtime from the
> validated clean data layer. Uploading a new dataset automatically updates all cards.

---

## 1. Total Revenue

| Field | Detail |
|---|---|
| **Business Question** | Is our revenue growing month-over-month? |
| **Source File** | `data/raw/kpi_transactions.csv` |
| **Compute Function** | `kpi_dashboard.compute_revenue()` → filters `payment_status == 'Success'`, sums `amount` |
| **SQL View Reference** | `database/views/vw_active_customers.sql` (revenue_30d column) |
| **Current Period** | Latest 30-day rolling window ending at `max(transaction_date)` |
| **Prior Period** | 30-day window ending 30 days before the current window anchor |
| **Directional Logic** | Standard – ↑ = good (green), ↓ = bad (red) |
| **Validation** | Cross-checked against `kpis/kpi_functions.py::calculate_revenue_per_customer()` – values consistent |
| **Streamlit Display** | `st.metric(delta_color='normal')` |

---

## 2. Active Users

| Field | Detail |
|---|---|
| **Business Question** | Are we retaining and growing our active customer base? |
| **Source File** | `data/raw/kpi_transactions.csv` |
| **Compute Function** | `kpis/kpi_functions.py::calculate_mau()` – `COUNT(DISTINCT customer_id)` where `payment_status == 'Success'` in last N days |
| **SQL View Reference** | `database/views/vw_active_customers.sql` (order_count_30d column) |
| **Current Period** | Distinct customers in last 30 days from reference date |
| **Prior Period** | Distinct customers in the 30 days prior to that |
| **Directional Logic** | Standard – ↑ = good (green), ↓ = bad (red) |
| **Validation** | Cross-checked with pandas `nunique()` on the same date-filtered slice – values match |
| **Streamlit Display** | `st.metric(delta_color='normal')` |

---

## 3. Average Order Value (AOV)

| Field | Detail |
|---|---|
| **Business Question** | Are customers spending more per transaction over time? |
| **Source File** | `data/raw/kpi_transactions.csv` |
| **Compute Function** | `kpi_dashboard.compute_aov()` → `mean(amount)` on successful transactions in window |
| **SQL View Reference** | Equivalent to `AVG(order_amount)` on `vw_active_customers` revenue_30d / order_count_30d |
| **Current Period** | Mean of `amount` for successful transactions in last 30 days |
| **Prior Period** | Mean of `amount` for successful transactions in the prior 30-day window |
| **Directional Logic** | Standard – ↑ = good (green), ↓ = bad (red) |
| **Validation** | Cross-checked against `calculate_revenue_per_customer()` baseline – directional trend matches |
| **Streamlit Display** | `st.metric(delta_color='normal')` |

---

## 4. Churn Rate  ⚠️ Inverted Metric

| Field | Detail |
|---|---|
| **Business Question** | Are we losing more customers than last period? |
| **Source File** | `data/raw/kpi_transactions.csv` |
| **Compute Function** | `kpis/kpi_functions.py::calculate_churn_rate()` – customers in P1 absent in P2, divided by |P1| |
| **SQL View Reference** | `queries/monthly_active_users.sql` – same two-window cohort logic |
| **Current Period** | P2 = `[ref - 30d, ref]`, P1 = `[ref - 60d, ref - 30d)` |
| **Prior Period** | Shifted back 30 days: P2 = `[ref - 60d, ref - 30d]`, P1 = `[ref - 90d, ref - 60d)` |
| **Directional Logic** | **INVERTED** – ↓ = good (green), ↑ = bad (red). `delta_color='inverse'` in Streamlit |
| **Validation** | Cross-checked set-difference manually on a 100-row sample – results match to 3 d.p. |
| **Streamlit Display** | `st.metric(delta_color='inverse')` ← critical for correct colour |

> **Important:** `delta_color='inverse'` is mandatory for churn. Without it, a churn
> increase would display green, misleading every stakeholder who reads the card.

---

## 5. Customer Satisfaction

| Field | Detail |
|---|---|
| **Business Question** | Are customers experiencing a reliable, high-quality service? |
| **Source File** | `data/raw/kpi_transactions.csv` |
| **Compute Function** | `kpi_dashboard.compute_satisfaction()` – Payment Success Rate × 5 (maps [0,1] → [0,5]) |
| **Proxy Rationale** | No direct satisfaction survey data in current dataset. PSR is the strongest available proxy: service failures (PSR < 1.0) directly reduce satisfaction. PSR of 1.0 → 5.0/5 (perfect), PSR of 0.95 → 4.75/5. |
| **SQL View Reference** | `kpis/kpi_functions.py::calculate_payment_success_rate()` |
| **Current Period** | PSR computed over the most recent 30-day window |
| **Prior Period** | PSR computed over the prior 30-day window |
| **Directional Logic** | Standard – ↑ = good (green), ↓ = bad (red) |
| **Validation** | `payment_success_rate` baseline ≈ 0.98 → satisfaction ≈ 4.9/5, consistent with simulated 98% success rate |
| **Streamlit Display** | `st.metric(delta_color='normal')` |

---

## Comparison Period Design

All periods are **automatically calculated** relative to `df['transaction_date'].max()`.
No manual date values are set anywhere in the code.

```
Reference date (ref) = latest transaction timestamp in dataset

Current window: (ref - 30 days, ref]
Prior window:   (ref - 60 days, ref - 30 days]
```

When a new CSV is uploaded, `ref` updates automatically and every KPI window shifts
with it — no code changes required.

---

## Data Flow Diagram

```
kpi_transactions.csv
        │
        ▼
kpis/kpi_functions.py          ← validated compute layer
  calculate_mau()
  calculate_churn_rate()
  calculate_payment_success_rate()
  calculate_revenue_per_customer()
        │
        ▼
kpi_dashboard.py               ← assignment file
  compute_all_kpis()           Task 1 – current + prior values
  add_trend_indicators()       Task 2 – arrows + colours
  add_change_display()         Task 3 – formatted Δ%
  run_streamlit_dashboard()    Task 4 – five KPI cards + charts
  print_kpi_report()           Task 5 – standalone lineage report
```

---

## Automated Update Flow (Bonus Answer)

> **Q:** When a new dataset is uploaded, how do KPI values update automatically
> without code changes?

**A:**
1. `kpi_dashboard.py` references `RAW_DATA_PATH` from `kpi_functions.py` (a constant
   pointing to `data/raw/kpi_transactions.csv`).
2. `compute_all_kpis()` derives `ref = df['transaction_date'].max()` at runtime.
3. All 30-day windows are computed relative to `ref` — no hardcoded dates exist.
4. Replacing the CSV file and running `streamlit run kpi_dashboard.py` (or the
   standalone script) is the only action needed.
5. For production: schedule a daily `python kpi_dashboard.py` via cron / GitHub Actions.
   The dashboard always reflects the latest uploaded data.

---

## KPI Card Checklist

| Requirement | Status |
|---|---|
| Maximum 5 KPI cards per dashboard | ✅ Exactly 5 |
| Each card shows current value | ✅ `Current_Display` column |
| Each card shows percentage change | ✅ `Change_Display` column (Task 3) |
| Each card shows trend direction | ✅ `Trend_Arrow` column (Task 2) |
| Colour logic correct for standard metrics | ✅ green > +2%, red < -2% |
| Churn Rate inverted (↓ = green) | ✅ `delta_color='inverse'` + inverted logic |
| Values from validated data layer | ✅ `kpis/kpi_functions.py` (no hardcoding) |
| Comparison period automatic | ✅ Relative to `max(transaction_date)` |
| Data lineage documented | ✅ This file |
