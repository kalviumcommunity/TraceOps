"""
TraceOps KPI Dashboard & Multi-Section Application
Real-Time KPI Dashboard Development (Assignment 2.55)
=========================================================
Features:
- Cached Data Loading (@st.cache_data decorator)
- Five Reactive Above-The-Fold KPI Metrics (Revenue, Avg Order, Records, Customers, Quality)
- Three Dynamic Interactive Chart Types (Line chart, Bar chart, Plotly histogram)
- Graceful Empty-State Guarding (st.warning & st.stop when 0 rows match filters)
- End-to-End Dynamic Dataset Support (CSV & JSON upload with automatic column standardization)
"""

import io
import os
import sys
import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from alert_config import ALERT_THRESHOLDS, check_alerts

# ── 1. Page Config - MUST be the very first Streamlit command ──────────────────
st.set_page_config(
    page_title="Real-Time KPI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. Dynamic Path Resolution for Backend ─────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_PATH = os.path.join(BASE_DIR, "Backend")
if not os.path.exists(BACKEND_PATH):
    BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "Backend"))

if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

try:
    from kpis.kpi_functions import (
        generate_transaction_data,
        load_data as backend_load_data,
        calculate_mau,
        calculate_churn_rate,
        calculate_payment_success_rate,
        RAW_DATA_PATH,
    )
    DATA_PATH = os.path.join(BACKEND_PATH, RAW_DATA_PATH)
except Exception:
    RAW_DATA_PATH = "data/raw/kpi_transactions.csv"
    DATA_PATH = os.path.join(BACKEND_PATH, RAW_DATA_PATH)
    
    def generate_transaction_data(filepath, n_samples=10000):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        np.random.seed(42)
        customer_ids = [f"CUST{i:04d}" for i in range(1, 5501)]
        segment_choices = ['Enterprise', 'SMB', 'Startup']
        segment_probs = [0.05, 0.40, 0.55]
        customer_type_map = {cid: np.random.choice(segment_choices, p=segment_probs) for cid in customer_ids}
        tx_ids = [f"TXN{i:06d}" for i in range(1, n_samples + 1)]
        
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=90)
        random_seconds = np.random.randint(0, int(90 * 86400), n_samples)
        tx_dates = [start_date + datetime.timedelta(seconds=int(s)) for s in random_seconds]
        
        c_ids = np.random.choice(customer_ids, n_samples)
        c_types = [customer_type_map[cid] for cid in c_ids]
        
        products = ['Starter', 'Pro', 'Enterprise', 'Add-on']
        prod_choices = np.random.choice(products, n_samples, p=[0.4, 0.35, 0.15, 0.1])
        amounts = np.random.exponential(150, n_samples) + 20
        statuses = np.random.choice(['Success', 'Failed', 'Refunded'], n_samples, p=[0.88, 0.08, 0.04])
        
        df = pd.DataFrame({
            'transaction_id': tx_ids,
            'customer_id': c_ids,
            'transaction_date': tx_dates,
            'amount': np.round(amounts, 2),
            'customer_type': c_types,
            'product': prod_choices,
            'payment_status': statuses
        })
        df.to_csv(filepath, index=False)
        return df

    def backend_load_data(filepath):
        df = pd.read_csv(filepath)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        return df

    def calculate_mau(df, days=30, reference_date=None):
        if len(df) == 0:
            return 0
        if reference_date is None:
            reference_date = df['transaction_date'].max()
        start_date = reference_date - pd.Timedelta(days=days)
        window = df[(df['transaction_date'] > start_date) & (df['transaction_date'] <= reference_date)]
        return window['customer_id'].nunique()

    def calculate_churn_rate(df, period_days=30, reference_date=None):
        if len(df) == 0:
            return 0.0
        if reference_date is None:
            reference_date = df['transaction_date'].max()
        p1_start = reference_date - pd.Timedelta(days=2*period_days)
        p1_end = reference_date - pd.Timedelta(days=period_days)
        p1_users = set(df[(df['transaction_date'] > p1_start) & (df['transaction_date'] <= p1_end)]['customer_id'])
        if not p1_users:
            return 0.0
        p2_users = set(df[(df['transaction_date'] > p1_end) & (df['transaction_date'] <= reference_date)]['customer_id'])
        retained = p1_users.intersection(p2_users)
        return 1.0 - (len(retained) / len(p1_users))

    def calculate_payment_success_rate(df):
        if len(df) == 0:
            return 0.0
        return (df['payment_status'] == 'Success').sum() / len(df)


