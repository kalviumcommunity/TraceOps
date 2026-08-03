/**
 * data.js  –  Synthetic KPI data matching kpi_functions.py logic
 *
 * Generates the same five KPIs:
 *   Revenue | Active Users | Avg Order Value | Churn Rate | Satisfaction
 * with current vs prior 30-day window values and 30-day daily trend arrays.
 */

// ── Seeded PRNG (Mulberry32) so data is consistent across renders ──────────
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function buildDailyTrend(rand, base, noise, days = 30) {
  return Array.from({ length: days }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (days - 1 - i));
    return {
      date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      value: Math.max(0, +(base + (rand() - 0.45) * noise).toFixed(2)),
    };
  });
}

export function generateKPIData() {
  const rand = mulberry32(42);

  // ── Revenue (daily, in USD) ──────────────────────────────────────────────
  const revTrend = buildDailyTrend(rand, 185_000, 40_000);
  const currentRevenue = revTrend.reduce((s, d) => s + d.value, 0);
  const priorRevenue = currentRevenue * (1 - 0.125 + rand() * 0.04);

  // ── Active Users (daily unique) ───────────────────────────────────────────
  const usersTrend = buildDailyTrend(rand, 3_800, 600);
  const currentUsers = Math.round(usersTrend[usersTrend.length - 1].value * 30 / 5);
  const priorUsers = Math.round(currentUsers * (1 - 0.052 + rand() * 0.02));

  // ── Average Order Value ────────────────────────────────────────────────────
  const aovTrend = buildDailyTrend(rand, 147, 18);
  const currentAOV = +(aovTrend.reduce((s, d) => s + d.value, 0) / 30).toFixed(2);
  const priorAOV = +(currentAOV * (1 - 0.021 + rand() * 0.01)).toFixed(2);

  // ── Churn Rate (%) – inverted metric ──────────────────────────────────────
  const churnTrend = buildDailyTrend(rand, 5.2, 0.8);
  const currentChurn = +churnTrend[churnTrend.length - 1].value.toFixed(1);
  const priorChurn = +(currentChurn * (1 + 0.028 + rand() * 0.01)).toFixed(1);

  // ── Satisfaction (/ 5) ────────────────────────────────────────────────────
  const satTrend = buildDailyTrend(rand, 4.72, 0.12);
  const currentSat = Math.min(5, +(satTrend[satTrend.length - 1].value).toFixed(2));
  const priorSat = +(currentSat * (1 - 0.003 + rand() * 0.001)).toFixed(2);

  // ── Revenue by segment (for bar chart) ────────────────────────────────────
  const segmentData = [
    { segment: "Enterprise", revenue: +(currentRevenue * 0.38).toFixed(0), color: "#3b82f6" },
    { segment: "SMB",        revenue: +(currentRevenue * 0.35).toFixed(0), color: "#10b981" },
    { segment: "Startup",    revenue: +(currentRevenue * 0.27).toFixed(0), color: "#8b5cf6" },
  ];

  // ── Product mix (for donut) ────────────────────────────────────────────────
  const productData = [
    { name: "Cloud API",        value: 38, color: "#3b82f6" },
    { name: "Enterprise Suite", value: 27, color: "#10b981" },
    { name: "Analytics Pro",    value: 22, color: "#8b5cf6" },
    { name: "Basic Tier",       value: 13, color: "#f59e0b" },
  ];

  return {
    kpis: [
      {
        id: "revenue",
        label: "Total Revenue",
        current: currentRevenue,
        prior: priorRevenue,
        display: `$${(currentRevenue / 1_000_000).toFixed(2)}M`,
        inverted: false,
        trend: revTrend,
        color: "#3b82f6",
        icon: "💰",
        unit: "$",
        format: (v) => `$${(v / 1_000_000).toFixed(2)}M`,
      },
      {
        id: "users",
        label: "Active Users",
        current: currentUsers,
        prior: priorUsers,
        display: currentUsers.toLocaleString(),
        inverted: false,
        trend: usersTrend,
        color: "#10b981",
        icon: "👥",
        unit: "",
        format: (v) => Math.round(v).toLocaleString(),
      },
      {
        id: "aov",
        label: "Avg Order Value",
        current: currentAOV,
        prior: priorAOV,
        display: `$${currentAOV.toFixed(2)}`,
        inverted: false,
        trend: aovTrend,
        color: "#8b5cf6",
        icon: "🛒",
        unit: "$",
        format: (v) => `$${(+v).toFixed(2)}`,
      },
      {
        id: "churn",
        label: "Churn Rate",
        current: currentChurn,
        prior: priorChurn,
        display: `${currentChurn}%`,
        inverted: true,   // ← lower is better
        trend: churnTrend,
        color: "#f59e0b",
        icon: "📉",
        unit: "%",
        format: (v) => `${(+v).toFixed(1)}%`,
      },
      {
        id: "satisfaction",
        label: "Satisfaction",
        current: currentSat,
        prior: priorSat,
        display: `${currentSat}/5`,
        inverted: false,
        trend: satTrend,
        color: "#ec4899",
        icon: "⭐",
        unit: "/5",
        format: (v) => `${(+v).toFixed(2)}/5`,
      },
    ],
    segmentData,
    productData,
    revenueTrend: revTrend,
    usersTrend,
  };
}
