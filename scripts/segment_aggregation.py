"""
Segment Aggregation & GroupBy Insights Script.

This script implements customer segment analysis using pandas GroupBy operations:
1. Single-level GroupBy with multiple aggregations (churn rate, total revenue, customer count, avg support tickets).
2. Multi-level GroupBy across customer type and product.
3. Pivot table creation for multi-dimensional revenue visualization.
4. Segment ranking by churn rate and revenue contribution percentage.
5. Actionable segment insights generation with automated recommendations.
"""

import os
import sys
import json
import numpy as np
import pandas as pd

RAW_DATA_PATH = "data/raw/customer_segment_data.csv"
OUTPUT_DIR = "output"
INSIGHTS_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "segment_insights.csv")
SUMMARY_JSON_PATH = os.path.join(OUTPUT_DIR, "segment_summary.json")


def generate_segment_data(filepath: str = RAW_DATA_PATH, n_samples: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic customer segment dataset reflecting real-world distributions:
    - Enterprise (5% base): ~1% churn, ~70% revenue contribution
    - SMB (40% base): ~12% churn, low revenue
    - Startup (55% base): ~8% churn, medium revenue
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    np.random.seed(42)

    # Segment proportions: 5% Enterprise, 40% SMB, 55% Startup
    segment_choices = ['Enterprise', 'SMB', 'Startup']
    segment_probs = [0.05, 0.40, 0.55]
    
    customer_types = np.random.choice(segment_choices, size=n_samples, p=segment_probs)
    
    products = []
    churns = []
    revenues = []
    support_tickets = []
    
    for ctype in customer_types:
        if ctype == 'Enterprise':
            # Churn rate ~ 1%
            churn = 1 if np.random.rand() < 0.01 else 0
            # Revenue ~ 14000 per customer
            rev = max(5000.0, np.random.normal(14000, 2000))
            tickets = max(0, int(np.random.poisson(1.2)))
            prod = np.random.choice(['Enterprise Suite', 'Analytics Pro'], p=[0.7, 0.3])
        elif ctype == 'SMB':
            # Churn rate ~ 12%
            churn = 1 if np.random.rand() < 0.12 else 0
            # Revenue ~ 500 per customer
            rev = max(50.0, np.random.normal(500, 100))
            tickets = max(0, int(np.random.poisson(4.5)))
            prod = np.random.choice(['Basic Tier', 'Cloud API', 'Analytics Pro'], p=[0.5, 0.3, 0.2])
        else:  # Startup
            # Churn rate ~ 8%
            churn = 1 if np.random.rand() < 0.08 else 0
            # Revenue ~ 180 per customer
            rev = max(30.0, np.random.normal(180, 40))
            tickets = max(0, int(np.random.poisson(2.8)))
            prod = np.random.choice(['Cloud API', 'Basic Tier', 'Analytics Pro'], p=[0.5, 0.3, 0.2])
            
        churns.append(churn)
        revenues.append(round(rev, 2))
        support_tickets.append(tickets)
        products.append(prod)
        
    df = pd.DataFrame({
        'customer_id': np.arange(1, n_samples + 1),
        'customer_type': customer_types,
        'product': products,
        'churn': churns,
        'revenue': revenues,
        'support_tickets': support_tickets
    })
    
    df.to_csv(filepath, index=False)
    print(f"[GENERATE] Created synthetic segment dataset at {filepath} ({n_samples} rows)")
    return df


def load_data(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Load dataset from CSV, generating synthetic data if missing.
    """
    if not os.path.exists(filepath):
        generate_segment_data(filepath)
    df = pd.read_csv(filepath)
    print(f"[LOAD] Ingested {len(df)} records from {filepath}")
    return df


def single_level_groupby(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 1: Compute single-level GroupBy with multiple aggregations.
    """
    print("\n--- Task 1: Single-Level GroupBy with Multiple Aggregations ---")
    segment_metrics = df.groupby('customer_type').agg({
        'churn': 'mean',
        'revenue': 'sum',
        'customer_id': 'count',
        'support_tickets': 'mean'
    })

    segment_metrics.columns = ['churn_rate', 'total_revenue', 'customer_count', 'avg_support_tickets']
    print(segment_metrics)
    return segment_metrics


def multi_level_groupby(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Task 2: Compute multi-level GroupBy and unstack for pivot view.
    """
    print("\n--- Task 2: Multi-Level GroupBy ---")
    # Two dimensions simultaneously
    product_segment = df.groupby(['customer_type', 'product']).agg({
        'revenue': 'sum',
        'customer_id': 'count'
    })

    product_segment.columns = ['total_revenue', 'customer_count']

    # Unstack for cleaner view
    product_segment_pivot = product_segment.unstack()
    print(product_segment_pivot)
    return product_segment, product_segment_pivot


def create_pivot_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 3: Compute Pivot Table for two-dimensional view.
    """
    print("\n--- Task 3: Pivot Table ---")
    # Two-dimensional view: customer_type rows, product columns
    pivot = pd.pivot_table(
        df,
        values='revenue',
        index='customer_type',
        columns='product',
        aggfunc='sum'
    )

    print(pivot)
    return pivot


def rank_and_identify_performers(segment_metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Task 4: Rank segments by churn rate and compute revenue contribution percentage.
    """
    print("\n--- Task 4: Rank and Identify Top/Bottom Performers ---")
    segment_metrics = segment_metrics.copy()
    
    # Rank segments by churn
    segment_metrics['churn_rank'] = segment_metrics['churn_rate'].rank()

    # Sort to see worst first
    worst_first = segment_metrics.sort_values('churn_rate', ascending=False)
    print("Worst first:")
    print(worst_first)

    # Profit/revenue ranking
    segment_metrics['revenue_contribution'] = (
        segment_metrics['total_revenue'] / segment_metrics['total_revenue'].sum() * 100
    )
    print("\nRevenue contribution vs Churn rate:")
    print(segment_metrics[['revenue_contribution', 'churn_rate']])
    
    return segment_metrics, worst_first


def surface_actionable_insights(segment_metrics: pd.DataFrame, output_path: str = INSIGHTS_OUTPUT_PATH) -> pd.DataFrame:
    """
    Task 5: Surface actionable segment insights and save summary to CSV.
    """
    print("\n--- Task 5: Surface Actionable Segment Insights ---")
    insights = []

    for segment in segment_metrics.index:
        row = segment_metrics.loc[segment]
        
        insight = {
            'segment': segment,
            'customer_count': int(row['customer_count']),
            'churn_rate': f"{row['churn_rate']:.1%}",
            'total_revenue': f"${row['total_revenue']:.0f}",
            'revenue_contribution': f"{row['revenue_contribution']:.1f}%",
            'action': ''
        }
        
        # Action based on metrics
        if row['churn_rate'] > 0.10:
            insight['action'] = 'HIGH PRIORITY: Churn above 10%. Investigate pain points.'
        elif row['churn_rate'] < 0.02:
            insight['action'] = 'Healthy. Maintain current service level.'
        else:
            insight['action'] = 'Monitor. No immediate action needed.'
        
        insights.append(insight)

    insights_df = pd.DataFrame(insights)
    print(insights_df.to_string(index=False))
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    insights_df.to_csv(output_path, index=False)
    print(f"\n[SAVE] Saved segment insights to {output_path}")
    return insights_df


def run_segment_analysis(filepath: str = RAW_DATA_PATH) -> dict:
    """
    Orchestrate full segment aggregation and insight analysis pipeline.
    """
    df = load_data(filepath)
    segment_metrics = single_level_groupby(df)
    product_segment, product_segment_pivot = multi_level_groupby(df)
    pivot = create_pivot_table(df)
    ranked_metrics, worst_first = rank_and_identify_performers(segment_metrics)
    insights_df = surface_actionable_insights(ranked_metrics)
    
    summary = {
        'total_customers': int(len(df)),
        'total_revenue': float(df['revenue'].sum()),
        'overall_churn_rate': float(df['churn'].mean()),
        'segment_count': int(len(segment_metrics))
    }
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(SUMMARY_JSON_PATH, 'w') as f:
        json.dump(summary, f, indent=2)
        
    return {
        'segment_metrics': ranked_metrics,
        'product_segment_pivot': product_segment_pivot,
        'pivot': pivot,
        'worst_first': worst_first,
        'insights_df': insights_df,
        'summary': summary
    }


if __name__ == "__main__":
    run_segment_analysis()
