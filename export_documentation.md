# Analysis Report & Export Guide

Automated export pipeline guide for stakeholders and data analysts.

---

## What's Included

Each report run generates a timestamped export package containing four distinct files designed for specific business use cases:

### 1. `cleaned_data.csv`
- **Purpose:** Raw, cleaned, and validated analytical dataset for custom downstream analysis.
- **Record Count:** Up to 50,000 customer records per extraction run.
- **Schema & Columns:** `customer_id`, `date`, `segment`, `churn_risk`, `monthly_spend`, `support_interactions`, `response_time_hours`
- **Use Case:** Enables financial modeling, custom Excel pivot tables, and machine learning imports.
- **Refresh Schedule:** Updated automatically daily at 5:00 PM (or on-demand via dashboard trigger).

### 2. `summary_report.pdf`
- **Purpose:** Executive summary report optimized for leadership meetings, printing, and email attachments.
- **Content:** Core business findings, revenue exposure metrics, risk segmentations, and strategic recommendations.
- **Format & Branding:** Portable PDF format with standardized typography and page layouts.
- **Use Case:** Executive briefings, board slide decks, and quarterly strategy reviews.

### 3. `interactive_report.html`
- **Purpose:** Comprehensive interactive dashboard accessible in any web browser without local Python installation.
- **Content:** Executive markdown summary paired with interactive Plotly visualizations (Revenue Trend, Churn Risk Profile, Support Speed Impact).
- **Interactivity:** Hover tooltips, zooming, panning, legend filtering, and dynamic chart resizing.
- **Sharing:** Single self-contained HTML file (uses Plotly CDN) that can be emailed or hosted on an internal intranet portal.

### 4. `README.md`
- **Purpose:** Machine-readable and human-readable metadata logging.
- **Metadata Fields:** Generation timestamp (ISO-8601), record count, column names, and dataset date boundaries.
- **Use Case:** Audit trails, data lineage verification, and automated compliance logging.

---

## How to Use These Files

1. **For Excel / Data Analysis:** Open `cleaned_data.csv` in Excel or Power BI to build custom visualizations and formulas.
2. **For Executive Presentations:** Share or present `summary_report.pdf` during leadership calls or attach to status emails.
3. **For Deep Exploration:** Double-click `interactive_report.html` to open in Google Chrome, Microsoft Edge, or Safari to inspect data points on hover.
4. **For Compliance & Auditing:** Reference `README.md` to verify exact data ranges and extraction timestamps.

---

## Automated Scheduling & Error Handling

- **Schedule Execution:** Automated report scripts execute daily at 5:00 PM via Python `schedule` or OS Cron / Task Scheduler.
- **Resilience Strategy:**
  - If database connections fail or dependencies are missing, the exporter logs a timestamped warning in `output/workflow.log`.
  - Non-critical visual format failures fail gracefully without halting the remaining file exports.
  - Operations teams receive immediate failure alerts, prompting stakeholders to review the live dashboard directly.

---

## Technical Architecture & Code References

- **Core Export Functions:** [`export_functions.py`](file:///d:/Project/TraceOps/export_functions.py)
- **Streamlit Integration:** [`streamlit_export_integration.py`](file:///d:/Project/TraceOps/streamlit_export_integration.py)
- **Validation Suite:** `verify_exports(report_dir)`
