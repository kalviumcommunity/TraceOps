import React, { useMemo } from "react";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";
import { generateKPIData } from "./data";
import "./App.css";

// ── Helpers ───────────────────────────────────────────────────────────────────
function pctChange(current, prior) {
  if (!prior || prior === 0) return 0;
  return ((current - prior) / Math.abs(prior)) * 100;
}

function trendMeta(change, inverted) {
  const threshold = 2;
  if (inverted) {
    if (change < -threshold) return { arrow: "↓", label: "On Track",    cls: "green" };
    if (change > threshold)  return { arrow: "↑", label: "Alert",       cls: "red"   };
    return                          { arrow: "→", label: "Stable",      cls: "yellow" };
  }
  if (change > threshold)    return { arrow: "↑", label: "On Track",    cls: "green" };
  if (change < -threshold)   return { arrow: "↓", label: "Alert",       cls: "red"   };
  return                            { arrow: "→", label: "Stable",      cls: "yellow" };
}

// ── Custom tooltip ─────────────────────────────────────────────────────────────
const ChartTooltip = ({ active, payload, label, prefix = "", suffix = "" }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name ?? p.dataKey}: <strong>{prefix}{typeof p.value === "number" ? p.value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : p.value}{suffix}</strong>
        </p>
      ))}
    </div>
  );
};

