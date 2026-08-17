# TraceOps Sales Analytics & Operational KPI Dashboard

An interactive analytics dashboard and automated data pipeline that ingests sales transaction data, computes operational KPIs, monitors threshold breaches, detects churn risk, and delivers weekly executive reports via email. Built for operations, sales, and analytics teams to maintain full visibility over revenue performance, customer health, and data quality.

---

## 1. Project Overview & Dataset

### Overview
TraceOps provides an end-to-end analytics platform that bridges raw transaction logs and operational decision-making. The system ingests sales data from CSV/JSON uploads or automated background pipelines, applies strict cleaning and validation checks, computes high-level KPIs and derived metrics, and surfaces interactive visual charts with threshold-based alert warnings.

### Dataset Description
- **Data Source:** Raw CSV file upload via Streamlit UI or automated scheduled pipeline ingestion (`pipeline.py`).
- **Data Refresh Rate:** Weekly automated refresh via GitHub Actions workflow (`pipeline.yml`) or ad-hoc pipeline executions.
- **Core Raw Schema:**

| Column Name | Type | Description | Example |
|---|---|---|---|
| `customer_id` | string | Unique identifier assigned to each customer | `"CUST-1001"` |
| `order_id` / `transaction_id` | string | Unique transaction identifier | `"TXN000001"` |
| `amount` / `revenue` | float | Monetary transaction amount in USD | `149.99` |
| `date` / `transaction_date` | datetime | Date and timestamp of transaction | `"2026-08-17"` |
| `segment` / `customer_type` | string | Business segment classification (`Enterprise`, `SMB`, `Startup`) | `"Enterprise"` |
| `product` | string | Purchased product tier (`Starter`, `Pro`, `Enterprise`, `Add-on`) | `"Pro"` |
| `payment_status` | string | Status of payment processing (`Success`, `Failed`, `Refunded`) | `"Success"` |

---

## 2. Getting Started & Setup

Follow these numbered steps to go from `git clone` to running the interactive application.

### 1. Clone the repository
```bash
git clone https://github.com/kalviumcommunity/TraceOps.git
cd TraceOps
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment & run the application
```bash
cp .env.example .env
streamlit run app.py
```

> **Note on Email Delivery Configuration:**  
> Edit `.env` to supply SMTP credentials (`SENDER_EMAIL`, `SENDER_PASSWORD`, `SMTP_SERVER`, `SMTP_PORT`) if you intend to send automated email reports from the dashboard sidebar.

---

## 3. Pipeline Architecture

The pipeline processes raw incoming sales data through a modular six-stage architecture from ingestion to executive delivery.

### Data Flow Diagram

```
CSV Upload / Scheduled Ingest
         │
         ▼
    Ingestion: Load raw CSV/JSON data (`pipeline.py` / Streamlit file uploader)
         │
         ▼
    Cleaning & Validation: Drop null customer_ids & amounts, cast types, filter negative values (`validate_data.py`)
         │
         ▼
    Aggregation: Group by segment, compute total revenue, order count, and derived metrics
         │
         ▼
    Output: Write `cleaned.csv` and `aggregated.csv` to `output/` directory
         │
         ▼
    Dashboard: Load processed data (`@st.cache_data`), calculate live KPIs, render interactive charts (`app.py`)
         │
         ▼
    Alerts & Reports: Evaluate threshold breaches (`alert_config.py`), generate summary (`report_generator.py`), deliver email (`email_sender.py`)
