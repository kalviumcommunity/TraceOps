"""
Correlation and Relationship Analysis Pipeline script.

This script implements churn model relationship discovery:
1. Computing Pearson and Spearman correlation matrices and comparing them.
2. Visualizing the feature correlation matrix with a heatmap.
3. Identifying strongly correlated feature pairs (|r| > 0.7).
4. Business interpretation and reasoning about direction of causation (avoiding correlation=causation trap).
5. Performing feature selection based on redundancy to improve model interpretability.
"""

import json
import os
import sys
import numpy as np
import pandas as pd

# Configure matplotlib for headless environment
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

RAW_DATA_PATH = "data/raw/churn_correlation_data.csv"
OUTPUT_DIR = "output"
HEATMAP_PATH = os.path.join(OUTPUT_DIR, "correlation_heatmap.png")


def generate_churn_data(filepath: str = RAW_DATA_PATH, n_samples: int = 1000) -> None:
    """
    Generate synthetic churn dataset with specified correlations:
    - support_tickets <-> churn (r ≈ 0.80)
    - transactions_per_month <-> engagement (r ≈ 0.92)
    - satisfaction_score with non-linear relationship (Pearson vs Spearman difference)
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    np.random.seed(42)

    # Base latent variables
    customer_pain = np.random.normal(0, 1, n_samples)
    usage = np.random.normal(10, 3, n_samples)

    # Generated features based on latent variables
    churn = (customer_pain + np.random.normal(0, 0.4, n_samples) > 0.3).astype(int)
    support_tickets = np.round(np.maximum(0, 5 + 3.5 * customer_pain + np.random.normal(0, 0.8, n_samples))).astype(int)

    transactions_per_month = np.maximum(1, np.round(usage + np.random.normal(0, 0.5, n_samples))).astype(int)
    engagement = np.maximum(0.0, 0.92 * transactions_per_month + np.random.normal(0, 1.2, n_samples))

    # Satisfaction score (exponential relationship creating Pearson/Spearman difference)
    satisfaction_score = np.exp(-0.5 * customer_pain) + np.random.normal(0, 0.2, n_samples)

    df = pd.DataFrame({
        'customer_id': np.arange(1, n_samples + 1),
        'engagement': engagement,
        'transactions_per_month': transactions_per_month,
        'support_tickets': support_tickets,
        'satisfaction_score': satisfaction_score,
        'churn': churn
    })

    df.to_csv(filepath, index=False)
    print(f"[GENERATE] Created synthetic churn dataset at {filepath} ({n_samples} rows)")


def load_data(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Load dataset from CSV, generating synthetic data if missing.
    """
    if not os.path.exists(filepath):
        generate_churn_data(filepath)
    df = pd.read_csv(filepath)
    print(f"[LOAD] Ingested {len(df)} records from {filepath}")
    return df


def compute_correlations(df: pd.DataFrame) -> tuple:
    """
    Task 1: Compute Pearson and Spearman correlation matrices, and compare correlations with churn.
    """
    print("\n--- Task 1: Compute Pearson and Spearman Correlation ---")
    # Filter numerical columns excluding customer_id
    numeric_cols = [col for col in df.columns if col != 'customer_id' and pd.api.types.is_numeric_dtype(df[col])]
    df_num = df[numeric_cols]

    # Pearson (linear relationships)
    pearson_corr = df_num.corr(method='pearson')

    # Spearman (monotonic, robust to outliers)
    spearman_corr = df_num.corr(method='spearman')

    # Compare which correlations differ for 'churn'
    comparison = pd.DataFrame({
        'pearson': pearson_corr['churn'],
        'spearman': spearman_corr['churn']
    })
    print("Comparison of Pearson vs Spearman correlation with churn:")
    print(comparison)

    return pearson_corr, spearman_corr, comparison


def visualize_correlation_heatmap(pearson_corr: pd.DataFrame, output_path: str = HEATMAP_PATH) -> None:
    """
    Task 2: Visualize correlation heatmap and save to output directory.
    """
    print("\n--- Task 2: Visualize Correlation Heatmap ---")
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(pearson_corr, annot=True, cmap='coolwarm', center=0, ax=ax)
    ax.set_title('Feature Correlation Matrix')
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"OK: Saved correlation heatmap to {output_path}")


def identify_strong_correlations(pearson_corr: pd.DataFrame, threshold: float = 0.7, top_n: int = 10) -> pd.Series:
    """
    Task 3: Flatten correlation matrix and identify strongly correlated pairs (|r| > 0.7).
    """
    print("\n--- Task 3: Identify Strongly Correlated Pairs ---")
    # Flatten and find strong correlations
    corr_flat = pearson_corr.unstack()
    strong = corr_flat[corr_flat.abs() > threshold].sort_values(ascending=False)

    # Exclude self-correlation (r=1.0)
    strong_pairs = strong[strong != 1.0].head(top_n)
    print(f"Top strong correlation pairs (|r| > {threshold}):")
    print(strong_pairs)

    return strong_pairs


def analyze_business_causation(support_tickets_churn_corr: float = 0.8) -> dict:
    """
    Task 4: Business Interpretation - Reason about causation direction vs correlation.
    """
    print("\n--- Task 4: Business Interpretation ---")
    analysis = {
        'support_tickets <-> churn': {
            'correlation': float(support_tickets_churn_corr),
            'possible_directions': [
                'support_tickets → churn (customer gives up after contacting support)',
                'churn → support_tickets (unhappy customers contact support before leaving)',
                'customer_pain → both (underlying issue causes both)'
            ],
            'data_indicates': 'Likely customer_pain is the confounder; tickets are symptom not cause',
            'action': 'Focus on reducing pain, not blocking tickets'
        }
    }

    print(json.dumps(analysis, indent=2))
    return analysis


def perform_feature_selection(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 5: Feature Selection Based on Correlation.
    Drop redundant highly-correlated features to retain interpretable features.
    """
    print("\n--- Task 5: Feature Selection Based on Correlation ---")
    # High correlation means redundancy - keep more interpretable feature
    df_features = df[['engagement', 'transactions_per_month', 'support_tickets', 'churn']]

    # transactions_per_month and engagement are r ≈ 0.92 (correlated)
    # Drop redundant, keep interpretable
    df_features = df_features.drop('engagement', axis=1)

    selected_corr = df_features.corr()
    print("Correlation matrix after feature selection:")
    print(selected_corr)

    return df_features


def analyze_correlations(df: pd.DataFrame) -> tuple:
    """
    Execute Tasks 1 to 5 for correlation & relationship analysis.
    """
    print("\n" + "=" * 60)
    print("RUNNING CORRELATION & RELATIONSHIP ANALYSIS PIPELINE")
    print("=" * 60)

    # Task 1
    pearson_corr, spearman_corr, comparison = compute_correlations(df)

    # Task 2
    visualize_correlation_heatmap(pearson_corr, HEATMAP_PATH)

    # Task 3
    strong_pairs = identify_strong_correlations(pearson_corr, threshold=0.7)

    # Task 4
    support_tickets_corr = pearson_corr.loc['support_tickets', 'churn'] if ('support_tickets' in pearson_corr.index and 'churn' in pearson_corr.columns) else 0.8
    analysis = analyze_business_causation(round(support_tickets_corr, 2))

    # Task 5
    selected_features = perform_feature_selection(df)

    return pearson_corr, spearman_corr, strong_pairs, analysis, selected_features


def main():
    # Force stdout/stderr to use UTF-8 on Windows
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    df = load_data()
    analyze_correlations(df)


if __name__ == "__main__":
    main()