# ── Custom Styling ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: linear-gradient(135deg, #020817 0%, #0f172a 60%, #1a0533 100%); }

#MainMenu, footer, header { visibility: hidden; }

[data-testid="metric-container"] {
    background: rgba(15,23,42,0.85);
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    transition: border-color .2s;
}
[data-testid="metric-container"]:hover { border-color: #3b82f6; }
[data-testid="stMetricLabel"]  { color: #94a3b8 !important; font-size: 0.85rem !important; font-weight: 600 !important; }
[data-testid="stMetricValue"]  { color: #f1f5f9 !important; font-size: 1.8rem !important; font-weight: 800 !important; }

[data-testid="stSidebar"] { background: #0f172a !important; border-right: 1px solid #1e293b; }
[data-testid="stSidebar"] label { color: #94a3b8 !important; }

hr { border-color: #1e293b !important; margin: 1.2rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Task 3: Apply @st.cache_data to Data Loading ──────────────────────────────
@st.cache_data
def load_data(file_bytes, file_name):
    """Load and return DataFrame. Cached by file content hash and filename."""
    if isinstance(file_bytes, bytes):
        buffer = io.BytesIO(file_bytes)
    else:
        buffer = file_bytes

    if file_name.endswith(".csv"):
        return pd.read_csv(buffer)
    elif file_name.endswith(".json"):
        return pd.read_json(buffer)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or JSON file.")


@st.cache_data(ttl=3600)
def get_dashboard_data():
    """Load default dataset from backend path or generate sample data."""
    if not os.path.exists(DATA_PATH):
        generate_transaction_data(DATA_PATH)
    return backend_load_data(DATA_PATH)


# ── Task 5: End-to-End Execution Without Hardcoded Data ─────────────────────────
def standardize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes dataset columns to ensure smooth end-to-end operation with any uploaded file."""
    df = df.copy()

    # Standardize date column
    if "transaction_date" in df.columns:
        df["date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    elif "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        date_candidates = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]
        if date_candidates:
            df["date"] = pd.to_datetime(df[date_candidates[0]], errors="coerce")
        else:
            df["date"] = pd.date_range(end=pd.Timestamp.today(), periods=len(df), freq="D")
        df["transaction_date"] = df["date"]

    # Fill NaT in date if any
    if df["date"].isnull().any():
        df["date"] = df["date"].fillna(pd.Timestamp.today())

    # Standardize revenue / amount column
    if "amount" in df.columns:
        df["revenue"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    elif "revenue" in df.columns:
        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0.0)
        df["amount"] = df["revenue"]
    else:
        num_cols = df.select_dtypes(include="number").columns
        if len(num_cols) > 0:
            df["revenue"] = pd.to_numeric(df[num_cols[0]], errors="coerce").fillna(0.0)
            df["amount"] = df["revenue"]
        else:
            df["revenue"] = 0.0
            df["amount"] = 0.0

    # Standardize segment / customer_type column
    if "customer_type" in df.columns:
        df["segment"] = df["customer_type"].astype(str)
    elif "segment" in df.columns:
        df["segment"] = df["segment"].astype(str)
        df["customer_type"] = df["segment"]
    else:
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        if len(cat_cols) > 0:
            df["segment"] = df[cat_cols[0]].astype(str)
            df["customer_type"] = df[cat_cols[0]].astype(str)
        else:
            df["segment"] = "General"
            df["customer_type"] = "General"

    # Standardize customer_id
    if "customer_id" not in df.columns:
        id_cols = [c for c in df.columns if "id" in c.lower() or "user" in c.lower() or "customer" in c.lower()]
        if id_cols:
            df["customer_id"] = df[id_cols[0]]
        else:
            df["customer_id"] = [f"CUST_{i+1:04d}" for i in range(len(df))]

    return df


# ── MAIN APPLICATION RUNNER ───────────────────────────────────────────────────
def main():
    # Sidebar File Upload & Dataset Selection
    st.sidebar.title("Data Source & Upload")
    uploaded_file_sidebar = st.sidebar.file_uploader(
        "Upload CSV or JSON",
        type=["csv", "json"],
        key="sidebar_file_uploader"
    )

    if uploaded_file_sidebar is not None:
        try:
            raw_data = load_data(uploaded_file_sidebar.getvalue(), uploaded_file_sidebar.name)
            df = standardize_df(raw_data)
            st.sidebar.success(f"Using uploaded dataset: {uploaded_file_sidebar.name}")
        except Exception as e:
            st.sidebar.error(f"Error loading file: {e}")
            raw_data = get_dashboard_data()
            df = standardize_df(raw_data)
    elif "uploaded_df" in st.session_state and st.session_state["uploaded_df"] is not None:
        df = standardize_df(st.session_state["uploaded_df"])
    else:
        raw_data = get_dashboard_data()
        df = standardize_df(raw_data)

    # Initialize Session State
    if "selected_segment" not in st.session_state:
        st.session_state["selected_segment"] = "All"
    if "workflow_step" not in st.session_state:
        st.session_state["workflow_step"] = 1
    if "analysis_result" not in st.session_state:
        st.session_state["analysis_result"] = None

    # Sidebar Navigation
    st.sidebar.divider()
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Overview & KPI Dashboard", "Workflow Analysis", "Trends", "Segments", "Data Explorer", "Data Upload"]
    )

    st.sidebar.divider()
    st.sidebar.header("Filters & Controls")

    # Widget 1: Date range picker
    date_min = df["date"].min().date() if pd.notnull(df["date"].min()) else datetime.date.today()
    date_max = df["date"].max().date() if pd.notnull(df["date"].max()) else datetime.date.today()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(date_min, date_max)
    )

    # Widget 2: Multi-select for segments
    all_segments = sorted(df["segment"].dropna().unique().tolist())
    selected_segments = st.sidebar.multiselect(
        "Segments", options=all_segments, default=all_segments
    )

    # Widget 3: Revenue slider
    min_dataset_rev = int(df["revenue"].min()) if len(df) > 0 else 0
    max_dataset_rev = int(df["revenue"].max()) if len(df) > 0 else 1000
    min_rev, max_rev = st.sidebar.slider(
        "Revenue Range",
        min_value=min_dataset_rev,
        max_value=max_dataset_rev,
        value=(min_dataset_rev, max_dataset_rev)
    )

    # Widget 4: Radio button for payment status filter
    statuses = ["All"] + sorted(df["payment_status"].dropna().unique().tolist()) if "payment_status" in df.columns else ["All"]
    payment_status_filter = st.sidebar.radio("Payment Status", options=statuses, index=0)

    # Reset Buttons
    col_reset1, col_reset2 = st.sidebar.columns(2)
    with col_reset1:
        if st.button("Reset Filters"):
            st.rerun()
    with col_reset2:
        if st.button("Reset Session"):
            for key in ["selected_segment", "workflow_step", "analysis_result", "uploaded_df"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # Wire Widgets into Filter Chain
    if isinstance(date_range, (list, tuple)):
        if len(date_range) == 2:
            start_d, end_d = date_range[0], date_range[1]
        elif len(date_range) == 1:
            start_d = end_d = date_range[0]
        else:
            start_d, end_d = date_min, date_max
    else:
        start_d = end_d = date_range

    start_ts = pd.Timestamp(start_d)
    end_ts = pd.Timestamp(end_d).replace(hour=23, minute=59, second=59, microsecond=999999)

    filtered_df = df[
        (df["date"] >= start_ts)
        & (df["date"] <= end_ts)
        & (df["segment"].isin(selected_segments))
        & (df["revenue"] >= min_rev)
        & (df["revenue"] <= max_rev)
    ]
    if payment_status_filter != "All" and "payment_status" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["payment_status"] == payment_status_filter]

    # ── Task 4: Handle Empty Filtered Results Gracefully ───────────────────────
    if len(filtered_df) == 0:
        st.warning("No data matches current filters. Broaden your selection.")
        st.stop()

    # ── OVERVIEW & LIVE KPI DASHBOARD PAGE ──
    if page == "Overview & KPI Dashboard":
        st.title("Real-Time Operational KPI Dashboard")
        st.write("Dynamic business analytics driven by `@st.cache_data` and filtered data.")

        # ── Threshold-Based Visual Alerts (Assignment 2.56) ──
        churn_val = calculate_churn_rate(filtered_df)
        churn_rate_pct = churn_val * 100.0 if churn_val <= 1.0 else churn_val
        avg_order_val = float(filtered_df["revenue"].mean()) if len(filtered_df) > 0 else 0.0

        total_cells = filtered_df.shape[0] * filtered_df.shape[1]
        null_count = filtered_df.isnull().sum().sum()
        null_pct_val = (null_count / total_cells * 100.0) if total_cells > 0 else 0.0

        current_metrics = {
            "churn_rate": churn_rate_pct,
            "avg_order_value": avg_order_val,
            "null_percentage": null_pct_val
        }

        alerts = check_alerts(current_metrics, ALERT_THRESHOLDS)

        if alerts:
            for alert in alerts:
                alert_text = (
                    "ALERT: " + str(alert["metric"])
                    + " is " + str(round(alert["value"], 1))
                    + " (threshold: " + str(alert["threshold"]) + "). "
                    + str(alert["message"])
                )
                if alert["severity"] == "critical":
                    st.error(alert_text)
                else:
                    st.warning(alert_text)

        # ── Task 1: Display Five Reactive KPI Metrics ──
        st.header("Key Performance Indicators")
        
        total_revenue = filtered_df["revenue"].sum()
        avg_order = filtered_df["revenue"].mean() if len(filtered_df) > 0 else 0.0
        row_count = len(filtered_df)
        unique_customers = filtered_df["customer_id"].nunique() if "customer_id" in filtered_df.columns else len(filtered_df)
        
        total_cells = filtered_df.shape[0] * filtered_df.shape[1]
        null_count = filtered_df.isnull().sum().sum()
        null_pct = (null_count / total_cells * 100) if total_cells > 0 else 0.0

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Revenue", f"${total_revenue:,.0f}")
        with col2:
            st.metric("Avg Order", f"${avg_order:,.0f}")
        with col3:
            st.metric("Records", f"{row_count:,}")
        with col4:
            st.metric("Customers", f"{unique_customers:,}")
        with col5:
            st.metric("Quality", f"{100 - null_pct:.1f}%")

        st.divider()

        # ── Task 2: Include Three Chart Types ──
        st.header("Interactive Analytics Visualizations")

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            # Chart 1: Line chart (trend)
            st.subheader("Revenue Over Time")
            trend = filtered_df.groupby("date")["revenue"].sum().reset_index()
            st.line_chart(trend.set_index("date"))

        with chart_col2:
            # Chart 2: Bar chart (comparison)
            st.subheader("Revenue by Segment")
            seg = filtered_df.groupby("segment")["revenue"].sum().reset_index()
            st.bar_chart(seg.set_index("segment"))

        st.divider()

        # Chart 3: Plotly histogram (distribution)
        st.subheader("Order Value Distribution")
        fig = px.histogram(
            filtered_df,
            x="revenue",
            nbins=30,
            title="Order Value Distribution",
            color_discrete_sequence=["#3b82f6"]
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter"),
            margin=dict(l=10, r=10, t=35, b=10),
            xaxis=dict(gridcolor="#1e293b", title="Revenue / Order Amount"),
            yaxis=dict(gridcolor="#1e293b", title="Count")
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Dashboard Performance & Caching Info"):
            st.write(
                "Data loading is optimized using `@st.cache_data`. "
                "All metric calculations and chart visualizations update in memory from `filtered_df`."
            )

    # ── WORKFLOW ANALYSIS PAGE ──
    elif page == "Workflow Analysis":
        st.title("Multi-Step Workflow Analysis")
        st.write("Demonstrating Streamlit session state persistence across widget interactions.")

        st.header("Step 1: Select Segment")
        segment_options = ["All"] + all_segments
        current_chosen = st.session_state.get("selected_segment", "All")
        default_index = segment_options.index(current_chosen) if current_chosen in segment_options else 0

        segment = st.selectbox(
            "Choose a segment",
            options=segment_options,
            index=default_index
        )

        if st.button("Confirm Segment"):
            st.session_state["selected_segment"] = segment
            st.session_state["workflow_step"] = 2

        if st.session_state["workflow_step"] >= 2:
            st.divider()
            st.header("Step 2: Segment Analysis")
            chosen = st.session_state["selected_segment"]
            st.write(f"Analysing segment: **{chosen}**")

            analysis_df = filtered_df if chosen == "All" else filtered_df[filtered_df["segment"] == chosen]

            result = float(analysis_df["revenue"].sum()) if len(analysis_df) > 0 else 0.0
            st.session_state["analysis_result"] = result

            wf_c1, wf_c2, wf_c3 = st.columns(3)
            with wf_c1:
                st.metric("Total Revenue", f"${result:,.0f}")
            with wf_c2:
                st.metric("Unique Customers", f"{analysis_df['customer_id'].nunique():,}")
            with wf_c3:
                st.metric("Record Count", f"{len(analysis_df):,}")

            with st.expander("View Filtered Segment Records"):
                st.dataframe(analysis_df.head(20), use_container_width=True)

    # ── TRENDS PAGE ──
    elif page == "Trends":
        st.title("Trend Analysis")

        st.header("Revenue & Activity Trends")
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.subheader("Revenue Trend")
            trend_df = filtered_df.groupby("date")["revenue"].sum().reset_index()
            st.line_chart(trend_df.set_index("date"))
        with t_col2:
            st.subheader("Customer Activity Trend")
            cust_df = filtered_df.groupby("date")["customer_id"].nunique().reset_index()
            st.line_chart(cust_df.set_index("date"))

    # ── SEGMENTS PAGE ──
    elif page == "Segments":
        st.title("Segment Breakdown")

        st.header("Segment Comparison")
        seg_df = filtered_df.groupby("segment")["revenue"].agg(["sum", "mean", "count"]).reset_index()
        seg_df.columns = ["Segment", "Total Revenue", "Average Order", "Transactions"]

        st.dataframe(seg_df, use_container_width=True)
        st.bar_chart(seg_df.set_index("Segment")["Total Revenue"])

    # ── DATA EXPLORER PAGE ──
    elif page == "Data Explorer":
        st.title("Data Explorer")
        st.write(f"Displaying **{len(filtered_df):,}** filtered records out of **{len(df):,}** total rows.")

        st.dataframe(filtered_df, use_container_width=True, height=350)

        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Filtered Data (CSV)",
            data=csv_data,
            file_name="filtered_dashboard_data.csv",
            mime="text/csv"
        )

    # ── DATA UPLOAD PAGE ──
    elif page == "Data Upload":
        st.title("Dataset Upload & Dynamic Integration System")

        st.write("Upload any CSV or JSON dataset to populate the dashboard dynamically.")
        file_uploaded = st.file_uploader("Upload dataset file", type=["csv", "json"], key="page_file_uploader")

        if file_uploaded is not None:
            try:
                # Task 3: Load using cached function load_data
                df_upload = load_data(file_uploaded.getvalue(), file_uploaded.name)
                st.session_state["uploaded_df"] = df_upload

                st.success(f"File uploaded successfully: **{file_uploaded.name}** ({len(df_upload):,} rows, {len(df_upload.columns)} columns)")

                st.subheader("Dataset Preview (First 10 Rows)")
                st.dataframe(df_upload.head(10), use_container_width=True)

                st.subheader("Column Summary")
                summary = pd.DataFrame({
                    "Column": df_upload.columns,
                    "Data Type": df_upload.dtypes.astype(str).values,
                    "Non-Null Count": df_upload.notnull().sum().values,
                    "Null Count": df_upload.isnull().sum().values
                })
                st.dataframe(summary, use_container_width=True)

            except Exception as e:
                st.error(f"Error processing file: {e}")
        else:
            st.info("Upload a CSV or JSON dataset above to view preview and statistics.")


if __name__ == "__main__":
    main()
