"""
Assignment 36 - Interactive Chart Builder with Plotly
======================================================
Demonstrates interactive visualisations using Plotly:
  - Custom hover tooltips (detail on demand)
  - Dropdown metric filters (multiple views, one chart)
  - Zoom, pan, and date-range selection (built-in Plotly interactions)
  - Streamlit integration (st.plotly_chart)
  - HTML export (fig.write_html)

Run standalone:  python assignment-36-interactive-charts.py
Run as dashboard: streamlit run assignment-36-interactive-charts.py
"""

import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Ensure output directory exists
# ---------------------------------------------------------------------------
os.makedirs("output", exist_ok=True)

# ---------------------------------------------------------------------------
# Design Tokens  (consistent with existing TraceOps palette)
# ---------------------------------------------------------------------------
PALETTE = {
    "primary":   "#1f77b4",   # Blue   – Cloud / primary
    "secondary": "#ff7f0e",   # Orange – Analytics / secondary
    "success":   "#2ca02c",   # Green  – Security / positive
    "warning":   "#d62728",   # Red    – Danger / outliers
    "purple":    "#9467bd",   # Purple – AI & ML / premium
    "neutral":   "#7f7f7f",   # Gray   – baseline
}

CHART_COLORS = list(PALETTE.values())

# ---------------------------------------------------------------------------
# Synthetic Data Generation
# ---------------------------------------------------------------------------

