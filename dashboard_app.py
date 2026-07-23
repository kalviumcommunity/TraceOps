import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime

# Page Configuration
st.set_page_config(
    page_title="Business Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header Section
st.title("Business Performance Dashboard")
st.markdown("### Executive Overview & Strategic Operational Metrics")
st.markdown("---")

# =============================================================================
# Level 1: Status (KPI Summary Cards)
# =============================================================================
st.subheader("Level 1: Status & Core KPIs")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="Revenue", value="$5.2M", delta="+12.5%")
with col2:
    st.metric(label="Active Customers", value="2,500", delta="+5.2%")
with col3:
    st.metric(label="Avg Order Value", value="$145", delta="+3.1%")
with col4:
    st.metric(label="Churn Rate", value="4.8%", delta="-1.2%", delta_color="inverse")
with col5:
    st.metric(label="NPS Score", value="72", delta="+4")

st.divider()

# =============================================================================
# Level 2: Trends (Time Series Metrics)
# =============================================================================
st.subheader("Level 2: Trends Over Time")

trend_col1, trend_col2 = st.columns(2)

with trend_col1:
    st.markdown("#### Monthly Revenue Trend (2024)")
    st.image("output/revenue_trend.png", caption="Revenue progression with target reference line ($5.0M)", use_container_width=True)

with trend_col2:
    st.markdown("#### Active vs. Churned Customers Trend")
    st.image("output/customer_metrics_trend.png", caption="Growth in active customers vs churn reduction following May retention campaign", use_container_width=True)

st.markdown("#### Average Order Value (AOV) Trend")
st.image("output/aov_trend.png", caption="Monthly AOV tracking against $140 target", use_container_width=True)

st.divider()

# =============================================================================
# Level 3: Segments (Distribution & Breakdown)
# =============================================================================
st.subheader("Level 3: Segment Breakdown")

seg_col1, seg_col2 = st.columns([3, 2])

with seg_col1:
    st.markdown("#### Revenue by Customer Segment")
    st.image("output/revenue_by_segment.png", caption="Breakdown of total revenue across Enterprise, Mid-Market, SMB, and Starter tiers", use_container_width=True)

with seg_col2:
    st.markdown("#### Segment Revenue Contribution Summary")
    segment_df = pd.DataFrame({
        'Segment': ['Enterprise', 'Mid-Market', 'SMB', 'Starter'],
        'Revenue ($M)': [2.1, 1.5, 1.0, 0.6],
        'Share (%)': ['40.4%', '28.8%', '19.2%', '11.5%'],
        'YoY Growth': ['+15.2%', '+10.4%', '+6.1%', '+2.3%']
    })
    st.dataframe(segment_df, hide_index=True, use_container_width=True)
    st.info("💡 **Insight:** Enterprise accounts drive 40.4% of total revenue and display the highest YoY growth rate (+15.2%).")

st.divider()

# =============================================================================
# Level 4: Progressive Disclosure (Detailed Data Explorer)
# =============================================================================
st.subheader("Level 4: Detailed Data Explorer")

# Generate synthetic detailed customer dataset for interactive exploration
np.random.seed(42)
n_records = 150
segments = ['Enterprise', 'Mid-Market', 'SMB', 'Starter']
risk_levels = ['Low', 'Medium', 'High']

dates = [datetime.date(2024, 1, 1) + datetime.timedelta(days=int(i)) for i in np.random.randint(0, 360, n_records)]
sample_data = pd.DataFrame({
    'customer_id': [f"CUST-{1000 + i}" for i in range(n_records)],
    'segment': np.random.choice(segments, n_records, p=[0.25, 0.30, 0.30, 0.15]),
    'revenue': np.round(np.random.uniform(500, 50000, n_records), 2),
    'last_activity': dates,
    'churn_risk': np.random.choice(risk_levels, n_records, p=[0.6, 0.25, 0.15])
})

# Sidebar Filters
st.sidebar.header("Filters")
selected_segment = st.sidebar.selectbox('Customer Segment', ['All', 'Enterprise', 'Mid-Market', 'SMB', 'Starter'])
start_date = datetime.date(2024, 1, 1)
end_date = datetime.date(2024, 12, 31)
date_range = st.sidebar.date_input('Date Range', value=(start_date, end_date))
selected_risk = st.sidebar.multiselect('Churn Risk Level', ['Low', 'Medium', 'High'], default=['Low', 'Medium', 'High'])

# Apply Sidebar Filters
filtered_df = sample_data.copy()

if selected_segment != 'All':
    filtered_df = filtered_df[filtered_df['segment'] == selected_segment]

if isinstance(date_range, tuple) and len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['last_activity'] >= date_range[0]) & 
        (filtered_df['last_activity'] <= date_range[1])
    ]

if selected_risk:
    filtered_df = filtered_df[filtered_df['churn_risk'].isin(selected_risk)]

# Display Filtered Data Summary & Table
st.write(f"Showing **{len(filtered_df):,}** records")
st.dataframe(filtered_df[['customer_id', 'segment', 'revenue', 'last_activity', 'churn_risk']], use_container_width=True)

# Export Functionality
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="Download CSV",
    data=csv,
    file_name="filtered_customer_data.csv",
    mime="text/csv"
)
