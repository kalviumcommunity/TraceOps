# Clean Data Layer Naming Conventions

## Architecture Overview

The TraceOps Clean Data Layer serves as the single source of truth for business metrics across sales, customer success, and operations dashboards. By establishing version-controlled views and pre-aggregated summary tables, we eliminate metric drift, optimize query execution, and enforce strict naming standards across teams.

---

## 1. Views
- **Prefix**: `vw_`
- **Pattern**: `vw_[business_entity]_[metric]`
- **Description**: Logic-only SQL views that calculate real-time business metrics directly from raw tables. Views store definitions, not data.
- **Examples & Applied Objects**:
  - `vw_active_customers`: Evaluates 30-day customer activity, revenue, and order recency for active customer tracking.
  - `vw_product_performance`: Aggregates order items and sales volume per product and category.

---

## 2. Pre-Aggregated Tables
- **Prefix**: `agg_`
- **Pattern**: `agg_[grain]_[subject]`
- **Description**: Physical tables storing pre-computed metrics at a specific aggregation grain (e.g. daily, hourly) to ensure sub-millisecond dashboard load times.
- **Examples & Applied Objects**:
  - `agg_daily_metrics`: Daily summary table pre-computing total revenue and transaction counts.

---

## 3. Columns in Aggregated Tables
All pre-aggregated tables must enforce standard audit and metadata columns:
- **Timestamp Column**: `updated_at` (or `created_at`) indicating exact timestamp when aggregation batch was computed.
- **Audit Volume**: `row_count` capturing the count of raw records aggregated into each row.
- **Grain Dimension**: Date or entity grain column (`aggregation_date`, `hour`, `customer_id`).

---

## 4. Applied Conventions Matrix

| Object Name | Object Type | Grain / Entity | Key Metrics / Columns | Usage |
| :--- | :--- | :--- | :--- | :--- |
| `vw_active_customers` | View (`vw_`) | Customer (`active_customers`) | `order_count_30d`, `revenue_30d`, `days_since_order` | Customer Success & Retention Dashboards |
| `vw_product_performance` | View (`vw_`) | Product (`product_performance`) | `total_orders`, `units_sold`, `total_revenue`, `avg_unit_price` | Sales & Product Operations Dashboards |
| `agg_daily_metrics` | Pre-Agg Table (`agg_`) | Daily (`daily_metrics`) | `aggregation_date`, `metric_name`, `metric_value`, `row_count`, `updated_at` | Financial & Executive Overview Dashboards |

---

## 5. Key Business Benefits
- **Zero Metric Drift**: Revenue and customer activity metrics are defined exactly once in SQL view logic.
- **Instant Dashboard Performance**: Expensive multi-table joins are pre-computed in physical `agg_` tables for immediate response.
- **Immediate Navigation**: Engineers and analysts instantly know an object's behavior and update cycle from its prefix (`vw_` vs `agg_`).
- **Version Control & Auditability**: SQL definitions reside in git repositories with documentation headers for lineage tracking.
