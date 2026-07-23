# Dashboard Design Documentation

## Information Hierarchy Applied

The dashboard is built following the four-level information pyramid, ensuring immediate clarity for executive stakeholders while preserving deep exploration capabilities for data analysts.

### Level 1: Status (Top Row KPI Summary Cards)
Five key performance indicator (KPI) cards are positioned at the very top of the page to answer the fundamental executive question: *"Are we on track?"* within 5 seconds.
- **Revenue (`$5.2M`, `+12.5%` MoM):** Measures overall top-line financial velocity and business trajectory.
- **Active Customers (`2,500`, `+5.2%` MoM):** Tracks active customer base expansion and adoption health.
- **Avg Order Value (`$145`, `+3.1%` MoM):** Monitors customer purchasing power and cross-sell effectiveness.
- **Churn Rate (`4.8%`, `-1.2%` MoM):** Evaluates retention efficiency and customer attrition risk (inverse color metric where negative change represents improvement).
- **NPS Score (`72`, `+4` pts):** Assesses customer satisfaction, brand advocacy, and product sentiment.

### Level 2: Trends (Time Series Performance)
Located immediately below the KPI cards, time-series charts provide temporal context to answer: *"Is performance improving or deteriorating over time?"*
- **Monthly Revenue Trend (2024 Line Chart):** Tracks monthly revenue against a static `$5.0M` benchmark target line, highlighting Q3/Q4 target achievements.
- **Active vs. Churned Customers (Dual Line Chart):** Superimposes active account growth against churn numbers, illustrating the positive impact of retention initiatives launched in May 2024.
- **Average Order Value (AOV) Trend (Line Chart):** Visualizes month-by-month spend per order against a `$140` baseline target.

### Level 3: Segments (Distribution & Breakdown)
Positioned below trends, segment charts answer: *"Which areas of the business are driving growth or requiring intervention?"*
- **Revenue by Customer Segment (Horizontal Bar Chart):** Compares total revenue across Enterprise (`$2.1M`), Mid-Market (`$1.5M`), SMB (`$1.0M`), and Starter (`$0.6M`) tiers with exact dollar and percentage annotations.

### Level 4: Detail (Progressive Disclosure & Exploration)
Positioned at the bottom and accessible via the sidebar filters, Level 4 serves power users and analysts answering: *"What are the exact underlying transactional details behind anomalies?"*
- **Interactive Sidebar Filters:** Segment selection, custom date range filtering, and churn risk categorizations.
- **Dynamic Table Display:** Displays individual customer IDs, segment classifications, revenues, activity dates, and risk scores.
- **Raw Data Export:** Dedicated CSV download button for offline auditing and ad-hoc analysis.

---

## Design Principles Applied

1. **Progressive Disclosure:**
   - Summaries and top-level KPIs are rendered immediately on initial load.
   - Granular row-level data and exploratory controls are placed downstream or behind sidebar filters, reducing initial cognitive overload.

2. **Spatial Organisation (Western Reading Pattern):**
   - Critical KPIs are situated top-left (the first focal point).
   - Summary status occupies the top row, trend trajectory occupies the middle, and detailed tables occupy the bottom.

3. **Consistent Visual Metaphor:**
   - Standardized status colors across all visuals: Green (`#2ca02c`) indicates positive growth/target attainment; Red (`#d62728`) indicates churn or negative performance.
   - Up arrows indicate positive momentum, while down arrows signify reductions.

4. **Context Over Numbers:**
   - Raw numbers are accompanied by period-over-period delta indicators (`+12.5%`) and visual target benchmark lines (`$5.0M` target) so readers instantly know if a metric is good or bad.

---

## Colour Palette

- **Primary (`#1f77b4` - Standard Blue):** Represents primary revenue and active metric series.
- **Secondary (`#ff7f0e` - Vivid Orange):** Used for secondary comparisons, average order values, and Mid-Market segment.
- **Success (`#2ca02c` - Forest Green):** Denotes target attainment, positive retention, and SMB metrics.
- **Danger (`#d62728` - Crimson Red):** Highlights customer churn, high-risk churn tiers, and revenue loss warnings.

---

## Target Audience

- **Primary (VP of Sales):** Daily active viewer who monitors high-level KPI cards and segment revenue distributions to reallocate sales pipeline resources.
- **Secondary (CEO):** Weekly executive reviewer who glances at the Level 1 status row to confirm business health within 5 seconds.
- **Tertiary (Data Analysts & Finance):** Operational users who utilize Level 4 sidebar filters, custom date ranges, and CSV export functionality to conduct root-cause anomaly investigations.

---

## Data Sources

- **KPI Values:** Derived from database aggregation views (`vw_monthly_revenue` and `vw_active_customers`).
- **Trend Data:** Queried from the aggregated daily revenue table (`agg_daily_revenue`) and time-series transactional metrics.
- **Segment Data:** Computed from customer segmentation breakdown views (`vw_customer_segments`).
- **Detail Records:** Dynamically filtered from clean customer transaction logs in `analytics.db`.
