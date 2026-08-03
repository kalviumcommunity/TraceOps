"""
Assignment 2.47 – KPI Card & Summary Metric Design
====================================================
Designs and displays a five-card KPI header that answers
"are we on track?" in five seconds.

Tasks covered
─────────────
Task 1 : Compute five KPI metrics with current vs prior period comparison
Task 2 : Trend indicators (↑ ↓ →) with correct directional logic
Task 3 : Percentage change formatted as (+/-X.X%)
Task 4 : Streamlit dashboard – five KPI cards at top, charts below
Task 5 : All values sourced from the validated clean data layer
         (kpis/kpi_functions.py) – no hardcoded numbers

Run standalone:   python kpi_dashboard.py
Run as dashboard: streamlit run kpi_dashboard.py
"""

from __future__ import annotations

import os
import sys
import logging
import numpy as np
import pandas as pd
from datetime import datetime

# ── path bootstrap so kpi_functions can be imported from any cwd ──────────────
sys.path.insert(0, os.path.dirname(__file__))
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

os.makedirs("output", exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1 – Compute five KPI metrics with period-over-period comparison
# ─────────────────────────────────────────────────────────────────────────────

def _window(df: pd.DataFrame, ref: pd.Timestamp, days: int) -> pd.DataFrame:
    """Slice *df* to the N-day window ending at *ref* (inclusive)."""
    start = ref - pd.Timedelta(days=days)
    return df[(df["transaction_date"] > start) & (df["transaction_date"] <= ref)]


def compute_revenue(df: pd.DataFrame, ref: pd.Timestamp, days: int = 30) -> float:
    """Total revenue of successful transactions in window."""
    window = _window(df, ref, days)
    return float(window[window["payment_status"] == "Success"]["amount"].sum())


def compute_active_users(df: pd.DataFrame, ref: pd.Timestamp, days: int = 30) -> int:
    """Unique customers with ≥1 successful transaction in window."""
    return calculate_mau(df, days=days, reference_date=ref)


def compute_aov(df: pd.DataFrame, ref: pd.Timestamp, days: int = 30) -> float:
    """Mean order amount of successful transactions in window."""
    window = _window(df, ref, days)
    success = window[window["payment_status"] == "Success"]["amount"]
    return float(success.mean()) if len(success) > 0 else 0.0


def compute_churn(df: pd.DataFrame, ref: pd.Timestamp, days: int = 30) -> float:
    """
    Churn rate: % of customers active in P1 who are absent in P2.
    P1 = [ref - 60d, ref - 30d)   P2 = [ref - 30d, ref]
    Returns value in PERCENT (e.g. 4.8 = 4.8%).
    """
    return calculate_churn_rate(df, period_days=days, reference_date=ref) * 100


def compute_satisfaction(df: pd.DataFrame, ref: pd.Timestamp, days: int = 30) -> float:
    """
    Proxy satisfaction score: Payment Success Rate scaled to a /5 rating.
    PSR of 1.0 → 5.0/5   PSR of 0.95 → 4.75/5
    Uses the existing payment_success_rate function.
    """
    window = _window(df, ref, days)
    if len(window) == 0:
        return 0.0
    success_rate = calculate_payment_success_rate(window)
    return round(success_rate * 5, 2)          # map [0,1] → [0,5]


def compute_all_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 1: Compute five KPIs for current period (latest 30 days)
    and prior period (30–60 days ago), then derive Change_Pct.

    Returns a DataFrame with columns:
        Metric, Current, Prior, Change_Pct, Current_Display, Prior_Display
    """
    ref        = df["transaction_date"].max()
    prior_ref  = ref - pd.Timedelta(days=30)   # anchor for prior window

    rows = []

    # ── 1. Total Revenue ──────────────────────────────────────────────────────
    curr_rev  = compute_revenue(df, ref,       days=30)
    prior_rev = compute_revenue(df, prior_ref, days=30)
    rows.append({
        "Metric":          "Revenue",
        "Current":         curr_rev,
        "Prior":           prior_rev,
        "Current_Display": f"${curr_rev / 1_000_000:.2f}M" if curr_rev >= 1_000_000
                           else f"${curr_rev:,.0f}",
        "Prior_Display":   f"${prior_rev / 1_000_000:.2f}M" if prior_rev >= 1_000_000
                           else f"${prior_rev:,.0f}",
    })

    # ── 2. Active Users ───────────────────────────────────────────────────────
    curr_users  = compute_active_users(df, ref,       days=30)
    prior_users = compute_active_users(df, prior_ref, days=30)
    rows.append({
        "Metric":          "Active Users",
        "Current":         curr_users,
        "Prior":           prior_users,
        "Current_Display": f"{curr_users:,}",
        "Prior_Display":   f"{prior_users:,}",
    })

    # ── 3. Average Order Value ────────────────────────────────────────────────
    curr_aov  = compute_aov(df, ref,       days=30)
    prior_aov = compute_aov(df, prior_ref, days=30)
    rows.append({
        "Metric":          "Avg Order Value",
        "Current":         curr_aov,
        "Prior":           prior_aov,
        "Current_Display": f"${curr_aov:,.2f}",
        "Prior_Display":   f"${prior_aov:,.2f}",
    })

    # ── 4. Churn Rate (inverted metric: lower is better) ──────────────────────
    curr_churn  = compute_churn(df, ref,       days=30)
    prior_churn = compute_churn(df, prior_ref, days=30)
    rows.append({
        "Metric":          "Churn Rate",
        "Current":         curr_churn,
        "Prior":           prior_churn,
        "Current_Display": f"{curr_churn:.1f}%",
        "Prior_Display":   f"{prior_churn:.1f}%",
    })

    # ── 5. Customer Satisfaction ──────────────────────────────────────────────
    curr_sat  = compute_satisfaction(df, ref,       days=30)
    prior_sat = compute_satisfaction(df, prior_ref, days=30)
    rows.append({
        "Metric":          "Satisfaction",
        "Current":         curr_sat,
        "Prior":           prior_sat,
        "Current_Display": f"{curr_sat:.2f}/5",
        "Prior_Display":   f"{prior_sat:.2f}/5",
    })

    kpis = pd.DataFrame(rows)

    # Percentage change: avoid division by zero
    kpis["Change_Pct"] = kpis.apply(
        lambda r: ((r["Current"] - r["Prior"]) / r["Prior"]) * 100
        if r["Prior"] != 0 else 0.0,
        axis=1,
    ).round(1)

    return kpis


# ─────────────────────────────────────────────────────────────────────────────
# TASK 2 – Trend indicators with correct directional logic
# ─────────────────────────────────────────────────────────────────────────────

INVERTED_METRICS = {"Churn Rate"}   # metrics where ↓ = good

def get_trend_indicator(change_pct: float, metric_name: str) -> tuple[str, str]:
    """
    Return (arrow, hex_colour) based on metric direction.

    Standard metrics (Revenue, Active Users, AOV, Satisfaction):
        > +2% → ↑ green    < -2% → ↓ red    else → → yellow

    Inverted metrics (Churn Rate):
        > +2% → ↑ red      < -2% → ↓ green  else → → yellow
    """
    THRESHOLD = 2.0  # % dead-band for "flat"

    if metric_name in INVERTED_METRICS:
        if change_pct < -THRESHOLD:
            return "↓", "#10b981"   # green – improvement
        elif change_pct > THRESHOLD:
            return "↑", "#ef4444"   # red   – deterioration
        else:
            return "→", "#f59e0b"   # yellow – flat
    else:
        if change_pct > THRESHOLD:
            return "↑", "#10b981"   # green
        elif change_pct < -THRESHOLD:
            return "↓", "#ef4444"   # red
        else:
            return "→", "#f59e0b"   # yellow


def add_trend_indicators(kpis: pd.DataFrame) -> pd.DataFrame:
    """Task 2: Apply get_trend_indicator to every row and store results."""
    indicators = kpis.apply(
        lambda r: get_trend_indicator(r["Change_Pct"], r["Metric"]), axis=1
    )
    kpis[["Trend_Arrow", "Trend_Color"]] = pd.DataFrame(
        indicators.tolist(), index=kpis.index
    )
    return kpis


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3 – Display percentage change formatted correctly
# ─────────────────────────────────────────────────────────────────────────────

def add_change_display(kpis: pd.DataFrame) -> pd.DataFrame:
    """Task 3: Format Change_Pct as '+12.5%' / '-2.8%' / '0.0%'."""
    kpis["Change_Display"] = kpis["Change_Pct"].apply(
        lambda x: f"{x:+.1f}%"
    )
    return kpis


# ─────────────────────────────────────────────────────────────────────────────
# TASK 4 – Streamlit dashboard layout (five KPI cards + trend charts)
# ─────────────────────────────────────────────────────────────────────────────

def run_streamlit_dashboard(kpis: pd.DataFrame, df: pd.DataFrame) -> None:
    """
    Task 4: Render the five KPI cards at the top, then charts below.
    Layout hierarchy:
        Level 1 (Top)    – five KPI metric cards
        Level 2 (Middle) – trend mini-charts
        Level 3 (Bottom) – segment breakdown table
    """
    try:
        import streamlit as st
        import plotly.graph_objects as go
    except ImportError:
        print("Streamlit/Plotly not installed. Run: pip install streamlit plotly")
        return

    # ── Page config ───────────────────────────────────────────────────────────
    st.set_page_config(
        page_title="KPI Dashboard – TraceOps",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Custom CSS: card styling, status badges
    st.markdown("""
    <style>
    [data-testid="metric-container"] {
        background: #1e293b;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        border: 1px solid #334155;
    }
    [data-testid="stMetricLabel"]  { color: #94a3b8 !important; font-size: 0.85rem; }
    [data-testid="stMetricValue"]  { color: #f1f5f9 !important; font-size: 1.6rem; font-weight: 700; }
    [data-testid="stMetricDelta"]  { font-size: 0.95rem !important; font-weight: 600; }
    .block-container { padding-top: 2rem; }
    h1 { color: #f1f5f9; }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    st.title("📊 Sales Performance KPI Dashboard")
    st.caption(
        f"Data sourced from `data/raw/kpi_transactions.csv` via `kpis/kpi_functions.py` · "
        f"Reference date: **{df['transaction_date'].max().strftime('%Y-%m-%d')}** · "
        f"Comparison window: 30-day rolling"
    )
    st.markdown("---")

    # ── Level 1: Five KPI Cards ───────────────────────────────────────────────
    st.subheader("📌 Level 1 — Business Status at a Glance")

    col1, col2, col3, col4, col5 = st.columns(5)
    columns = [col1, col2, col3, col4, col5]

    delta_color_map = {
        "Revenue":         "normal",
        "Active Users":    "normal",
        "Avg Order Value": "normal",
        "Churn Rate":      "inverse",   # ← negative delta should be green
        "Satisfaction":    "normal",
    }

    for col, (_, row) in zip(columns, kpis.iterrows()):
        with col:
            st.metric(
                label=row["Metric"],
                value=row["Current_Display"],
                delta=row["Change_Display"],
                delta_color=delta_color_map.get(row["Metric"], "normal"),
                help=f"Prior period: {row['Prior_Display']}",
            )

    st.markdown("---")

    # ── Status legend ─────────────────────────────────────────────────────────
    st.caption(
        "🟢 Green = on track (>2% change in good direction)  "
        "🔴 Red = off track (>2% change in bad direction)  "
        "🟡 Yellow = flat (within ±2%)"
    )

    # ── Level 2: Trend mini-charts ────────────────────────────────────────────
    st.subheader("📈 Level 2 — 30-Day Rolling Trends")

    ref      = df["transaction_date"].max()
    dates    = pd.date_range(end=ref, periods=30, freq="D")
    df_s     = df[df["payment_status"] == "Success"].copy()

    trend_col1, trend_col2 = st.columns(2)

    # Revenue trend
    with trend_col1:
        daily_rev = (
            df_s.set_index("transaction_date")
            .resample("D")["amount"].sum()
            .reindex(dates, fill_value=0)
        )
        fig_rev = go.Figure(go.Scatter(
            x=daily_rev.index, y=daily_rev.values,
            mode="lines", fill="tozeroy",
            line=dict(color="#3b82f6", width=2),
            fillcolor="rgba(59,130,246,0.10)",
            hovertemplate="<b>%{x|%d %b}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
        ))
        fig_rev.update_layout(
            title="Daily Revenue (last 30 days)",
            height=280, margin=dict(l=10, r=10, t=40, b=10),
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            yaxis=dict(tickprefix="$", gridcolor="#1e293b", color="#94a3b8"),
            xaxis=dict(gridcolor="#1e293b", color="#94a3b8"),
            font=dict(color="#94a3b8"),
        )
        st.plotly_chart(fig_rev, use_container_width=True)

    # Active users trend
    with trend_col2:
        daily_users = (
            df_s.set_index("transaction_date")
            .resample("D")["customer_id"].nunique()
            .reindex(dates, fill_value=0)
        )
        fig_usr = go.Figure(go.Scatter(
            x=daily_users.index, y=daily_users.values,
            mode="lines+markers",
            line=dict(color="#10b981", width=2),
            marker=dict(size=4, color="#10b981"),
            hovertemplate="<b>%{x|%d %b}</b><br>Active Users: %{y:,}<extra></extra>",
        ))
        fig_usr.update_layout(
            title="Daily Active Users (last 30 days)",
            height=280, margin=dict(l=10, r=10, t=40, b=10),
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            yaxis=dict(gridcolor="#1e293b", color="#94a3b8"),
            xaxis=dict(gridcolor="#1e293b", color="#94a3b8"),
            font=dict(color="#94a3b8"),
        )
        st.plotly_chart(fig_usr, use_container_width=True)

    st.markdown("---")

    # ── Level 3: KPI summary table ────────────────────────────────────────────
    st.subheader("🔍 Level 3 — KPI Summary Table")

    display_df = kpis[
        ["Metric", "Current_Display", "Prior_Display", "Change_Display", "Trend_Arrow"]
    ].rename(columns={
        "Current_Display": "Current (30d)",
        "Prior_Display":   "Prior (30–60d)",
        "Change_Display":  "Δ Change",
        "Trend_Arrow":     "Trend",
    })

    st.dataframe(display_df, hide_index=True, use_container_width=True)

    st.markdown("---")

    # ── Level 4: Segment breakdown ────────────────────────────────────────────
    st.subheader("📋 Level 4 — Revenue by Customer Segment")

    seg_rev = (
        df_s.groupby("customer_type")["amount"]
        .agg(Revenue="sum", Transactions="count", AvgOrder="mean")
        .reset_index()
        .rename(columns={"customer_type": "Segment"})
    )
    seg_rev["Revenue"] = seg_rev["Revenue"].map("${:,.2f}".format)
    seg_rev["AvgOrder"] = seg_rev["AvgOrder"].map("${:,.2f}".format)

    st.dataframe(seg_rev, hide_index=True, use_container_width=True)
    st.info(
        "💡 **Insight:** These values flow automatically from `kpi_transactions.csv`. "
        "Upload a new dataset and re-run — every KPI updates without touching this code."
    )


# ─────────────────────────────────────────────────────────────────────────────
# TASK 5 – Print data-lineage summary & validate values come from clean layer
# ─────────────────────────────────────────────────────────────────────────────

def print_kpi_report(kpis: pd.DataFrame) -> None:
    """
    Task 5: Print a compact KPI report to stdout, including data source
    references and validation cross-check notes.
    """
    header = (
        "\n"
        "╔══════════════════════════════════════════════════════════════════╗\n"
        "║          ASSIGNMENT 2.47 – KPI Card & Summary Metrics           ║\n"
        "╚══════════════════════════════════════════════════════════════════╝\n"
    )
    print(header)

    print(f"{'Metric':<18} {'Current':>12}  {'Prior':>12}  {'Change':>8}  {'Trend':>5}  Status")
    print("─" * 75)

    status_map = {"#10b981": "✅ On Track", "#ef4444": "❌ Alert", "#f59e0b": "⚠️  Flat"}

    for _, row in kpis.iterrows():
        status = status_map.get(row["Trend_Color"], "—")
        print(
            f"{row['Metric']:<18} {row['Current_Display']:>12}  "
            f"{row['Prior_Display']:>12}  {row['Change_Display']:>8}  "
            f"{row['Trend_Arrow']:>5}  {status}"
        )

    print("\n📁 Data lineage – all values sourced from:")
    print(f"   Source file   : {RAW_DATA_PATH}")
    print("   Compute layer : kpis/kpi_functions.py")
    print("   SQL view refs : database/views/vw_active_customers.sql")
    print("   Target ranges : kpis/kpi_validation_targets.json")
    print("\n✔  No hardcoded values – every KPI is computed from the clean data layer.")
    print("✔  Comparison period auto-calculated as 30-day rolling windows.")
    print("✔  See kpi_sources.md for full per-KPI lineage documentation.\n")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def build_kpis() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load data and return (kpis_df, raw_df)."""
    if not os.path.exists(RAW_DATA_PATH):
        generate_transaction_data(RAW_DATA_PATH)
    df   = load_data(RAW_DATA_PATH)
    kpis = compute_all_kpis(df)          # Task 1
    kpis = add_trend_indicators(kpis)    # Task 2
    kpis = add_change_display(kpis)      # Task 3
    return kpis, df


if __name__ == "__main__":
    kpis, df = build_kpis()

    # Detect Streamlit execution context
    if "streamlit" in sys.modules or any("streamlit" in a for a in sys.argv):
        run_streamlit_dashboard(kpis, df)    # Task 4
    else:
        print_kpi_report(kpis)               # Task 5 – standalone report


# ── Streamlit top-level call (needed when launched via `streamlit run`) ──────
try:
    import streamlit as _st_check          # noqa: F401
    _IS_STREAMLIT = True
except ImportError:
    _IS_STREAMLIT = False

if _IS_STREAMLIT and "streamlit" in sys.modules:
    _kpis, _df = build_kpis()
    run_streamlit_dashboard(_kpis, _df)
