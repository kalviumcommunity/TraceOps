"""
Revenue Distribution Analysis Pipeline script.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

# Configure matplotlib for headless environment
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RAW_DATA_PATH = "data/raw/skewed_revenue_data.csv"
OUTPUT_DIR = "output"


def generate_skewed_data(filepath=RAW_DATA_PATH):
    """
    Generate synthetic revenue data with a mean of ~450 and skewness of ~2.5.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    np.random.seed(42)
    
    # lognormal parameters chosen to yield mean ~450 and skewness ~2.5
    mu, sigma = 5.95, 0.55
    revenue = np.random.lognormal(mean=mu, sigma=sigma, size=1000)
    
    df = pd.DataFrame({
        'customer_id': np.arange(1, 1001),
        'revenue': revenue
    })
    df.to_csv(filepath, index=False)
    print(f"[GENERATE] Created synthetic skewed revenue data at {filepath} (1000 rows)")


def load_data(filepath=RAW_DATA_PATH):
    """Load input dataset from CSV, generating it if missing."""
    if not os.path.exists(filepath):
        generate_skewed_data(filepath)
    df = pd.read_csv(filepath)
    print(f"[LOAD] Ingested {len(df)} records from {filepath}")
    return df


def analyze_distributions(df):
    """
    Execute Tasks 1 to 5 to analyze skewness, kurtosis, segments, and business decisions.
    """
    print("\n" + "=" * 60)
    print("RUNNING REVENUE DISTRIBUTION ANALYSIS PIPELINE")
    print("=" * 60)

    # Task 1: Distribution Plots (1 mark)
    print("\n--- Task 1: Distribution Plots ---")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Histogram
    axes[0].hist(df['revenue'], bins=50, edgecolor='black', alpha=0.8, color='#3F51B5')
    axes[0].set_title('Revenue Distribution (Histogram)', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Revenue', fontsize=10)
    axes[0].set_ylabel('Count', fontsize=10)
    axes[0].grid(axis='y', linestyle='--', alpha=0.7)

    # KDE
    df['revenue'].plot(kind='density', ax=axes[1], color='#FF5722', linewidth=2)
    axes[1].set_title('Revenue Distribution (KDE)', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Revenue', fontsize=10)
    axes[1].grid(axis='both', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plot_path = os.path.join(OUTPUT_DIR, 'revenue_distribution.png')
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"OK: Saved distribution plots to {plot_path}")

    # Task 2: Compute Skewness and Kurtosis (1 mark)
    print("\n--- Task 2: Compute Skewness and Kurtosis ---")
    skewness = stats.skew(df['revenue'])
    kurtosis = stats.kurtosis(df['revenue'])

    print(f"Skewness: {skewness:.2f}")
    print(f"Kurtosis: {kurtosis:.2f}")

    if abs(skewness) > 1:
        print("Highly skewed - use median not mean")
    if kurtosis > 3:
        print("Heavy tails - expect outliers")

    # Task 3: Identify Abnormal Patterns (1 mark)
    print("\n--- Task 3: Identify Abnormal Patterns ---")
    # Check for bimodality
    print("Descriptive Statistics:")
    print(df['revenue'].describe())

    # Percentiles show if distribution is bimodal
    percentiles = df['revenue'].quantile([0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
    print("\nPercentiles:")
    print(percentiles)

    # Task 4: Compare Segment Distributions (1 mark)
    print("\n--- Task 4: Compare Segment Distributions ---")
    # Split by high-value vs low-value
    high_value = df[df['revenue'] > df['revenue'].quantile(0.75)]
    low_value = df[df['revenue'] < df['revenue'].quantile(0.25)]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Histograms
    axes[0].hist(high_value['revenue'], bins=30, alpha=0.7, label='High-Value', color='#4CAF50', edgecolor='black')
    axes[0].hist(low_value['revenue'], bins=30, alpha=0.7, label='Low-Value', color='#9E9E9E', edgecolor='black')
    axes[0].legend(fontsize=10)
    axes[0].set_title('Revenue Histograms: High vs Low Value', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Revenue', fontsize=10)
    axes[0].set_ylabel('Count', fontsize=10)
    axes[0].grid(axis='y', linestyle='--', alpha=0.7)

    # Densities/KDE
    high_value['revenue'].plot(kind='density', ax=axes[1], color='#4CAF50', label='High-Value Density', linewidth=2)
    low_value['revenue'].plot(kind='density', ax=axes[1], color='#9E9E9E', label='Low-Value Density', linewidth=2)
    axes[1].legend(fontsize=10)
    axes[1].set_title('Revenue Densities (KDE): High vs Low Value', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Revenue', fontsize=10)
    axes[1].grid(axis='both', linestyle='--', alpha=0.7)

    plt.tight_layout()
    segment_plot_path = os.path.join(OUTPUT_DIR, 'segment_comparison.png')
    plt.savefig(segment_plot_path, dpi=300)
    plt.close()
    print(f"OK: Saved segment comparison plots to {segment_plot_path}")

    # Compare metrics
    print(f"High-value: mean={high_value['revenue'].mean():.0f}, median={high_value['revenue'].median():.0f}")
    print(f"Low-value: mean={low_value['revenue'].mean():.0f}, median={low_value['revenue'].median():.0f}")

    # Task 5: Business Interpretation (1 mark)
    print("\n--- Task 5: Business Interpretation ---")
    interpretation = f"""
Revenue Distribution Analysis:

Skewness: {skewness:.2f} → {"Highly right-skewed" if skewness > 1 else "Moderate"}
Mean: ${df['revenue'].mean():.0f}
Median: ${df['revenue'].median():.0f}
Interpretation: {'Most customers are small; few are huge enterprise accounts' if skewness > 1 else 'Balanced distribution'}

Kurtosis: {kurtosis:.2f} → {"Fat tails (outliers)" if kurtosis > 3 else "Normal"}
Max: ${df['revenue'].max():.0f}
Top 1%: ${df['revenue'].quantile(0.99):.0f}

Business Action: {'Segment into small/enterprise for different strategies' if skewness > 1 else 'Uniform strategy'}
"""
    print(interpretation)
    return skewness, kurtosis, percentiles


def main():
    # Force stdout/stderr to use UTF-8 on Windows to prevent UnicodeEncodeError
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    df = load_data()
    analyze_distributions(df)


if __name__ == "__main__":
    main()
