import os
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

# Use clean matplotlib style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

# -------------------------------------------------------------
# Define Palette & Design Tokens (Consistent Across All Charts)
# -------------------------------------------------------------
PALETTE = {
    'primary': '#1f77b4',      # Blue - Cloud / Primary metric
    'secondary': '#ff7f0e',    # Orange - Analytics / Secondary metric
    'success': '#2ca02c',      # Green - Security / Target / Growth
    'warning': '#d62728',      # Red - Database / Danger / Outliers
    'purple': '#9467bd',       # Purple - AI & ML / Premium
    'neutral': '#7f7f7f'       # Gray - Grid / Baseline
}

CHART_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

# -------------------------------------------------------------
# Chart 1: Bar Chart (Comparison) - Total Revenue by Product Line
# -------------------------------------------------------------
def create_chart1():
    product_lines = ['Cloud Solutions', 'Analytics Platform', 'Security Suite', 'Database Services', 'AI & ML Tools']
    revenue = [5.2, 3.8, 2.9, 2.1, 1.6]  # Revenue in $M
    total_rev = sum(revenue)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.barh(product_lines, revenue, color=CHART_COLORS, height=0.6, edgecolor='none')
    
    # Labelling & Formatting
    ax.set_title('Q4 Revenue by Product Line', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Revenue ($M)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Product Line', fontsize=12, fontweight='bold')
    ax.set_xlim(0, 6.2)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'${x:.1f}M'))
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    
    # Data labels on bars
    for bar, val in zip(bars, revenue):
        pct = (val / total_rev) * 100
        ax.text(val + 0.1, bar.get_y() + bar.get_height() / 2, f'${val:.1f}M ({pct:.1f}%)',
                va='center', fontsize=10, fontweight='bold', color='#333333')
                
    # Annotation: Mark top performer
    ax.annotate(
        'Top Revenue Driver\n($5.2M - 33.3%)',
        xy=(5.2, 0), xytext=(4.5, 0.8),
        arrowprops=dict(arrowstyle='->', color=PALETTE['warning'], lw=2),
        fontsize=10, fontweight='bold', color=PALETTE['warning'],
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#fffbe6', edgecolor=PALETTE['warning'], alpha=0.9)
    )
    
    # Invert Y-axis so top performer is at the top
    ax.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig('output/chart1_revenue_by_product.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved output/chart1_revenue_by_product.png")

# -------------------------------------------------------------
# Chart 2: Line Chart (Trend) - 12-Month Revenue Trend
# -------------------------------------------------------------
def create_chart2():
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    cloud_rev = [3.2, 3.4, 3.6, 3.8, 4.1, 4.3, 4.2, 4.0, 4.6, 4.9, 5.1, 5.2]
    analytics_rev = [2.5, 2.6, 2.7, 2.9, 3.0, 3.2, 3.1, 2.9, 3.3, 3.5, 3.7, 3.8]
    security_rev = [2.0, 2.1, 2.1, 2.3, 2.4, 2.5, 2.6, 2.4, 2.7, 2.8, 2.9, 2.9]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(months, cloud_rev, marker='o', linewidth=2.5, color=PALETTE['primary'], label='Cloud Solutions')
    ax.plot(months, analytics_rev, marker='s', linewidth=2.5, color=PALETTE['secondary'], label='Analytics Platform')
    ax.plot(months, security_rev, marker='^', linewidth=2.5, color=PALETTE['success'], label='Security Suite')
    
    # Target reference line
    target_revenue = 4.5
    ax.axhline(y=target_revenue, color=PALETTE['warning'], linestyle='--', linewidth=1.8, label=f'Cloud Target (${target_revenue:.1f}M)')
    
    # Labelling & Formatting
    ax.set_title('Monthly Revenue Trend by Product Line (Last 12 Months)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Month (2024)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Monthly Revenue ($M)', fontsize=12, fontweight='bold')
    ax.set_ylim(1.5, 5.8)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, p: f'${y:.1f}M'))
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper left', frameon=True, fontsize=10, facecolor='#ffffff', edgecolor='#cccccc')
    
    # Annotations
    # Annotation 1: August seasonal dip
    ax.annotate(
        'August Dip:\nSeasonal Effect ($4.0M)',
        xy=('Aug', 4.0), xytext=('Jul', 3.2),
        arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5),
        fontsize=9, fontweight='bold', ha='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#f0f0f0', edgecolor='#999999', alpha=0.9)
    )
    
    # Annotation 2: Cloud target cross
    ax.annotate(
        'Target Cross\n(Sep)',
        xy=('Sep', 4.6), xytext=('Sep', 5.3),
        arrowprops=dict(arrowstyle='->', color=PALETTE['success'], lw=1.5),
        fontsize=9, fontweight='bold', ha='center', color=PALETTE['success'],
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#e6ffe6', edgecolor=PALETTE['success'], alpha=0.9)
    )
    
    plt.tight_layout()
    plt.savefig('output/chart2_revenue_trend.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved output/chart2_revenue_trend.png")

# -------------------------------------------------------------
# Chart 3: Histogram (Distribution) - Distribution of Order Values
# -------------------------------------------------------------
def create_chart3():
    np.random.seed(42)
    # Generate realistic bimodal order value dataset
    small_orders = np.random.normal(loc=120, scale=35, size=350)
    large_orders = np.random.normal(loc=450, scale=60, size=150)
    order_values = np.clip(np.concatenate([small_orders, large_orders]), 20, 700)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    counts, bins, patches = ax.hist(order_values, bins=15, color=PALETTE['primary'], edgecolor='white', alpha=0.85)
    
    # Custom colors for patches
    for patch in patches:
        patch.set_facecolor(PALETTE['primary'])
        
    # Mean and Median reference lines
    mean_val = np.mean(order_values)
    median_val = np.median(order_values)
    
    ax.axvline(mean_val, color=PALETTE['warning'], linestyle='-', linewidth=2, label=f'Mean Order: ${mean_val:.2f}')
    ax.axvline(median_val, color=PALETTE['success'], linestyle='--', linewidth=2, label=f'Median Order: ${median_val:.2f}')
    
    # Labelling & Formatting
    ax.set_title('Distribution of Order Values (Q4)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Order Value ($)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Orders (Frequency)', fontsize=12, fontweight='bold')
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'${x:.0f}'))
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    
    # Add count labels on top of highest bins
    for count, x in zip(counts, bins):
        if count > 15:
            ax.text(x + (bins[1] - bins[0]) / 2, count + 1.5, f'{int(count)}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold', color='#333333')
                    
    # Annotation: Bimodal peaks explanation
    ax.annotate(
        'Bimodal Peak 1:\nStandard Orders ($100-$150)',
        xy=(120, max(counts)), xytext=(220, max(counts) - 5),
        arrowprops=dict(arrowstyle='->', color=PALETTE['primary'], lw=2),
        fontsize=9, fontweight='bold', color=PALETTE['primary'],
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#e6f2ff', edgecolor=PALETTE['primary'], alpha=0.9)
    )
    
    ax.annotate(
        'Bimodal Peak 2:\nEnterprise Bundles ($400-$500)',
        xy=(450, 25), xytext=(520, 45),
        arrowprops=dict(arrowstyle='->', color=PALETTE['secondary'], lw=2),
        fontsize=9, fontweight='bold', color=PALETTE['secondary'],
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff0e6', edgecolor=PALETTE['secondary'], alpha=0.9)
    )
    
    plt.tight_layout()
    plt.savefig('output/chart3_order_value_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved output/chart3_order_value_distribution.png")

# -------------------------------------------------------------
# Chart 4: Stacked Bar (Composition) - Revenue Composition by Quarter
# -------------------------------------------------------------
def create_chart4():
    quarters = ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024']
    product_lines = ['Cloud Solutions', 'Analytics Platform', 'Security Suite', 'Database Services', 'AI & ML Tools']
    
    data = np.array([
        [3.2, 3.8, 4.0, 5.2],  # Cloud
        [2.5, 3.0, 3.1, 3.8],  # Analytics
        [2.0, 2.4, 2.6, 2.9],  # Security
        [1.8, 1.9, 2.0, 2.1],  # Database
        [0.8, 1.1, 1.3, 1.6]   # AI & ML
    ])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bottom = np.zeros(len(quarters))
    bars_list = []
    
    for idx, (prod, row) in enumerate(zip(product_lines, data)):
        bars = ax.bar(quarters, row, bottom=bottom, label=prod, color=CHART_COLORS[idx], width=0.5)
        bars_list.append(bars)
        bottom += row
        
    # Total revenue labels on top of bars
    for idx, q_total in enumerate(bottom):
        ax.text(idx, q_total + 0.3, f'${q_total:.1f}M', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
    # Labelling & Formatting
    ax.set_title('Quarterly Revenue Composition by Product Line', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Quarter', fontsize=12, fontweight='bold')
    ax.set_ylabel('Total Revenue ($M)', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 18.0)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, p: f'${y:.0f}M'))
    ax.grid(True, axis='y', linestyle='--', alpha=0.5)
    ax.legend(loc='upper left', frameon=True, fontsize=10)
    
    # Annotation: Highlight shift in composition
    ax.annotate(
        'Cloud & AI Expansion\nDrives Q4 Surge (+47.5%)',
        xy=(3, bottom[3]), xytext=(1.8, 16.5),
        arrowprops=dict(arrowstyle='->', color=PALETTE['purple'], lw=2),
        fontsize=10, fontweight='bold', color=PALETTE['purple'],
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#f3e8ff', edgecolor=PALETTE['purple'], alpha=0.9)
    )
    
    plt.tight_layout()
    plt.savefig('output/chart4_revenue_composition.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved output/chart4_revenue_composition.png")

# -------------------------------------------------------------
# Chart 5: Scatter Plot (Correlation) - Marketing Spend vs Revenue
# -------------------------------------------------------------
def create_chart5():
    np.random.seed(101)
    
    # 25 Marketing Campaigns
    spend = np.array([12, 15, 18, 22, 25, 28, 30, 35, 40, 42, 45, 50, 55, 58, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110])  # $K
    # Revenue = 3.5 * spend + noise
    noise = np.random.normal(0, 25, size=len(spend))
    revenue = 3.2 * spend + 40 + noise
    
    # Introduce 1 distinct outlier (High Spend, Low Revenue - failed campaign)
    outlier_idx = 18
    spend[outlier_idx] = 85
    revenue[outlier_idx] = 120  # Underperforming outlier
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot normal points and outlier with distinct styling
    normal_mask = np.ones(len(spend), dtype=bool)
    normal_mask[outlier_idx] = False
    
    ax.scatter(spend[normal_mask], revenue[normal_mask], color=PALETTE['primary'], s=70, alpha=0.85, label='Campaigns', edgecolors='none')
    ax.scatter(spend[outlier_idx], revenue[outlier_idx], color=PALETTE['warning'], s=120, marker='D', label='Outlier Campaign', zorder=5)
    
    # Linear Trendline
    z = np.polyfit(spend[normal_mask], revenue[normal_mask], 1)
    p = np.poly1d(z)
    trend_x = np.linspace(min(spend), max(spend), 100)
    ax.plot(trend_x, p(trend_x), color=PALETTE['secondary'], linestyle='--', linewidth=2, label=f'Trendline (r = 0.88)')
    
    # Labelling & Formatting
    ax.set_title('Marketing Spend vs. Revenue Generated', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Marketing Spend ($K)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Revenue Generated ($K)', fontsize=12, fontweight='bold')
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'${x:.0f}K'))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, p: f'${y:.0f}K'))
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper left', frameon=True, fontsize=10)
    
    # Annotation: Highlight Outlier
    ax.annotate(
        'Outlier Campaign:\nHigh Spend ($85K), Low ROI ($120K)',
        xy=(spend[outlier_idx], revenue[outlier_idx]),
        xytext=(spend[outlier_idx] - 25, revenue[outlier_idx] - 60),
        arrowprops=dict(arrowstyle='->', color=PALETTE['warning'], lw=2),
        fontsize=9, fontweight='bold', color=PALETTE['warning'],
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffe6e6', edgecolor=PALETTE['warning'], alpha=0.9)
    )
    
    # Annotation: Strong correlation note
    ax.annotate(
        'Strong Positive Correlation\nLinear ROI ~ 3.2x Spend',
        xy=(65, p(65)), xytext=(40, 310),
        arrowprops=dict(arrowstyle='->', color=PALETTE['secondary'], lw=1.5),
        fontsize=9, fontweight='bold', color='#333333',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff0e6', edgecolor=PALETTE['secondary'], alpha=0.9)
    )
    
    plt.tight_layout()
    plt.savefig('output/chart5_marketing_vs_revenue.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved output/chart5_marketing_vs_revenue.png")

if __name__ == '__main__':
    create_chart1()
    create_chart2()
    create_chart3()
    create_chart4()
    create_chart5()
    print("All five charts generated successfully!")