```

### Pipeline Stage Details

1. **Ingestion Stage (`ingest` in `pipeline.py`):** Loads raw transaction CSV files from local paths or file upload buffers. Logs total record counts and schema properties.
2. **Cleaning & Validation Stage (`clean` & `validate_data.py`):** Filters out records missing required keys (`customer_id`, `amount`), converts `amount` to numeric, strips non-positive values, and enforces minimum dataset row thresholds.
3. **Aggregation Stage (`aggregate`):** Summarizes transactional metrics across business segments (`revenue` sum, `orders` count).
4. **Output Stage (`output`):** Persists sanitized datasets (`output/cleaned.csv` and `output/aggregated.csv`) for downstream consumption.
5. **Dashboard Layer (`app.py`):** Provides a multi-page Streamlit web app powered by `@st.cache_data` caching, sidebar filters (date range, segment multi-select, revenue slider, payment status), and responsive Plotly visual charts.
6. **Alerting & Delivery Layer (`alert_config.py`, `email_sender.py`):** Monitors live KPI metrics against static operational thresholds, displays visual error/warning banners in the dashboard, and delivers formatted text/HTML reports via SMTP.

---

## 4. Feature & Derived Metrics Documentation

### Derived & Engineered Features

| Derived Column | Type | Description | Example Value |
|---|---|---|---|
| `revenue_30d` | float | Sum of order amounts for a customer/segment within the trailing 30-day window | `4523.50` |
| `days_since_order` | integer | Days elapsed between reference date and customer's most recent order date | `12` |
| `churn_risk` | string | Risk classification (`"Low"`, `"Medium"`, `"High"`) based on activity gap & support tickets | `"high"` |
| `null_pct` | float | Percentage of missing/null values across all columns in the dataset | `2.3` |
| `segment_rank` | integer | Revenue rank of customer segment relative to total revenue contribution | `1` |
| `payment_success_rate` | float | Ratio of successful payment transactions to total attempted transactions | `0.88` |

### Core Dashboard KPIs

- **Total Revenue:** Sum of valid transaction amounts across active filtered selection (`$df['revenue'].sum()`).
- **Average Order Value (AOV):** Mean revenue per transaction (`$df['revenue'].mean()`).
- **Record Count:** Total count of transaction rows matching filter criteria.
- **Active Customers (MAU):** Distinct count of active `customer_id`s in trailing window.
- **Data Quality Score:** Overall cleanliness percentage calculated as `100 - null_percentage`.

### Dashboard Navigation Modules

- **Overview & KPI Dashboard:** High-level metrics, threshold alerts, line charts (Revenue Over Time), bar charts (Revenue by Segment), and Plotly order value distribution histograms.
- **Workflow Analysis:** Multi-step segment drill-down maintaining state across widget interactions via Streamlit `st.session_state`.
- **Trends:** Historical revenue trajectory and unique customer activity trendlines.
- **Segments:** Tabular breakdown of revenue, average order value, and volume by segment.
- **Data Explorer:** Tabular inspection of filtered records with one-click CSV export download.
- **Data Upload:** Dynamic CSV/JSON file uploader with automated schema standardization and data profiling.

---

## 5. Known Limitations & Assumptions

Transparency builds trust. The following known limitations, technical assumptions, and caveats apply to this data product:

1. **Weekly Data Refresh Staleness:** Data is refreshed on a weekly schedule via automated GitHub Actions pipelines. The dashboard does **not** reflect real-time streaming data. Maximum data staleness is **7 days**.
2. **Gross Revenue Focus (Refund Handling):** Revenue metrics represent gross order revenue. While payment statuses (`Refunded`, `Failed`) can be filtered, net revenue after refunds is not automatically deducted from total revenue metrics unless explicitly filtered.
3. **Static Segment Categorization:** Segment classification is based on customer attributes present at the time of ingestion. Customers who transition between segments mid-year are categorized under their most recent segment entry.
4. **Static Alert Thresholds:** Alert monitoring rules in `alert_config.py` use static thresholds (e.g. Churn Rate > 7.0%, AOV < $30.00). Thresholds do not dynamically adjust for seasonal fluctuations or historical variance.
5. **SMTP Configuration Dependency:** Email report delivery requires valid SMTP server credentials configured in `.env`. If credentials are omitted or invalid, email functionality logs a warning and gracefully disables sending without crashing the dashboard.
6. **Schema Formatting Assumptions:** Data validation routines in `validate_data.py` and `pipeline.py` expect CSV inputs with core columns (`customer_id`, `order_id`, `amount`, `date`, `segment`). Uploaded datasets with alternative headers are standardized using standard fallback mapping in `app.py`.
