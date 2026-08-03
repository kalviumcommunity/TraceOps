"""
dashboard/app.py  –  TraceOps KPI Dashboard (Streamlit)
=========================================================
Frontend dashboard that imports from the Backend data layer.

Run from the project root:
    streamlit run dashboard/app.py
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

# ── Page config MUST be the very first Streamlit command ───────────────────────
st.set_page_config(
    page_title="TraceOps KPI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Import from Backend data layer ─────────────────────────────────────────────
BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Backend"))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

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

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Page background */
.stApp { background: linear-gradient(135deg, #020817 0%, #0f172a 60%, #1a0533 100%); }

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* Metric cards */
[data-testid="metric-container"] {
    background: rgba(15,23,42,0.85);
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 1.2rem 1.3rem 1rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 24px rgba(0,0,0,0.35);
    transition: border-color .2s;
}
[data-testid="metric-container"]:hover { border-color: #334155; }
[data-testid="stMetricLabel"]  { color: #94a3b8 !important; font-size: 0.8rem !important; font-weight: 600 !important; letter-spacing: .04em; }
[data-testid="stMetricValue"]  { color: #f1f5f9 !important; font-size: 1.85rem !important; font-weight: 800 !important; letter-spacing: -.03em; }
[data-testid="stMetricDelta"]  { font-size: 0.85rem !important; font-weight: 600 !important; }

/* Section headers */
.section-header {
    display: flex; align-items: center; gap: .55rem;
    font-size: .72rem; font-weight: 700; letter-spacing: .08em;
    text-transform: uppercase; color: #475569; margin-bottom: .6rem;
}
.dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.dot-green  { background: #10b981; box-shadow: 0 0 8px #10b981; }
.dot-blue   { background: #3b82f6; box-shadow: 0 0 8px #3b82f6; }
.dot-purple { background: #8b5cf6; box-shadow: 0 0 8px #8b5cf6; }
.dot-yellow { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }

/* Divider */
hr { border-color: #1e293b !important; margin: 1.5rem 0 !important; }

/* Sidebar */
[data-testid="stSidebar"] { background: #0f172a !important; border-right: 1px solid #1e293b; }
[data-testid="stSidebar"] label { color: #94a3b8 !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

/* Info/success boxes */
.stAlert { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)


# ── Data helpers ───────────────────────────────────────────────────────────────

# Absolute path to the CSV so it works regardless of current working dir
DATA_PATH = os.path.join(BACKEND_PATH, RAW_DATA_PATH)

@st.cache_data(ttl=3600)
def load_kpi_data():
    if not os.path.exists(DATA_PATH):
        generate_transaction_data(DATA_PATH)
    df = load_data(DATA_PATH)
    return df


def window(df: pd.DataFrame, ref: pd.Timestamp, days: int) -> pd.DataFrame:
    start = ref - pd.Timedelta(days=days)
    return df[(df["transaction_date"] > start) & (df["transaction_date"] <= ref)]


def pct_change(curr, prior):
    if not prior or prior == 0:
        return 0.0
    return ((curr - prior) / abs(prior)) * 100


def trend_meta(change, inverted=False):
    t = 2.0
    if inverted:
        if change < -t: return "↓", "#10b981", "✅ On Track"
        if change > t:  return "↑", "#ef4444", "❌ Alert"
        return "→", "#f59e0b", "⚠️ Stable"
    if change > t:  return "↑", "#10b981", "✅ On Track"
    if change < -t: return "↓", "#ef4444", "❌ Alert"
    return "→", "#f59e0b", "⚠️ Stable"


def compute_kpis(df: pd.DataFrame, ref: pd.Timestamp):
    prior_ref = ref - pd.Timedelta(days=30)
    success   = df[df["payment_status"] == "Success"]

    def rev(r, d=30):
        w = window(df, r, d)
        return float(w[w["payment_status"] == "Success"]["amount"].sum())

    def users(r, d=30):
        return calculate_mau(df, days=d, reference_date=r)

    def aov(r, d=30):
        w = window(df, r, d)
        s = w[w["payment_status"] == "Success"]["amount"]
        return float(s.mean()) if len(s) > 0 else 0.0

    def churn(r, d=30):
        return calculate_churn_rate(df, period_days=d, reference_date=r) * 100

    def sat(r, d=30):
        w = window(df, r, d)
        psr = calculate_payment_success_rate(w) if len(w) > 0 else 0.0
        return round(psr * 5, 2)

    curr = {
        "revenue":      rev(ref),
        "users":        users(ref),
        "aov":          aov(ref),
        "churn":        churn(ref),
        "satisfaction": sat(ref),
    }
    prior = {
        "revenue":      rev(prior_ref),
        "users":        users(prior_ref),
        "aov":          aov(prior_ref),
        "churn":        churn(prior_ref),
        "satisfaction": sat(prior_ref),
    }
    return curr, prior


# ── Chart builders ─────────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter"),
    margin=dict(l=10, r=10, t=40, b=10),
    hovermode="x unified",
    xaxis=dict(gridcolor="#1e293b", linecolor="#1e293b", tickcolor="#1e293b"),
    yaxis=dict(gridcolor="#1e293b", linecolor="rgba(0,0,0,0)", tickcolor="#1e293b"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
)


def revenue_trend_chart(df: pd.DataFrame, ref: pd.Timestamp):
    dates  = pd.date_range(end=ref, periods=30, freq="D")
    daily  = (
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
        title=dict(text="Daily Revenue — last 30 days", font=dict(size=14, color="#f1f5f9")),
        height=280,
        yaxis=dict(tickprefix="$", tickformat=",.0f", gridcolor="#1e293b"),
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("yaxis",)},
    )
    return fig


def users_trend_chart(df: pd.DataFrame, ref: pd.Timestamp):
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
        title=dict(text="Daily Active Users — last 30 days", font=dict(size=14, color="#f1f5f9")),
        height=280, **PLOTLY_LAYOUT,
    )
    return fig


def segment_chart(df: pd.DataFrame, ref: pd.Timestamp):
    w = window(df, ref, 30)
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
            marker=dict(
                color=[colors.get(s, "#64748b") for s in seg["Segment"]],
                line=dict(width=0),
            ),
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
        )
    ])
    fig.update_layout(
        title=dict(text="Revenue by Customer Segment", font=dict(size=14, color="#f1f5f9")),
        height=280,
        yaxis=dict(tickprefix="$", gridcolor="#1e293b"),
        bargap=0.3,
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("yaxis",)},
    )
    fig.update_traces(marker_line_color="rgba(0,0,0,0)")
    return fig


def product_donut(df: pd.DataFrame, ref: pd.Timestamp):
    w = window(df, ref, 30)
    prod = (
        w[w["payment_status"] == "Success"]
        .groupby("product")["amount"].sum()
        .reset_index()
    )
    colors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899"]
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
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis", "hovermode", "legend")},
    )
    return fig


def kpi_subplot(df: pd.DataFrame, ref: pd.Timestamp):
    dates   = pd.date_range(end=ref, periods=30, freq="D")
    success = df[df["payment_status"] == "Success"].set_index("transaction_date")
    daily_rev  = success.resample("D")["amount"].sum().reindex(dates, fill_value=0)
    daily_usr  = success.resample("D")["customer_id"].nunique().reindex(dates, fill_value=0)
    daily_aov  = (daily_rev / daily_usr.replace(0, np.nan)).fillna(0)
    daily_psr  = (
        df.set_index("transaction_date")
        .resample("D")
        .apply(lambda g: len(g[g["payment_status"] == "Success"]) / max(len(g), 1) * 100)
        .reindex(dates, fill_value=0)
    )

    fig = make_subplots(
        rows=2, cols=2, shared_xaxes=True,
        subplot_titles=("Revenue ($)", "Active Users", "Avg Order Value ($)", "Payment Success Rate (%)"),
        vertical_spacing=0.14, horizontal_spacing=0.08,
    )

    traces = [
        (daily_rev,  "#3b82f6", 1, 1, "$%{y:,.0f}"),
        (daily_usr,  "#10b981", 1, 2, "%{y:,}"),
        (daily_aov,  "#8b5cf6", 2, 1, "$%{y:,.2f}"),
        (daily_psr,  "#f59e0b", 2, 2, "%{y:.1f}%"),
    ]
    for data, color, row, col, fmt in traces:
        # Convert hex color (#3b82f6 -> rgba(59,130,246,0.08))
        h = color.lstrip('#')
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        fill_rgba = f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.08)"

        fig.add_trace(go.Scatter(
            x=data.index, y=data.values,
            mode="lines", line=dict(color=color, width=1.8),
            fill="tozeroy", fillcolor=fill_rgba,
            hovertemplate=f"<b>%{{x|%d %b}}</b><br>{fmt}<extra></extra>",
            showlegend=False,
        ), row=row, col=col)

    fig.update_layout(
        title=dict(text="Multi-KPI Linked Dashboard — zoom any panel to sync all",
                   font=dict(size=14, color="#f1f5f9")),
        height=420,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", family="Inter"),
        margin=dict(l=10, r=10, t=55, b=10),
    )
    fig.update_xaxes(gridcolor="#1e293b", linecolor="#1e293b")
    fig.update_yaxes(gridcolor="#1e293b", linecolor="rgba(0,0,0,0)")
    for i in range(1, 5):
        fig.layout.annotations[i - 1].font.color = "#94a3b8"
        fig.layout.annotations[i - 1].font.size  = 12
    return fig


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar(df: pd.DataFrame):
    st.sidebar.markdown("## ⚙️ Filters")
    st.sidebar.markdown("---")

    ref_default = df["transaction_date"].max().date()
    ref_date    = st.sidebar.date_input(
        "Reference Date", value=ref_default,
        min_value=df["transaction_date"].min().date(),
        max_value=ref_default,
        help="KPIs use a 30-day window ending on this date.",
    )

    segments = ["All"] + sorted(df["customer_type"].unique().tolist())
    seg_filter = st.sidebar.selectbox("Customer Segment", segments)

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
**📁 Data Source**
`Backend/data/raw/kpi_transactions.csv`

**🔄 Compute Layer**
`Backend/kpis/kpi_functions.py`

**📐 Comparison Window**
Rolling 30-day vs prior 30-day

**⚠️ Inverted Metrics**
Churn Rate: ↓ = green
""")
    return pd.Timestamp(ref_date), seg_filter


