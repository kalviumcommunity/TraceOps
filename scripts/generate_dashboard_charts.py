import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

# Set consistent style & palette
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
PRIMARY_BLUE = '#1f77b4'
SECONDARY_ORANGE = '#ff7f0e'
SUCCESS_GREEN = '#2ca02c'
DANGER_RED = '#d62728'

months = pd.date_range('2024-01-01', periods=12, freq='ME')
month_labels = [m.strftime('%b') for m in months]

# -------------------------------------------------------------
# Chart 1: Revenue Trend (Line Chart)
# -------------------------------------------------------------
revenue = [4.2, 4.5, 4.8, 4.6, 5.0, 5.1, 4.9, 4.7, 5.2, 5.4, 5.5, 5.2]

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(month_labels, revenue, marker='o', linewidth=2.5, color=PRIMARY_BLUE, label='Monthly Revenue ($M)')
ax.axhline(y=5.0, color=SUCCESS_GREEN, linestyle='--', linewidth=1.8, label='Target: $5.0M')

# Annotate target achievement point
ax.annotate('Target Reached ($5.0M)', xy=('May', 5.0), xytext=('Mar', 5.3),
            arrowprops=dict(facecolor=SUCCESS_GREEN, shrink=0.08, width=1.5, headwidth=6),
            fontsize=10, fontweight='bold', color=SUCCESS_GREEN)

ax.set_title('Monthly Revenue Trend (2024)', fontsize=14, fontweight='bold', pad=12)
ax.set_xlabel('Month', fontsize=12, fontweight='bold')
ax.set_ylabel('Revenue ($M)', fontsize=12, fontweight='bold')
ax.set_ylim(3.8, 6.0)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper left', frameon=True)

plt.tight_layout()
plt.savefig('output/revenue_trend.png', dpi=300)
plt.close()
print("Saved output/revenue_trend.png")

# -------------------------------------------------------------
# Chart 2: Customer Metrics (Dual Line Chart)
# -------------------------------------------------------------
active_customers = [2100, 2150, 2220, 2280, 2350, 2390, 2410, 2430, 2460, 2480, 2510, 2500]
churned_customers = [120, 115, 110, 105, 98, 95, 102, 108, 92, 88, 85, 82]

fig, ax1 = plt.subplots(figsize=(10, 5))

color_active = PRIMARY_BLUE
ax1.set_xlabel('Month', fontsize=12, fontweight='bold')
ax1.set_ylabel('Active Customers', color=color_active, fontsize=12, fontweight='bold')
line1 = ax1.plot(month_labels, active_customers, color=color_active, marker='o', linewidth=2.5, label='Active Customers')
ax1.tick_params(axis='y', labelcolor=color_active)
ax1.set_ylim(1800, 2700)

ax2 = ax1.twinx()
color_churn = DANGER_RED
ax2.set_ylabel('Churned Customers', color=color_churn, fontsize=12, fontweight='bold')
line2 = ax2.plot(month_labels, churned_customers, color=color_churn, marker='s', linestyle='--', linewidth=2, label='Churned Customers')
ax2.tick_params(axis='y', labelcolor=color_churn)
ax2.set_ylim(50, 150)

# Combine legends
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left', frameon=True)

# Annotation
ax1.annotate('Retention Campaign Launched', xy=('May', 2350), xytext=('Feb', 2550),
             arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=5),
             fontsize=9, fontweight='bold')

plt.title('Active vs. Churned Customers Trend (2024)', fontsize=14, fontweight='bold', pad=12)
plt.tight_layout()
plt.savefig('output/customer_metrics_trend.png', dpi=300)
plt.close()
print("Saved output/customer_metrics_trend.png")

# -------------------------------------------------------------
# Chart 3: Average Order Value (AOV) Trend
# -------------------------------------------------------------
aov = [132, 134, 136, 135, 139, 142, 140, 138, 143, 146, 147, 145]

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(month_labels, aov, marker='^', linewidth=2.5, color=SECONDARY_ORANGE, label='Avg Order Value ($)')
ax.axhline(y=140, color='gray', linestyle='--', linewidth=1.5, label='Target AOV ($140)')

ax.annotate('Q4 Upsell Surge ($147)', xy=('Nov', 147), xytext=('Jul', 148),
            arrowprops=dict(facecolor=SECONDARY_ORANGE, shrink=0.08, width=1.5, headwidth=6),
            fontsize=10, fontweight='bold', color=SECONDARY_ORANGE)

ax.set_title('Average Order Value (AOV) Monthly Trend (2024)', fontsize=14, fontweight='bold', pad=12)
ax.set_xlabel('Month', fontsize=12, fontweight='bold')
ax.set_ylabel('Avg Order Value ($)', fontsize=12, fontweight='bold')
ax.set_ylim(125, 155)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper left', frameon=True)

plt.tight_layout()
plt.savefig('output/aov_trend.png', dpi=300)
plt.close()
print("Saved output/aov_trend.png")

# -------------------------------------------------------------
# Chart 4: Revenue by Segment (Bar Chart - Level 3)
# -------------------------------------------------------------
segments = ['Enterprise', 'Mid-Market', 'SMB', 'Starter']
segment_revenue = [2.1, 1.5, 1.0, 0.6]
segment_colors = [PRIMARY_BLUE, SECONDARY_ORANGE, SUCCESS_GREEN, DANGER_RED]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(segments, segment_revenue, color=segment_colors, height=0.6)
ax.set_xlabel('Revenue ($M)', fontsize=12, fontweight='bold')
ax.set_title('Revenue by Customer Segment', fontsize=14, fontweight='bold', pad=12)
ax.set_xlim(0, 2.5)
ax.grid(True, axis='x', alpha=0.3)

# Add value labels on bars
for bar, val in zip(bars, segment_revenue):
    ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
            f'${val}M ({val/sum(segment_revenue)*100:.1f}%)', va='center', fontsize=11, fontweight='bold')

plt.gca().invert_yaxis()  # Highest revenue at top
plt.tight_layout()
plt.savefig('output/revenue_by_segment.png', dpi=300)
plt.close()
print("Saved output/revenue_by_segment.png")
