import streamlit as st
import pandas as pd
import numpy as np

# Page Configuration
st.set_page_config(
    page_title="Analytics Dashboard",
    layout="wide"
)

# Sidebar Navigation (Task 1)
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Overview", "Trends", "Data Explorer"]
)

# =============================================================================
# Section 1: Overview
# =============================================================================
if page == "Overview":
    # Visual Hierarchy: Page Title (Task 3)
    st.title("Business Overview")

    # Important Content Above the Fold: KPI Row using Columns (Task 2 & Task 5)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Revenue", "$5.2M", "+12.5%")
    with col2:
        st.metric("Users", "2,500", "+5.2%")
    with col3:
        st.metric("AOV", "$45", "+2.1%")
    with col4:
        st.metric("Churn", "5.2%", "-2.8%", delta_color="inverse")
    with col5:
        st.metric("NPS", "72", "+4")

    # Divider separating major sections (Task 3)
    st.divider()

    # Major Section Header (Task 3)
    st.header("Executive Summary")
    st.subheader("Performance Highlights & Strategic Metrics")

    # Columns for side-by-side executive insights (Task 2)
    exec_col1, exec_col2 = st.columns(2)
    with exec_col1:
        st.info("📈 **Growth Highlights:** Q3 revenue surpassed quarterly targets by 12.5%, driven primarily by enterprise expansion.")
    with exec_col2:
        st.success("🎯 **Retention Target:** Customer churn decreased by 2.8% following the implementation of proactive onboarding workflows.")

    # Progressive Disclosure Expander for Methodology (Task 2)
    with st.expander("About These Metrics"):
        st.write(
            "Revenue is calculated as the sum of all settled order amounts for the current month. "
            "Churn rate reflects the percentage of active customers who had no billing activity within 30 days. "
            "Average Order Value (AOV) is net revenue divided by completed orders."
        )

# =============================================================================
# Section 2: Trends
# =============================================================================
elif page == "Trends":
    # Visual Hierarchy: Page Title (Task 3)
    st.title("Trend Analysis")

    # Major Section 1: Revenue Trends (Task 3)
    st.header("Revenue Trends")
    st.subheader("Monthly Revenue & Growth Rate (Last 12 Months)")

    # Columns for side-by-side trend metrics (Task 2)
    trend_col1, trend_col2 = st.columns(2)
    with trend_col1:
        st.markdown("#### Monthly Revenue Progression ($M)")
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        revenue_values = [4.1, 4.2, 4.3, 4.5, 4.6, 4.8, 4.9, 5.0, 5.1, 5.2, 5.2, 5.2]
        revenue_df = pd.DataFrame({"Month": months, "Revenue ($M)": revenue_values})
        st.line_chart(revenue_df.set_index("Month"))
    with trend_col2:
        st.markdown("#### MoM Growth Rate (%)")
        growth_values = [2.1, 2.4, 2.3, 4.6, 2.2, 4.3, 2.0, 2.0, 2.0, 1.9, 0.0, 0.0]
        growth_df = pd.DataFrame({"Month": months, "Growth (%)": growth_values})
        st.bar_chart(growth_df.set_index("Month"))

    # Divider separating major sections (Task 3)
    st.divider()

    # Major Section 2: Customer Metrics (Task 3)
    st.header("Customer Metrics")
    st.subheader("Active Customers Over Time")

    cust_col1, cust_col2 = st.columns(2)
    with cust_col1:
        st.markdown("#### Active vs Churned Customer Count")
        cust_df = pd.DataFrame({
            "Month": months,
            "Active": [2100, 2150, 2200, 2280, 2320, 2380, 2410, 2450, 2480, 2500, 2510, 2520],
            "Churned": [120, 115, 110, 105, 98, 95, 90, 88, 85, 82, 80, 78]
        })
        st.line_chart(cust_df.set_index("Month"))
    with cust_col2:
        st.markdown("#### Summary Insight")
        st.write("Customer growth shows a steady upward trajectory with monthly active users increasing from 2,100 to 2,500 over the past 12 months.")

    # Progressive Disclosure Expander for Trend Details (Task 2)
    with st.expander("Trend Methodology & Notes"):
        st.write(
            "Monthly revenue figures are normalized to account for variable billing cycle lengths. "
            "Customer metrics track unique authenticated user IDs with at least one transaction event per calendar month."
        )

# =============================================================================
# Section 3: Data Explorer
# =============================================================================
elif page == "Data Explorer":
    # Visual Hierarchy: Page Title (Task 3)
    st.title("Data Explorer")

    # Major Section 1: Filters & Interactive Breakdown (Task 3)
    st.header("Data Filtering & Analysis")
    st.subheader("Filter & Aggregate Options")

    # Side-by-side columns for filter inputs (Task 2)
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        selected_segment = st.selectbox(
            "Customer Segment",
            ["All", "Enterprise", "Mid-Market", "SMB", "Starter"]
        )
    with filter_col2:
        selected_risk = st.multiselect(
            "Risk Level",
            ["Low", "Medium", "High"],
            default=["Low", "Medium", "High"]
        )

    # Divider separating major sections (Task 3)
    st.divider()

    # Major Section 2: Detailed Data Table (Task 3)
    st.header("Raw Dataset & Export")
    st.subheader("Filtered Customer Transaction Records")

    # Generate synthetic dataset for exploration
    np.random.seed(42)
    sample_df = pd.DataFrame({
        "Customer ID": [f"CUST-{1000 + i}" for i in range(20)],
        "Segment": np.random.choice(["Enterprise", "Mid-Market", "SMB", "Starter"], 20),
        "Revenue ($)": np.random.randint(500, 50000, 20),
        "Risk Level": np.random.choice(["Low", "Medium", "High"], 20)
    })

    # Apply filters
    filtered_df = sample_df.copy()
    if selected_segment != "All":
        filtered_df = filtered_df[filtered_df["Segment"] == selected_segment]
    if selected_risk:
        filtered_df = filtered_df[filtered_df["Risk Level"].isin(selected_risk)]

    # Display dataset summary in columns (Task 2)
    data_col1, data_col2 = st.columns([3, 1])
    with data_col1:
        st.dataframe(filtered_df, use_container_width=True)
    with data_col2:
        st.metric("Total Records", len(filtered_df))
        st.metric("Filtered Revenue", f"${filtered_df['Revenue ($)'].sum():,}")

    # Progressive Disclosure Expander for Raw Data & Download (Task 2)
    with st.expander("View Raw Data & Download CSV"):
        st.write("You can download the full dataset below for offline analysis.")
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="customer_data.csv",
            mime="text/csv"
        )