// ── KPI Card ──────────────────────────────────────────────────────────────────
function KPICard({ kpi }) {
  const change = pctChange(kpi.current, kpi.prior);
  const meta   = trendMeta(change, kpi.inverted);

  return (
    <div className={`kpi-card kpi-card--${meta.cls}`}>
      <div className="kpi-card__header">
        <span className="kpi-card__icon">{kpi.icon}</span>
        <span className={`kpi-badge kpi-badge--${meta.cls}`}>{meta.label}</span>
      </div>

      <p className="kpi-card__label">{kpi.label}</p>
      <p className="kpi-card__value">{kpi.display}</p>

      <div className="kpi-card__delta">
        <span className={`kpi-arrow kpi-arrow--${meta.cls}`}>{meta.arrow}</span>
        <span className={`kpi-change kpi-change--${meta.cls}`}>
          {change >= 0 ? "+" : ""}{change.toFixed(1)}% vs prior 30d
        </span>
      </div>

      {/* Sparkline */}
      <div className="kpi-spark">
        <ResponsiveContainer width="100%" height={52}>
          <AreaChart data={kpi.trend} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={`grad-${kpi.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={kpi.color} stopOpacity={0.35} />
                <stop offset="95%" stopColor={kpi.color} stopOpacity={0}    />
              </linearGradient>
            </defs>
            <Area
              type="monotone"
              dataKey="value"
              stroke={kpi.color}
              strokeWidth={1.8}
              fill={`url(#grad-${kpi.id})`}
              dot={false}
              activeDot={{ r: 3, fill: kpi.color }}
            />
            <Tooltip content={<ChartTooltip prefix={kpi.unit === "$" ? "$" : ""} suffix={kpi.unit !== "$" ? kpi.unit : ""} />} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <p className="kpi-prior">Prior period: {kpi.format(kpi.prior)}</p>
    </div>
  );
}

// ── Revenue trend chart ────────────────────────────────────────────────────────
function RevenueTrendChart({ data }) {
  return (
    <div className="chart-card">
      <h3 className="chart-title">Daily Revenue Trend <span className="chart-sub">— last 30 days</span></h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}   />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false}
            interval={4} axisLine={{ stroke: "#1e293b" }} />
          <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false}
            axisLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
          <Tooltip content={<ChartTooltip prefix="$" />} />
          <Area type="monotone" dataKey="value" name="Revenue"
            stroke="#3b82f6" strokeWidth={2}
            fill="url(#revGrad)" dot={false} activeDot={{ r: 4, fill: "#3b82f6" }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Active users chart ─────────────────────────────────────────────────────────
function UsersChart({ data }) {
  return (
    <div className="chart-card">
      <h3 className="chart-title">Daily Active Users <span className="chart-sub">— last 30 days</span></h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false}
            interval={4} axisLine={{ stroke: "#1e293b" }} />
          <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false}
            axisLine={false} tickFormatter={(v) => v.toLocaleString()} />
          <Tooltip content={<ChartTooltip />} />
          <Line type="monotone" dataKey="value" name="Users"
            stroke="#10b981" strokeWidth={2} dot={false}
            activeDot={{ r: 4, fill: "#10b981" }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Revenue by segment ─────────────────────────────────────────────────────────
function SegmentChart({ data }) {
  return (
    <div className="chart-card">
      <h3 className="chart-title">Revenue by Segment</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}
          barSize={36}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="segment" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false}
            tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
          <Tooltip content={<ChartTooltip prefix="$" />} />
          <Bar dataKey="revenue" name="Revenue" radius={[6, 6, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Product mix donut ──────────────────────────────────────────────────────────
function ProductDonut({ data }) {
  const RADIAN = Math.PI / 180;
  const label = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    if (percent < 0.08) return null;
    const r = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + r * Math.cos(-midAngle * RADIAN);
    const y = cy + r * Math.sin(-midAngle * RADIAN);
    return (
      <text x={x} y={y} fill="#fff" textAnchor="middle" dominantBaseline="central"
        fontSize={12} fontWeight={700}>
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div className="chart-card">
      <h3 className="chart-title">Product Mix</h3>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie data={data} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
            dataKey="value" labelLine={false} label={label}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} stroke="none" />
            ))}
          </Pie>
          <Tooltip formatter={(v, name) => [`${v}%`, name]} />
          <Legend iconType="circle" iconSize={8}
            formatter={(v) => <span style={{ color: "#94a3b8", fontSize: 12 }}>{v}</span>} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── KPI Table ─────────────────────────────────────────────────────────────────
function KPITable({ kpis }) {
  return (
    <div className="table-card">
      <h3 className="chart-title">KPI Summary Table</h3>
      <table className="kpi-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Current (30d)</th>
            <th>Prior (30–60d)</th>
            <th>Δ Change</th>
            <th>Trend</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {kpis.map((kpi) => {
            const change = pctChange(kpi.current, kpi.prior);
            const meta   = trendMeta(change, kpi.inverted);
            return (
              <tr key={kpi.id}>
                <td><span className="table-icon">{kpi.icon}</span>{kpi.label}</td>
                <td className="mono">{kpi.display}</td>
                <td className="mono muted">{kpi.format(kpi.prior)}</td>
                <td className={`mono kpi-change--${meta.cls}`}>
                  {change >= 0 ? "+" : ""}{change.toFixed(1)}%
                </td>
                <td className={`kpi-arrow--${meta.cls}`} style={{ fontSize: "1.1rem" }}>
                  {meta.arrow}
                </td>
                <td><span className={`status-pill status-pill--${meta.cls}`}>{meta.label}</span></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Header ────────────────────────────────────────────────────────────────────
function Header() {
  const now = new Date().toLocaleDateString("en-US", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });
  return (
    <header className="dashboard-header">
      <div className="header-left">
        <div className="header-logo">
          <span className="logo-icon">📊</span>
          <span className="logo-text">TraceOps</span>
        </div>
        <div className="header-divider" />
        <div>
          <h1 className="header-title">Sales Performance Dashboard</h1>
          <p className="header-sub">KPI Card & Summary Metrics · Assignment 2.47</p>
        </div>
      </div>
      <div className="header-right">
        <span className="header-date">{now}</span>
        <span className="header-badge">Live · 30-day rolling</span>
      </div>
    </header>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const { kpis, segmentData, productData, revenueTrend, usersTrend } =
    useMemo(() => generateKPIData(), []);

  return (
    <div className="app">
      <Header />

      <main className="dashboard">
        {/* Level 1 – KPI Cards */}
        <section className="section">
          <div className="section-label">
            <span className="section-dot" />
            Level 1 — Business Status at a Glance
          </div>
          <div className="kpi-grid">
            {kpis.map((kpi) => (
              <KPICard key={kpi.id} kpi={kpi} />
            ))}
          </div>
        </section>

        {/* Level 2 – Trend Charts */}
        <section className="section">
          <div className="section-label">
            <span className="section-dot section-dot--blue" />
            Level 2 — 30-Day Trends
          </div>
          <div className="charts-row">
            <RevenueTrendChart data={revenueTrend} />
            <UsersChart        data={usersTrend}   />
          </div>
        </section>

        {/* Level 3 – Segments */}
        <section className="section">
          <div className="section-label">
            <span className="section-dot section-dot--purple" />
            Level 3 — Segment & Product Breakdown
          </div>
          <div className="charts-row">
            <SegmentChart data={segmentData}  />
            <ProductDonut data={productData}  />
          </div>
        </section>

        {/* Level 4 – Summary Table */}
        <section className="section">
          <div className="section-label">
            <span className="section-dot section-dot--yellow" />
            Level 4 — KPI Summary Table
          </div>
          <KPITable kpis={kpis} />
        </section>

        <footer className="footer">
          <p>
            Data sourced from <code>data/raw/kpi_transactions.csv</code> via{" "}
            <code>kpis/kpi_functions.py</code> ·
            Comparison window: 30-day rolling ·
            Inverted metrics (Churn Rate): ↓ = green
          </p>
        </footer>
      </main>
    </div>
  );
}