# ── Main dashboard ─────────────────────────────────────────────────────────────

def main():
    # ── Header ─────────────────────────────────────────────────────────────────
    col_logo, col_title = st.columns([1, 11])
    with col_logo:
        st.markdown("<p style='font-size:2.8rem;margin:0'>📊</p>", unsafe_allow_html=True)
    with col_title:
        st.markdown("""
        <h1 style='margin:0;font-size:1.6rem;font-weight:800;
                   background:linear-gradient(90deg,#3b82f6,#8b5cf6);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   letter-spacing:-.02em'>
            TraceOps · Sales Performance Dashboard
        </h1>
        <p style='margin:0;font-size:.8rem;color:#475569'>
            KPI Card & Summary Metrics · Assignment 2.47 ·
            Data: <code style="background:#1e293b;padding:1px 6px;border-radius:4px;
                               color:#60a5fa;font-size:.75rem">
                      Backend/kpis/kpi_functions.py
                  </code>
        </p>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Load data & sidebar ─────────────────────────────────────────────────────
    df      = load_kpi_data()
    ref, seg_filter = render_sidebar(df)

    if seg_filter != "All":
        df = df[df["customer_type"] == seg_filter]

    curr, prior = compute_kpis(df, ref)

    # ── Level 1: KPI Cards ──────────────────────────────────────────────────────
    st.markdown("""<div class="section-header">
        <span class="dot dot-green"></span> Level 1 — Business Status at a Glance
    </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)

    rev_chg  = pct_change(curr["revenue"],      prior["revenue"])
    usr_chg  = pct_change(curr["users"],        prior["users"])
    aov_chg  = pct_change(curr["aov"],          prior["aov"])
    churn_chg= pct_change(curr["churn"],        prior["churn"])
    sat_chg  = pct_change(curr["satisfaction"], prior["satisfaction"])

    with c1:
        st.metric("💰 Revenue",
                  f"${curr['revenue']/1e6:.2f}M",
                  f"{rev_chg:+.1f}%",
                  help=f"Prior 30d: ${prior['revenue']/1e6:.2f}M")
    with c2:
        st.metric("👥 Active Users",
                  f"{curr['users']:,}",
                  f"{usr_chg:+.1f}%",
                  help=f"Prior 30d: {prior['users']:,}")
    with c3:
        st.metric("🛒 Avg Order Value",
                  f"${curr['aov']:,.2f}",
                  f"{aov_chg:+.1f}%",
                  help=f"Prior 30d: ${prior['aov']:,.2f}")
    with c4:
        st.metric("📉 Churn Rate",
                  f"{curr['churn']:.1f}%",
                  f"{churn_chg:+.1f}%",
                  delta_color="inverse",          # ← down is good
                  help=f"Prior 30d: {prior['churn']:.1f}%")
    with c5:
        st.metric("⭐ Satisfaction",
                  f"{curr['satisfaction']:.2f}/5",
                  f"{sat_chg:+.1f}%",
                  help=f"Prior 30d: {prior['satisfaction']:.2f}/5")

    st.caption(
        "🟢 On Track (>2% in good direction)  "
        "🔴 Alert (>2% in bad direction)  "
        "🟡 Stable (within ±2%)"
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Level 2: Trend charts ───────────────────────────────────────────────────
    st.markdown("""<div class="section-header">
        <span class="dot dot-blue"></span> Level 2 — 30-Day Trends
    </div>""", unsafe_allow_html=True)

    t1, t2 = st.columns(2)
    with t1:
        st.plotly_chart(revenue_trend_chart(df, ref), use_container_width=True)
    with t2:
        st.plotly_chart(users_trend_chart(df, ref),   use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Level 3: Segments ───────────────────────────────────────────────────────
    st.markdown("""<div class="section-header">
        <span class="dot dot-purple"></span> Level 3 — Segment & Product Breakdown
    </div>""", unsafe_allow_html=True)

    s1, s2 = st.columns(2)
    with s1:
        st.plotly_chart(segment_chart(df, ref), use_container_width=True)
    with s2:
        st.plotly_chart(product_donut(df, ref), use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Level 3b: Linked KPI subplots ───────────────────────────────────────────
    st.markdown("""<div class="section-header">
        <span class="dot dot-purple"></span> Level 3b — Linked Multi-KPI Chart
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(kpi_subplot(df, ref), use_container_width=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Level 4: KPI summary table ──────────────────────────────────────────────
    st.markdown("""<div class="section-header">
        <span class="dot dot-yellow"></span> Level 4 — KPI Summary Table
    </div>""", unsafe_allow_html=True)

    rows = [
        ("💰 Revenue",        f"${curr['revenue']/1e6:.2f}M",  f"${prior['revenue']/1e6:.2f}M",  rev_chg,   False),
        ("👥 Active Users",   f"{curr['users']:,}",            f"{prior['users']:,}",            usr_chg,   False),
        ("🛒 Avg Order Value",f"${curr['aov']:,.2f}",          f"${prior['aov']:,.2f}",          aov_chg,   False),
        ("📉 Churn Rate",     f"{curr['churn']:.1f}%",         f"{prior['churn']:.1f}%",         churn_chg, True),
        ("⭐ Satisfaction",   f"{curr['satisfaction']:.2f}/5", f"{prior['satisfaction']:.2f}/5", sat_chg,   False),
    ]

    table_data = []
    for label, cur_disp, pri_disp, chg, inv in rows:
        arrow, color, status = trend_meta(chg, inv)
        table_data.append({
            "Metric":        label,
            "Current (30d)": cur_disp,
            "Prior (30–60d)":pri_disp,
            "Δ Change":      f"{chg:+.1f}%",
            "Trend":         arrow,
            "Status":        status,
        })

    st.dataframe(
        pd.DataFrame(table_data),
        hide_index=True,
        use_container_width=True,
    )

    # ── Level 4b: Raw data explorer ─────────────────────────────────────────────
    with st.expander("🔍 Raw Transaction Data Explorer"):
        w30 = window(df, ref, 30)
        st.write(f"**{len(w30):,}** transactions in the current 30-day window")
        st.dataframe(
            w30[["transaction_id", "customer_id", "transaction_date",
                 "amount", "customer_type", "product", "payment_status"]]
            .sort_values("transaction_date", ascending=False)
            .reset_index(drop=True),
            use_container_width=True,
            height=300,
        )
        csv = w30.to_csv(index=False)
        st.download_button("⬇ Download CSV", csv, "kpi_transactions_30d.csv", "text/csv")

    # ── Footer ──────────────────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption(
        f"📅 Reference date: **{ref.strftime('%Y-%m-%d')}**  ·  "
        f"Data: `Backend/data/raw/kpi_transactions.csv`  ·  "
        f"Compute: `Backend/kpis/kpi_functions.py`  ·  "
        f"No hardcoded values – all KPIs computed from the clean data layer"
    )


if __name__ == "__main__":
    main()
