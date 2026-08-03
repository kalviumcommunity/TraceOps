from __future__ import annotations

import os
import sys
import logging
import numpy as np
import pandas as pd

# Optional plotting setup (using non-interactive 'Agg' backend)
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

# Path definitions
RAW_DATA_PATH = "data/raw/customer_behavior_data.csv"
OUTPUT_DIR = "output"
HEATMAP_PLOT_PATH = os.path.join(OUTPUT_DIR, "segment_heatmap.png")
SUMMARY_TXT_PATH = os.path.join(OUTPUT_DIR, "segmentation_summary.txt")
LOG_FILE = os.path.join(OUTPUT_DIR, "segmentation.log")

# Ensure directories exist
os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Add console logging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)


def generate_behavior_data(filepath: str = RAW_DATA_PATH, n_samples: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic customer behavioral and segmentation dataset.
    
    Proportions:
    - Enterprise (5%): ~$150k LTV, 1% churn rate, ~1.5 tickets, ~650 days retention.
    - SMB (40%): ~$8k LTV, 12% churn rate, ~4.5 tickets, ~180 days retention.
    - Startup (55%): ~$2k LTV, 8% churn rate, ~2.8 tickets, ~240 days retention.
    
    Args:
        filepath: CSV file path to write to.
        n_samples: Total number of customer records.
        
    Returns:
        Generated pd.DataFrame.
    """
    logging.info(f"Generating synthetic customer behavior data at {filepath} ({n_samples} samples)")
    np.random.seed(42)
    
    segment_choices = ['Enterprise', 'SMB', 'Startup']
    segment_probs = [0.05, 0.40, 0.55]
    
    customer_types = np.random.choice(segment_choices, size=n_samples, p=segment_probs)
    
    ltvs = []
    churns = []
    support_tickets = []
    retention_days = []
    
    for ctype in customer_types:
        if ctype == 'Enterprise':
            ltv = np.random.normal(150000, 15000)
            churn = 1 if np.random.rand() < 0.01 else 0
            tickets = np.random.poisson(1.5)
            retention = np.random.normal(650, 100)
        elif ctype == 'SMB':
            ltv = np.random.normal(8000, 1000)
            churn = 1 if np.random.rand() < 0.12 else 0
            tickets = np.random.poisson(4.5)
            retention = np.random.normal(180, 40)
        else: # Startup
            ltv = np.random.normal(2000, 300)
            churn = 1 if np.random.rand() < 0.08 else 0
            tickets = np.random.poisson(2.8)
            retention = np.random.normal(240, 60)
            
        ltvs.append(round(max(100.0, ltv), 2))
        churns.append(churn)
        support_tickets.append(max(0, tickets))
        retention_days.append(max(30, int(retention)))
        
    df = pd.DataFrame({
        'customer_id': np.arange(10001, 10001 + n_samples),
        'customer_type': customer_types,
        'lifetime_value': ltvs,
        'churn': churns,
        'support_tickets': support_tickets,
        'retention_days': retention_days
    })
    
    df.to_csv(filepath, index=False)
    logging.info(f"Saved generated behavioral dataset with {len(df)} rows.")
    return df


def load_data(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Ingest customer behavioral data from CSV.
    
    Args:
        filepath: Path to the behavioral CSV file.
        
    Returns:
        pd.DataFrame.
    """
    logging.info(f"Loading customer behavior data from {filepath}")
    if not os.path.exists(filepath):
        generate_behavior_data(filepath)
    df = pd.read_csv(filepath)
    logging.info(f"Ingested {len(df)} customer records.")
    return df


def compute_segment_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 1: Group by customer segment and compute average lifetime value,
    churn rate, average support tickets, average retention days, and segment count.
    
    Args:
        df: Ingested customer DataFrame.
        
    Returns:
        pd.DataFrame: Aggregated segment metrics.
    """
    logging.info("--- Task 1: Computing Segment Metrics ---")
    segment_metrics = df.groupby('customer_type').agg({
        'lifetime_value': 'mean',
        'churn': 'mean',
        'support_tickets': 'mean',
        'retention_days': 'mean',
        'customer_id': 'count'
    })
    segment_metrics.columns = ['avg_ltv', 'churn_rate', 'avg_tickets', 'avg_retention', 'count']
    logging.info(f"\nComputed Segment Metrics:\n{segment_metrics}")
    return segment_metrics


def create_summary_statistics_table(segment_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Task 2: Format metrics with readable labels and rankings.
    
    Ranks segments by lifetime value (descending) and churn rate (ascending - lower churn is better rank).
    
    Args:
        segment_metrics: Raw segment metrics DataFrame.
        
    Returns:
        pd.DataFrame: Structured segment summary with ranks.
    """
    logging.info("--- Task 2: Creating Summary Statistics and Rankings ---")
    segment_summary = segment_metrics.copy()
    
    # Compute rankings
    segment_summary['ltv_rank'] = segment_summary['avg_ltv'].rank(ascending=False).astype(int)
    segment_summary['churn_rank'] = segment_summary['churn_rate'].rank(ascending=True).astype(int)
    
    # Format absolute values for display
    # Keep formatted copy separately or print it, since heatmap requires floats
    formatted_summary = pd.DataFrame(index=segment_summary.index)
    formatted_summary['avg_ltv_formatted'] = segment_summary['avg_ltv'].apply(lambda x: f"${x:,.2f}")
    formatted_summary['ltv_rank'] = segment_summary['ltv_rank']
    formatted_summary['churn_rate_formatted'] = segment_summary['churn_rate'].apply(lambda x: f"{x:.1%}")
    formatted_summary['churn_rank'] = segment_summary['churn_rank']
    formatted_summary['avg_tickets'] = segment_summary['avg_tickets'].apply(lambda x: f"{x:.2f}")
    formatted_summary['avg_retention_days'] = segment_summary['avg_retention'].apply(lambda x: f"{x:.1f}")
    formatted_summary['sample_count'] = segment_summary['count']
    
    logging.info(f"\nFormatted Segment Summary Statistics:\n{formatted_summary}")
    return segment_summary


def visualize_segments(segment_metrics: pd.DataFrame, output_path: str = HEATMAP_PLOT_PATH) -> None:
    """
    Task 3: Create visual comparison heatmap.
    
    Since metrics have vastly different ranges (LTV: up to 150k, churn: up to 12%, tickets: up to 4.5),
    we normalize metrics column-wise for color intensity mapping, but display actual raw values as labels.
    
    Args:
        segment_metrics: Segment metrics DataFrame.
        output_path: Path to save the heatmap PNG.
    """
    if not HAS_PLOTTING:
        logging.warning("Matplotlib/Seaborn not installed. Skipping visualization.")
        return
        
    logging.info("--- Task 3: Generating Visual Comparison Heatmap ---")
    
    # Select columns to plot
    cols = ['avg_ltv', 'churn_rate', 'avg_tickets']
    df_plot = segment_metrics[cols].copy()
    
    # Min-max scale each column for color mapping
    df_plot_scaled = (df_plot - df_plot.min()) / (df_plot.max() - df_plot.min() + 1e-9)
    
    # Define text annotations with raw formatted values
    annot_text = np.array([
        [f"${row['avg_ltv']:,.0f}", f"{row['churn_rate']:.1%}", f"{row['avg_tickets']:.2f}"]
        for _, row in df_plot.iterrows()
    ])
    
    plt.figure(figsize=(10, 5))
    sns.heatmap(
        df_plot_scaled,
        annot=annot_text,
        fmt="",
        cmap='RdYlGn',
        linewidths=0.8,
        cbar_kws={'label': 'Scaled Intensity (Min to Max)'}
    )
    
    # Adjust tick labels for clarity
    plt.title('Segment Behavioral Comparison Heatmap (Color Scaled)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Behavioral Metrics', fontsize=12)
    plt.ylabel('Customer Segment', fontsize=12)
    plt.xticks([0.5, 1.5, 2.5], ['Average LTV', 'Churn Rate', 'Avg Support Tickets'])
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logging.info(f"Saved segment comparison heatmap to {output_path}")


def generate_report(segment_metrics: pd.DataFrame, output_path: str = SUMMARY_TXT_PATH) -> str:
    """
    Task 4 & 5: Perform top/bottom analysis and generate business-facing strategy summary.
    
    Args:
        segment_metrics: Segment metrics DataFrame.
        output_path: Path to write the report.
        
    Returns:
        str: Formatted report text.
    """
    logging.info("--- Tasks 4 & 5: Generating Business-Facing Insights & Report ---")
    
    # Task 4: Top and Bottom Performer Analysis
    top_segment = segment_metrics['avg_ltv'].idxmax()
    top_value = segment_metrics.loc[top_segment, 'avg_ltv']
    
    high_churn = segment_metrics['churn_rate'].idxmax()
    high_churn_rate = segment_metrics.loc[high_churn, 'churn_rate']
    
    best_retention_segment = segment_metrics['avg_retention'].idxmax()
    best_retention_days = segment_metrics.loc[best_retention_segment, 'avg_retention']
    
    # Task 5: Business-Facing Insights (observed numbers mapped to recommendations)
    # Proportions (hard-coded estimates or computed directly)
    total_count = segment_metrics['count'].sum()
    ent_prob = segment_metrics.loc['Enterprise', 'count'] / total_count * 100
    smb_prob = segment_metrics.loc['SMB', 'count'] / total_count * 100
    startup_prob = segment_metrics.loc['Startup', 'count'] / total_count * 100
    
    report = f"""CUSTOMER BEHAVIORAL ANALYSIS & USER SEGMENTATION
===============================================

1. PERFORMANCE LEADERBOARD (TASKS 4)
------------------------------------
- HIGHEST VALUE SEGMENT: {top_segment.upper()} (Average LTV: ${top_value:,.2f})
- HIGHEST CHURN RISK SEGMENT: {high_churn.upper()} (Churn Rate: {high_churn_rate:.1%})
- BEST RETENTION LEADER: {best_retention_segment.upper()} (Average Retention: {best_retention_days:.1f} days)

2. STRATEGIC SEGMENT PLAYBOOKS (TASK 5)
---------------------------------------
ENTERPRISE ({ent_prob:.1f}% of base, ${segment_metrics.loc['Enterprise', 'avg_ltv']:,.0f} LTV, {segment_metrics.loc['Enterprise', 'churn_rate']:.1%} churn):
- Insight: This segment represents our high-value cornerstone with an extremely stable profile. Their low support ticket volume ({segment_metrics.loc['Enterprise', 'avg_tickets']:.1f} avg) and high retention ({segment_metrics.loc['Enterprise', 'avg_retention']:.0f} days) indicate outstanding product-market fit.
- Recommended Action: Maintain dedicated white-glove support, organize quarterly business reviews (QBRs), and design premium expansion pathways to drive cross-sell revenue.

SMB ({smb_prob:.1f}% of base, ${segment_metrics.loc['SMB', 'avg_ltv']:,.0f} LTV, {segment_metrics.loc['SMB', 'churn_rate']:.1%} churn):
- Insight: This segment is our primary leak, displaying critical churn risk coupled with heavy support burden ({segment_metrics.loc['SMB', 'avg_tickets']:.1f} tickets avg). Shorter retention ({segment_metrics.loc['SMB', 'avg_retention']:.0f} days) points to gaps in onboarding or pricing frustration.
- Recommended Action: Redesign onboarding flows, deploy automated churn warning triggers, and offer lower-cost self-service support options to reduce support costs.

STARTUP ({startup_prob:.1f}% of base, ${segment_metrics.loc['Startup', 'avg_ltv']:,.0f} LTV, {segment_metrics.loc['Startup', 'churn_rate']:.1%} churn):
- Insight: Startups represent our volume engine (largest count) with moderate value and moderate churn ({segment_metrics.loc['Startup', 'churn_rate']:.1%}). They are moderately active in support ({segment_metrics.loc['Startup', 'avg_tickets']:.1f} tickets).
- Recommended Action: Deliver digital-first education (webinars, knowledge base articles) and implement product-led growth (PLG) self-service upsell models to capture expansion as they scale.
"""
    with open(output_path, 'w') as f:
        f.write(report)
        
    logging.info(f"Saved strategy report to {output_path}")
    return report


def main() -> None:
    """Run the user segmentation analysis pipeline."""
    logging.info("=== STARTING BEHAVIORAL ANALYSIS & USER SEGMENTATION PIPELINE ===")
    
    # 1. Ingest Data
    df = load_data(RAW_DATA_PATH)
    
    # 2. Compute Segment Metrics (Task 1)
    segment_metrics = compute_segment_metrics(df)
    
    # 3. Create Summary Table & Ranks (Task 2)
    _ = create_summary_statistics_table(segment_metrics)
    
    # 4. Generate Visual Comparisons Heatmap (Task 3)
    visualize_segments(segment_metrics, HEATMAP_PLOT_PATH)
    
    # 5. Conduct Performer Analysis & Business Strategy Report (Task 4 & 5)
    report = generate_report(segment_metrics, SUMMARY_TXT_PATH)
    print("\n" + report)
    
    logging.info("=== BEHAVIORAL ANALYSIS & USER SEGMENTATION PIPELINE COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