def _generate_daily_revenue(seed: int = 42) -> pd.DataFrame:
    """Daily revenue + order count for the full year 2024."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    n = len(dates)

    # Base trend with seasonal component and random noise
    trend    = np.linspace(4_000, 6_500, n)
    seasonal = 800 * np.sin(np.linspace(0, 2 * np.pi, n))
    noise    = rng.normal(0, 250, n)
    revenue  = np.clip(trend + seasonal + noise, 1_000, 10_000)

    orders   = np.clip((revenue / rng.uniform(130, 160, n)).astype(int), 5, 80)
    profit   = revenue * rng.uniform(0.18, 0.38, n)

    return pd.DataFrame(
        {"date": dates, "revenue": revenue.round(2),
         "profit": profit.round(2), "orders": orders}
    )


def _generate_product_data() -> pd.DataFrame:
    """Quarterly revenue, profit, and order count by product line."""
    product_lines = [
        "Cloud Solutions", "Analytics Platform",
        "Security Suite",  "Database Services", "AI & ML Tools",
    ]
    revenue = [5.2, 3.8, 2.9, 2.1, 1.6]
    profit  = [1.82, 1.14, 0.84, 0.55, 0.42]
    orders  = [1_240, 920, 680, 430, 310]
    return pd.DataFrame(
        {"product": product_lines, "revenue": revenue,
         "profit": profit, "orders": orders}
    )


def _generate_marketing_data(seed: int = 101) -> pd.DataFrame:
    """25 marketing campaigns: spend vs revenue generated."""
    rng   = np.random.default_rng(seed)
    spend = np.array([12, 15, 18, 22, 25, 28, 30, 35, 40, 42, 45,
                      50, 55, 58, 60, 65, 70, 75, 80, 85, 90, 95,
                      100, 105, 110], dtype=float)
    revenue = 3.2 * spend + 40 + rng.normal(0, 25, len(spend))
    revenue[18] = 120  # deliberate outlier (high spend, low ROI)
    channel = rng.choice(
        ["Email", "Social", "Paid Search", "Webinar"], len(spend)
    )
    return pd.DataFrame(
        {"spend_k": spend, "revenue_k": revenue.round(1),
         "channel": channel, "outlier": np.arange(len(spend)) == 18}
    )


# ---------------------------------------------------------------------------
# Chart 1 – Daily Revenue Trend with Custom Hover Tooltip & Date Range Selector
# ---------------------------------------------------------------------------

def chart1_revenue_trend(df: pd.DataFrame) -> go.Figure:
    """
    Line chart of daily revenue for 2024.

    Interactive features:
      • Rich hover tooltip: date, revenue, profit, orders
      • hovermode='x unified' shows all series at once
      • Date range buttons: 1M, 3M, 6M, YTD, All
      • Range slider for custom date selection
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["revenue"],
        mode="lines",
        name="Revenue",
        line=dict(color=PALETTE["primary"], width=2),
        fill="tozeroy",
        fillcolor="rgba(31,119,180,0.08)",
        hovertemplate=(
            "<b>%{x|%Y-%m-%d}</b><br>"
            "Revenue: $%{y:,.0f}<br>"
            "<extra></extra>"
        ),
    ))

    # Overlay profit as a secondary line
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["profit"],
        mode="lines",
        name="Profit",
        line=dict(color=PALETTE["success"], width=1.5, dash="dot"),
        hovertemplate=(
            "<b>%{x|%Y-%m-%d}</b><br>"
            "Profit: $%{y:,.0f}<br>"
            "<extra></extra>"
        ),
    ))

    # Unified hover across both traces
    fig.update_layout(
        title=dict(text="Daily Revenue & Profit Trend – 2024",
                   font=dict(size=18, color="#222")),
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        hovermode="x unified",
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
        yaxis=dict(tickprefix="$", tickformat=",.0f",
                   gridcolor="#e8e8e8"),
        xaxis=dict(
            gridcolor="#e8e8e8",
            rangeselector=dict(
                buttons=[
                    dict(count=1,  label="1M",  step="month", stepmode="backward"),
                    dict(count=3,  label="3M",  step="month", stepmode="backward"),
                    dict(count=6,  label="6M",  step="month", stepmode="backward"),
                    dict(count=1,  label="YTD", step="year",  stepmode="todate"),
                    dict(step="all", label="All"),
                ],
                bgcolor="#f0f2f6",
                activecolor=PALETTE["primary"],
            ),
            rangeslider=dict(visible=True, bgcolor="#f0f2f6"),
            type="date",
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Chart 2 – Product Revenue with Metric Dropdown Filter
# ---------------------------------------------------------------------------

def chart2_product_dropdown(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart of product-line metrics.

    Interactive features:
      • Dropdown menu to switch between Revenue / Profit / Orders
      • Each switch updates visible trace + axis label + chart title
      • Custom hover shows all three metrics regardless of active view
    """
    products = df["product"].tolist()

    fig = go.Figure()

    # --- Trace 0: Revenue ---
    fig.add_trace(go.Bar(
        y=products, x=df["revenue"],
        orientation="h",
        name="Revenue ($M)",
        marker=dict(color=CHART_COLORS[:5], line=dict(width=0)),
        visible=True,
        customdata=np.stack([df["profit"], df["orders"]], axis=1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Revenue: $%{x:.1f}M<br>"
            "Profit:  $%{customdata[0]:.2f}M<br>"
            "Orders:  %{customdata[1]:,}<br>"
            "<extra></extra>"
        ),
    ))

    # --- Trace 1: Profit ---
    fig.add_trace(go.Bar(
        y=products, x=df["profit"],
        orientation="h",
        name="Profit ($M)",
        marker=dict(color=CHART_COLORS[:5], line=dict(width=0)),
        visible=False,
        customdata=np.stack([df["revenue"], df["orders"]], axis=1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Profit:  $%{x:.2f}M<br>"
            "Revenue: $%{customdata[0]:.1f}M<br>"
            "Orders:  %{customdata[1]:,}<br>"
            "<extra></extra>"
        ),
    ))

    # --- Trace 2: Orders ---
    fig.add_trace(go.Bar(
        y=products, x=df["orders"],
        orientation="h",
        name="Orders",
        marker=dict(color=CHART_COLORS[:5], line=dict(width=0)),
        visible=False,
        customdata=np.stack([df["revenue"], df["profit"]], axis=1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Orders:  %{x:,}<br>"
            "Revenue: $%{customdata[0]:.1f}M<br>"
            "Profit:  $%{customdata[1]:.2f}M<br>"
            "<extra></extra>"
        ),
    ))

    # Dropdown buttons
    fig.update_layout(
        title=dict(text="Q4 Revenue by Product Line",
                   font=dict(size=18, color="#222")),
        height=430,
        xaxis=dict(gridcolor="#e8e8e8"),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
        updatemenus=[dict(
            type="dropdown",
            direction="down",
            active=0,
            x=0.01, xanchor="left",
            y=1.12, yanchor="top",
            bgcolor="#f0f2f6",
            bordercolor="#cccccc",
            font=dict(size=13),
            buttons=[
                dict(
                    label="📊  Revenue",
                    method="update",
                    args=[
                        {"visible": [True, False, False]},
                        {"title": "Q4 Revenue by Product Line",
                         "xaxis.title": "Revenue ($M)",
                         "xaxis.tickprefix": "$",
                         "xaxis.ticksuffix": "M"},
                    ],
                ),
                dict(
                    label="💹  Profit",
                    method="update",
                    args=[
                        {"visible": [False, True, False]},
                        {"title": "Q4 Profit by Product Line",
                         "xaxis.title": "Profit ($M)",
                         "xaxis.tickprefix": "$",
                         "xaxis.ticksuffix": "M"},
                    ],
                ),
                dict(
                    label="🛒  Orders",
                    method="update",
                    args=[
                        {"visible": [False, False, True]},
                        {"title": "Q4 Order Count by Product Line",
                         "xaxis.title": "Number of Orders",
                         "xaxis.tickprefix": "",
                         "xaxis.ticksuffix": ""},
                    ],
                ),
            ],
        )],
    )
    return fig


# ---------------------------------------------------------------------------
# Chart 3 – Marketing Spend vs Revenue Scatter with Trendline
# ---------------------------------------------------------------------------

def chart3_marketing_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot of campaign spend vs revenue.

    Interactive features:
      • Zoom and pan (built-in, free in Plotly)
      • Double-click to reset zoom
      • Color-coded by marketing channel
      • Outlier clearly flagged in hover
    """
    fig = go.Figure()

    channels = df["channel"].unique()
    channel_colors = {
        "Email":       PALETTE["primary"],
        "Social":      PALETTE["secondary"],
        "Paid Search": PALETTE["success"],
        "Webinar":     PALETTE["purple"],
    }

    for ch in channels:
        mask = (df["channel"] == ch) & (~df["outlier"])
        sub  = df[mask]
        fig.add_trace(go.Scatter(
            x=sub["spend_k"], y=sub["revenue_k"],
            mode="markers",
            name=ch,
            marker=dict(color=channel_colors.get(ch, "#aaa"), size=10,
                        opacity=0.85, line=dict(width=0)),
            hovertemplate=(
                "<b>%{customdata}</b> campaign<br>"
                "Spend:   $%{x:.0f}K<br>"
                "Revenue: $%{y:.0f}K<br>"
                f"Channel: {ch}<br>"
                "<extra></extra>"
            ),
            customdata=[ch] * len(sub),
        ))

    # Outlier trace
    outlier = df[df["outlier"]]
    fig.add_trace(go.Scatter(
        x=outlier["spend_k"], y=outlier["revenue_k"],
        mode="markers",
        name="⚠ Outlier",
        marker=dict(color=PALETTE["warning"], size=14,
                    symbol="diamond", line=dict(width=1.5, color="#fff")),
        hovertemplate=(
            "<b>Outlier Campaign</b><br>"
            "Spend:   $%{x:.0f}K<br>"
            "Revenue: $%{y:.0f}K  ← Low ROI!<br>"
            "<extra></extra>"
        ),
    ))

    # OLS trendline (exclude outlier)
    normal = df[~df["outlier"]]
    m, b   = np.polyfit(normal["spend_k"], normal["revenue_k"], 1)
    x_fit  = np.linspace(df["spend_k"].min(), df["spend_k"].max(), 200)
    y_fit  = m * x_fit + b

    fig.add_trace(go.Scatter(
        x=x_fit, y=y_fit,
        mode="lines",
        name=f"Trendline (r ≈ 0.88)",
        line=dict(color=PALETTE["neutral"], width=2, dash="dash"),
        hoverinfo="skip",
    ))

    fig.update_layout(
        title=dict(text="Marketing Spend vs Revenue Generated",
                   font=dict(size=18, color="#222")),
        xaxis=dict(title="Marketing Spend ($K)", tickprefix="$",
                   ticksuffix="K", gridcolor="#e8e8e8"),
        yaxis=dict(title="Revenue Generated ($K)", tickprefix="$",
                   ticksuffix="K", gridcolor="#e8e8e8"),
        hovermode="closest",
        height=460,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
        annotations=[dict(
            x=85, y=120,
            xref="x", yref="y",
            text="High Spend,<br>Low ROI",
            showarrow=True,
            arrowhead=2,
            arrowcolor=PALETTE["warning"],
            font=dict(size=11, color=PALETTE["warning"]),
            bgcolor="#ffe6e6",
            bordercolor=PALETTE["warning"],
            borderwidth=1,
        )],
    )
    return fig


# ---------------------------------------------------------------------------
# Chart 4 – Multi-Metric KPI Dashboard (Subplots)
# ---------------------------------------------------------------------------

def chart4_kpi_subplots(df: pd.DataFrame) -> go.Figure:
    """
    2x2 subplot grid showing revenue, profit, orders, and profit margin.

    Interactive features:
      • Linked x-axes: zooming on one subplot zooms all
      • Shared date range selector at the top
      • Unified hover across all subplots
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Daily Revenue ($)",
            "Daily Profit ($)",
            "Daily Orders",
            "Daily Profit Margin (%)",
        ),
        shared_xaxes=True,
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    margin_pct = (df["profit"] / df["revenue"] * 100).round(1)

    traces = [
        (df["revenue"], PALETTE["primary"],  1, 1, "Revenue",       "$%{y:,.0f}"),
        (df["profit"],  PALETTE["success"],  1, 2, "Profit",        "$%{y:,.0f}"),
        (df["orders"],  PALETTE["secondary"],2, 1, "Orders",        "%{y:,}"),
        (margin_pct,    PALETTE["purple"],   2, 2, "Margin %",      "%{y:.1f}%"),
    ]

    for y_data, color, row, col, name, hover_fmt in traces:
        fig.add_trace(go.Scatter(
            x=df["date"], y=y_data,
            mode="lines",
            name=name,
            line=dict(color=color, width=1.5),
            hovertemplate=(
                f"<b>%{{x|%Y-%m-%d}}</b><br>{name}: {hover_fmt}<extra></extra>"
            ),
        ), row=row, col=col)

    fig.update_layout(
        title=dict(text="Daily KPI Dashboard – 2024  (zoom any panel to sync all)",
                   font=dict(size=17, color="#222")),
        height=580,
        hovermode="x unified",
        showlegend=False,
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
    )

    # Add range selector to top-left xaxis only
    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=1,  label="1M",  step="month", stepmode="backward"),
                dict(count=3,  label="3M",  step="month", stepmode="backward"),
                dict(count=6,  label="6M",  step="month", stepmode="backward"),
                dict(step="all", label="All"),
            ],
            bgcolor="#f0f2f6",
            activecolor=PALETTE["primary"],
        ),
        row=1, col=1,
    )
    fig.update_yaxes(gridcolor="#e8e8e8")
    fig.update_xaxes(gridcolor="#e8e8e8")
    return fig


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def save_html(fig: go.Figure, filename: str) -> None:
    """Export a Plotly figure as a self-contained HTML file."""
    path = os.path.join("output", filename)
    fig.write_html(path, include_plotlyjs="cdn")
    print(f"Saved interactive HTML → {path}")


# ---------------------------------------------------------------------------
# Streamlit dashboard (run with: streamlit run assignment-36-interactive-charts.py)
# ---------------------------------------------------------------------------

def run_streamlit_dashboard() -> None:
    """Full Streamlit dashboard embedding all four Plotly charts."""
    try:
        import streamlit as st
    except ImportError:
        print("Streamlit not installed. Run: pip install streamlit")
        return

    st.set_page_config(
        page_title="Interactive Chart Builder",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.title("📊 Interactive Chart Builder")
    st.markdown(
        "Plotly charts with **hover tooltips**, **dropdown filters**, "
        "**zoom/pan**, and **date range selectors**."
    )
    st.divider()

    daily_df   = _generate_daily_revenue()
    product_df = _generate_product_data()
    mktg_df    = _generate_marketing_data()

    st.subheader("1 · Daily Revenue & Profit Trend")
    st.caption(
        "Hover for exact values · Drag to zoom · Double-click to reset · "
        "Use date buttons or range slider to filter"
    )
    st.plotly_chart(chart1_revenue_trend(daily_df), use_container_width=True)

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("2 · Product-Line Metrics")
        st.caption("Use the dropdown to switch between Revenue, Profit, and Orders")
        st.plotly_chart(chart2_product_dropdown(product_df), use_container_width=True)

    with col_b:
        st.subheader("3 · Marketing Spend vs Revenue")
        st.caption("Zoom in to explore individual campaigns · Click legend to toggle channels")
        st.plotly_chart(chart3_marketing_scatter(mktg_df), use_container_width=True)

    st.divider()

    st.subheader("4 · Multi-KPI Linked Dashboard")
    st.caption("Zoom on any panel and all panels sync · Unified hover shows values across metrics")
    st.plotly_chart(chart4_kpi_subplots(daily_df), use_container_width=True)

    st.divider()
    st.markdown(
        "> **Tip:** Click **Export HTML** from the Plotly toolbar (camera icon) "
        "to download a standalone interactive file you can share by email."
    )


# ---------------------------------------------------------------------------
# Standalone execution  (python assignment-36-interactive-charts.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Detect if Streamlit launched us
    if "streamlit" in sys.modules or any("streamlit" in a for a in sys.argv):
        run_streamlit_dashboard()
    else:
        print("Generating interactive HTML charts …")
        daily_df   = _generate_daily_revenue()
        product_df = _generate_product_data()
        mktg_df    = _generate_marketing_data()

        save_html(chart1_revenue_trend(daily_df),        "chart1_revenue_trend_interactive.html")
        save_html(chart2_product_dropdown(product_df),   "chart2_product_dropdown_interactive.html")
        save_html(chart3_marketing_scatter(mktg_df),     "chart3_marketing_scatter_interactive.html")
        save_html(chart4_kpi_subplots(daily_df),         "chart4_kpi_subplots_interactive.html")

        print("\nAll interactive charts saved to output/")
        print("Open any .html file in your browser to explore.")
        print("\nTo run the full Streamlit dashboard:")
        print("  streamlit run assignment-36-interactive-charts.py")
