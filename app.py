"""
TraceOps KPI Dashboard & Multi-Section Application
Streamlit App Structure & Navigation (Assignment 2.51)
=========================================================
Features:
- Sidebar Navigation (Overview, Trends, Segments, Data Explorer)
- Layout Components (st.columns & st.expander in every section)
- Visual Hierarchy (st.title, st.header, st.subheader, st.divider)
- Clean execution environment & dynamic path handling
- Above-the-fold KPI card presentation
"""

import os
import sys
import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

# ── 1. Page Config - MUST be the very first Streamlit command ──────────────────
st.set_page_config(
    page_title="Analytics Dashboard",
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
        load_data,
        calculate_mau,
        calculate_revenue_per_customer,
        calculate_churn_rate,
        calculate_payment_success_rate,
        calculate_customer_acquisition_cost,
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

    def load_data(filepath):
        df = pd.read_csv(filepath)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        return df

    def calculate_mau(df, days=30, reference_date=None):
        if reference_date is None:
            reference_date = df['transaction_date'].max()
        start_date = reference_date - pd.Timedelta(days=days)
        window = df[(df['transaction_date'] > start_date) & (df['transaction_date'] <= reference_date)]
        return window['customer_id'].nunique()

    def calculate_churn_rate(df, period_days=30, reference_date=None):
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


# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Background & Styling */
.stApp { background: linear-gradient(135deg, #020817 0%, #0f172a 60%, #1a0533 100%); }

/* Hide Streamlit default branding */
#MainMenu, footer, header { visibility: hidden; }

/* Metric Cards */
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
[data-testid="stMetricLabel"]  { color: #94a3b8 !important; font-size: 0.8rem !important; font-weight: 600 !important; }
[data-testid="stMetricValue"]  { color: #f1f5f9 !important; font-size: 1.8rem !important; font-weight: 800 !important; }

/* Sidebar styling */
[data-testid="stSidebar"] { background: #0f172a !important; border-right: 1px solid #1e293b; }
[data-testid="stSidebar"] label { color: #94a3b8 !important; }

/* Divider styling */
hr { border-color: #1e293b !important; margin: 1.2rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Cached Data Loader ────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_dashboard_data():
    if not os.path.exists(DATA_PATH):
        generate_transaction_data(DATA_PATH)
    return load_data(DATA_PATH)


# Helper functions
def get_window(df: pd.DataFrame, ref: pd.Timestamp, days: int) -> pd.DataFrame:
    start = ref - pd.Timedelta(days=days)
    return df[(df["transaction_date"] > start) & (df["transaction_date"] <= ref)]

def calculate_pct_change(curr, prior):
    if not prior or prior == 0:
        return 0.0
    return ((curr - prior) / abs(prior)) * 100

def get_kpis(df: pd.DataFrame, ref: pd.Timestamp):
    prior_ref = ref - pd.Timedelta(days=30)
    
    def calc_rev(r):
        w = get_window(df, r, 30)
        return float(w[w["payment_status"] == "Success"]["amount"].sum())
    
    def calc_users(r):
        return calculate_mau(df, days=30, reference_date=r)
    
    def calc_aov(r):
        w = get_window(df, r, 30)
        s = w[w["payment_status"] == "Success"]["amount"]
        return float(s.mean()) if len(s) > 0 else 0.0
    
    def calc_churn(r):
        return calculate_churn_rate(df, period_days=30, reference_date=r) * 100
    
    def calc_satisfaction(r):
        w = get_window(df, r, 30)
        psr = calculate_payment_success_rate(w) if len(w) > 0 else 0.0
        return round(psr * 5, 2)

    curr = {
        "revenue": calc_rev(ref),
        "users": calc_users(ref),
        "aov": calc_aov(ref),
        "churn": calc_churn(ref),
        "satisfaction": calc_satisfaction(ref)
    }
    prior = {
        "revenue": calc_rev(prior_ref),
        "users": calc_users(prior_ref),
        "aov": calc_aov(prior_ref),
        "churn": calc_churn(prior_ref),
        "satisfaction": calc_satisfaction(prior_ref)
    }
    return curr, prior


# Plotly plot configurations
PLOTLY_THEME = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter"),
    margin=dict(l=10, r=10, t=35, b=10),
    hovermode="x unified",
    xaxis=dict(gridcolor="#1e293b", linecolor="#1e293b"),
    yaxis=dict(gridcolor="#1e293b", linecolor="rgba(0,0,0,0)"),
)

def create_revenue_chart(df: pd.DataFrame, ref: pd.Timestamp):
    dates = pd.date_range(end=ref, periods=30, freq="D")
    daily = (
        df[df["payment_status"] == "Success"]
        .set_index("transaction_date")
        .resample("D")["amount"].sum()
        .reindex(dates, fill_value=0)
    )
    fig = go.Figure([
        go.Scatter(
            x=daily.index, y=daily.values,
            mode="lines", fill="tozeroy",
            line=dict(color="#3b82f6", width=2.5),
            fillcolor="rgba(59,130,246,0.10)",
            name="Revenue",
            hovertemplate="<b>%{x|%d %b}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
        )
    ])
    fig.update_layout(
        title=dict(text="Daily Revenue (30-Day Trend)", font=dict(size=14, color="#f1f5f9")),
        height=280,
        yaxis=dict(tickprefix="$", tickformat=",.0f", gridcolor="#1e293b"),
        **{k: v for k, v in PLOTLY_THEME.items() if k not in ("yaxis",)}
    )
    return fig

def create_users_chart(df: pd.DataFrame, ref: pd.Timestamp):
    dates = pd.date_range(end=ref, periods=30, freq="D")
    daily = (
        df[df["payment_status"] == "Success"]
        .set_index("transaction_date")
        .resample("D")["customer_id"].nunique()
        .reindex(dates, fill_value=0)
    )
    fig = go.Figure([
        go.Scatter(
            x=daily.index, y=daily.values,
            mode="lines+markers",
            line=dict(color="#10b981", width=2),
            marker=dict(size=3, color="#10b981"),
            name="Active Users",
            hovertemplate="<b>%{x|%d %b}</b><br>Users: %{y:,}<extra></extra>",
        )
    ])
    fig.update_layout(
        title=dict(text="Daily Active Users (30-Day Trend)", font=dict(size=14, color="#f1f5f9")),
        height=280, **PLOTLY_THEME
    )
    return fig

def create_segment_chart(df: pd.DataFrame, ref: pd.Timestamp):
    w = get_window(df, ref, 30)
    seg = (
        w[w["payment_status"] == "Success"]
        .groupby("customer_type")["amount"].sum()
        .reset_index()
        .rename(columns={"customer_type": "Segment", "amount": "Revenue"})
        .sort_values("Revenue", ascending=False)
    )
    colors = {"Enterprise": "#3b82f6", "SMB": "#10b981", "Startup": "#8b5cf6"}
    fig = go.Figure([
        go.Bar(
            x=seg["Segment"], y=seg["Revenue"],
            marker=dict(color=[colors.get(s, "#64748b") for s in seg["Segment"]]),
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
        )
    ])
    fig.update_layout(
        title=dict(text="Revenue by Customer Segment", font=dict(size=14, color="#f1f5f9")),
        height=280,
        yaxis=dict(tickprefix="$", gridcolor="#1e293b"),
        bargap=0.3,
        **{k: v for k, v in PLOTLY_THEME.items() if k not in ("yaxis",)}
    )
    return fig

def create_product_chart(df: pd.DataFrame, ref: pd.Timestamp):
    w = get_window(df, ref, 30)
    prod = (
        w[w["payment_status"] == "Success"]
        .groupby("product")["amount"].sum()
        .reset_index()
    )
    colors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b"]
    fig = go.Figure([
        go.Pie(
            labels=prod["product"],
            values=prod["amount"],
            hole=0.55,
            marker=dict(colors=colors[:len(prod)], line=dict(color="#0f172a", width=2)),
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f} (%{percent})<extra></extra>",
        )
    ])
    fig.update_layout(
        title=dict(text="Product Revenue Mix", font=dict(size=14, color="#f1f5f9")),
        height=280,
        legend=dict(font=dict(color="#94a3b8"), bgcolor="rgba(0,0,0,0)"),
        **{k: v for k, v in PLOTLY_THEME.items() if k not in ("xaxis", "yaxis", "hovermode", "legend")}
    )
    return fig


# ── MAIN APPLICATION RUNNER ───────────────────────────────────────────────────
def main():
    df = get_dashboard_data()

    # ── Task 1: Sidebar Navigation ──
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Overview", "Trends", "Segments", "Data Explorer", "Data Upload"]
    )

    st.sidebar.divider()
    st.sidebar.header("Global Filters")
    
    ref_default = df["transaction_date"].max().date()
    ref_date = st.sidebar.date_input(
        "Reference Date",
        value=ref_default,
        min_value=df["transaction_date"].min().date(),
        max_value=ref_default,
        help="KPI calculations use a 30-day window ending on this date."
    )
    
    segments = ["All"] + sorted(df["customer_type"].unique().tolist())
    seg_filter = st.sidebar.selectbox("Filter Segment", segments)

    ref = pd.Timestamp(ref_date)
    filtered_df = df.copy()
    if seg_filter != "All":
        filtered_df = filtered_df[filtered_df["customer_type"] == seg_filter]

    curr, prior = get_kpis(filtered_df, ref)

    # ── Task 1, 2, 3, 5: OVERVIEW PAGE ──
    if page == "Overview":
        # Task 3: Title (once per page)
        st.title("Business Overview")

        # Task 5: Primary content (KPI cards) loaded ABOVE THE FOLD at the top
        st.header("Key Performance Indicators")
        st.subheader("30-Day Rolling Business Metrics")

        # Task 2: st.columns for KPI cards side-by-side
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Revenue", f"${curr['revenue']/1e6:.2f}M", f"{calculate_pct_change(curr['revenue'], prior['revenue']):+.1f}%")
        with col2:
            st.metric("Active Users", f"{curr['users']:,}", f"{calculate_pct_change(curr['users'], prior['users']):+.1f}%")
        with col3:
            st.metric("Avg Order Value", f"${curr['aov']:,.2f}", f"{calculate_pct_change(curr['aov'], prior['aov']):+.1f}%")
        with col4:
            st.metric("Churn Rate", f"{curr['churn']:.1f}%", f"{calculate_pct_change(curr['churn'], prior['churn']):+.1f}%", delta_color="inverse")
        with col5:
            st.metric("Satisfaction", f"{curr['satisfaction']:.2f}/5", f"{calculate_pct_change(curr['satisfaction'], prior['satisfaction']):+.1f}%")

        # Task 2: st.expander for progressive disclosure & methodology
        with st.expander("About These Metrics"):
            st.write(
                "Revenue is calculated as the sum of all successful transaction amounts for the current 30-day window. "
                "Active Users (MAU) represents the count of unique customers with transactions within 30 days. "
                "Avg Order Value (AOV) is the mean transaction amount. "
                "Churn Rate represents customers who made a purchase in the prior period but had no activity in the current period."
            )

        st.divider()

        st.header("Executive Summary")
        st.subheader("Performance Highlights")
        summary_c1, summary_c2 = st.columns(2)
        with summary_c1:
            st.info(f"**Current Segment Filter**: {seg_filter} | **Reference Date**: {ref.strftime('%Y-%m-%d')}")
        with summary_c2:
            st.success(f"Total revenue generated in this 30-day window is **${curr['revenue']:,.2f}** across **{curr['users']:,}** active users.")

        with st.expander("View Methodology Notes"):
            st.markdown("""
            - **Data Layer**: Backend module `Backend/kpis/kpi_functions.py`
            - **Comparison Window**: Current 30-day period vs prior 30-day period
            - **Delta Calculations**: Inverse delta color used for Churn Rate where a negative change indicates improvement.
            """)

    # ── Task 1, 2, 3: TRENDS PAGE ──
    elif page == "Trends":
        st.title("Trend Analysis")

        st.header("Revenue Trends")
        st.subheader("Monthly Revenue (Last 30 Days)")
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_revenue_chart(filtered_df, ref), use_container_width=True)
        with col2:
            st.plotly_chart(create_users_chart(filtered_df, ref), use_container_width=True)

        with st.expander("Trend Analysis Insights & Methodology"):
            st.write(
                "Time-series charts track daily performance over the 30 days leading up to the selected reference date. "
                "The left chart highlights total daily dollar revenue, while the right chart tracks unique daily active users."
            )

        st.divider()

        st.header("Customer Metrics")
        st.subheader("Active Customers Over Time")
        
        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            st.metric("Peak Daily Revenue", f"${filtered_df[filtered_df['payment_status']=='Success']['amount'].max():,.2f}")
        with meta_col2:
            st.metric("Total Successful Transactions", f"{len(filtered_df[filtered_df['payment_status']=='Success']):,}")

        with st.expander("View Extended Trend Data Notes"):
            st.write("Calculations are filtered dynamically according to the sidebar segment and date controls.")

    # ── Task 1, 2, 3: SEGMENTS PAGE ──
    elif page == "Segments":
        st.title("Segment Breakdown")

        st.header("Customer & Product Distribution")
        st.subheader("Revenue by Segment and Product Mix")

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_segment_chart(filtered_df, ref), use_container_width=True)
        with col2:
            st.plotly_chart(create_product_chart(filtered_df, ref), use_container_width=True)

        with st.expander("Segment & Product Classification Notes"):
            st.write(
                "Customer segments are categorized into Enterprise, SMB, and Startup tiers. "
                "Product revenue mix displays distribution across Starter, Pro, Enterprise, and Add-on packages."
            )

        st.divider()

        st.header("Segment Performance Breakdown")
        st.subheader("Revenue Share Analysis")
        
        sub_c1, sub_c2, sub_c3 = st.columns(3)
        w30 = get_window(filtered_df, ref, 30)
        success_w30 = w30[w30["payment_status"] == "Success"]
        
        for idx, (seg_name, seg_group) in enumerate(success_w30.groupby("customer_type")):
            target_col = [sub_c1, sub_c2, sub_c3][idx % 3]
            with target_col:
                st.metric(f"{seg_name} Revenue", f"${seg_group['amount'].sum():,.2f}", f"{len(seg_group):,} orders")

        with st.expander("View Breakdown Methodology"):
            st.write("Segment totals are aggregated over successful transactions within the selected 30-day window.")

    # ── Task 1, 2, 3: DATA EXPLORER PAGE ──
    elif page == "Data Explorer":
        st.title("Data Explorer")

        st.header("Transaction Dataset & Export")
        st.subheader("Filtered Transactions Overview")

        w30 = get_window(filtered_df, ref, 30)
        
        stat1, stat2, stat3 = st.columns(3)
        with stat1:
            st.metric("Window Transactions", f"{len(w30):,}")
        with stat2:
            st.metric("Total Window Value", f"${w30[w30['payment_status']=='Success']['amount'].sum():,.2f}")
        with stat3:
            st.metric("Success Rate", f"{calculate_payment_success_rate(w30)*100:.1f}%")

        with st.expander("Dataset Summary Notes"):
            st.write(f"Displaying raw transaction data ending on {ref.strftime('%Y-%m-%d')} with customer segment filter '{seg_filter}'.")

        st.divider()

        st.header("Data Table & Download")
        st.subheader("Raw Transaction Records")

        st.dataframe(
            w30[["transaction_id", "customer_id", "transaction_date", "amount", "customer_type", "product", "payment_status"]]
            .sort_values("transaction_date", ascending=False)
            .reset_index(drop=True),
            use_container_width=True,
            height=320
        )

        with st.expander("Raw Transaction Data Explorer & Export Options"):
            csv_data = w30.to_csv(index=False)
            st.download_button(
                label="Download Filtered CSV Data",
                data=csv_data,
                file_name=f"traceops_transactions_{ref.strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            st.write("Click above to download the currently displayed dataset in standard CSV format.")

    # ── Task 1, 2, 3, 4, 5: DATA UPLOAD PAGE ──
    elif page == "Data Upload":
        st.title("Dataset Upload & Dynamic Preview System")

        st.header("Upload Custom Dataset")
        st.subheader("Accepts CSV and JSON formats")

        # Task 1 & Task 4: File Uploader widget & Error Handling
        uploaded_file = st.file_uploader("Upload your dataset", type=["csv", "json"])

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_upload = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith(".json"):
                    df_upload = pd.read_json(uploaded_file)
                else:
                    st.error("Unsupported file type. Please upload CSV or JSON.")
                    st.stop()

                if len(df_upload) == 0:
                    st.warning("Uploaded file is empty. Please check your data.")
                    st.stop()

                st.success(
                    "File loaded: "
                    + uploaded_file.name
                    + " ("
                    + str(len(df_upload))
                    + " rows, "
                    + str(len(df_upload.columns))
                    + " columns)"
                )
                st.session_state["uploaded_df"] = df_upload

            except Exception as e:
                st.error("Could not read this file. Please check the format and try again.")
                st.stop()

            # Task 2: Automatic Preview and Column Summary
            st.header("Dataset Preview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", f"{len(df_upload):,}")
            with col2:
                st.metric("Columns", str(len(df_upload.columns)))
            with col3:
                total_nulls = df_upload.isnull().sum().sum()
                total_cells = df_upload.shape[0] * df_upload.shape[1]
                null_pct = (total_nulls / total_cells) * 100 if total_cells > 0 else 0.0
                st.metric("Null %", f"{null_pct:.1f}%")

            st.divider()

            # First 10 rows
            st.subheader("First 10 Rows")
            st.dataframe(df_upload.head(10), use_container_width=True)

            # Column summary
            st.subheader("Column Summary")
            summary = pd.DataFrame({
                "Column": df_upload.columns,
                "Type": df_upload.dtypes.astype(str).values,
                "Non-Null": df_upload.notnull().sum().values,
                "Null Count": df_upload.isnull().sum().values,
                "Null %": (df_upload.isnull().sum() / len(df_upload) * 100).round(1).values
            })
            st.dataframe(summary, use_container_width=True)

            # Task 3: Basic Descriptive Statistics
            st.subheader("Descriptive Statistics")
            st.dataframe(df_upload.describe(), use_container_width=True)

            # Task 5: Ensure Data Is Usable Downstream (Quick Exploration)
            st.subheader("Quick Exploration")
            numeric_cols = df_upload.select_dtypes(include="number").columns.tolist()
            if numeric_cols:
                selected_col = st.selectbox("Select a column to visualise", numeric_cols)
                st.bar_chart(df_upload[selected_col].value_counts().head(20))

        else:
            st.info("Upload a CSV or JSON file to begin.")


if __name__ == "__main__":
    main()

