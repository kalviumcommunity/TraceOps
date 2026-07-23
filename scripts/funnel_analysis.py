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
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

# Path definitions
RAW_DATA_PATH = "data/raw/funnel_data.csv"
OUTPUT_DIR = "output"
FUNNEL_PLOT_PATH = os.path.join(OUTPUT_DIR, "funnel_chart.png")
SUMMARY_TXT_PATH = os.path.join(OUTPUT_DIR, "funnel_analysis.txt")
LOG_FILE = os.path.join(OUTPUT_DIR, "funnel.log")

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


def generate_funnel_data(filepath: str = RAW_DATA_PATH, total_users: int = 10000) -> pd.DataFrame:
    """
    Generate synthetic sequential funnel data.
    
    Target Counts:
    - Sign Up (stage1): 10,000 users
    - Email Entered (stage2): 8,000 users
    - Password Created (stage3): 6,000 users
    - Email Verified (stage4): 5,000 users
    - Payment Added (stage5): 4,000 users
    - First Purchase (stage6): 2,000 users
    
    Args:
        filepath: CSV file path to write to.
        total_users: Number of baseline users.
        
    Returns:
        Generated pd.DataFrame.
    """
    logging.info(f"Generating synthetic funnel data at {filepath}")
    
    # We construct a sequential dataset where users are mapped to their furthest completed stage:
    # 2000 users reach First Purchase (all stages = 1)
    # 2000 users reach Payment Added (stages 1-5 = 1, stage6 = 0)
    # 1000 users reach Email Verified (stages 1-4 = 1, stages 5-6 = 0)
    # 1000 users reach Password Created (stages 1-3 = 1, stages 4-6 = 0)
    # 2000 users reach Email Entered (stages 1-2 = 1, stages 3-6 = 0)
    # 2000 users reach Sign Up (stage1 = 1, stages 2-6 = 0)
    
    stage1 = np.zeros(total_users, dtype=int)
    stage2 = np.zeros(total_users, dtype=int)
    stage3 = np.zeros(total_users, dtype=int)
    stage4 = np.zeros(total_users, dtype=int)
    stage5 = np.zeros(total_users, dtype=int)
    stage6 = np.zeros(total_users, dtype=int)
    
    # Fill based on sequence limits
    # First Purchase (2,000)
    stage1[0:2000] = 1
    stage2[0:2000] = 1
    stage3[0:2000] = 1
    stage4[0:2000] = 1
    stage5[0:2000] = 1
    stage6[0:2000] = 1
    
    # Payment Added (additional 2,000 -> cumulative 4,000)
    stage1[2000:4000] = 1
    stage2[2000:4000] = 1
    stage3[2000:4000] = 1
    stage4[2000:4000] = 1
    stage5[2000:4000] = 1
    
    # Email Verified (additional 1,000 -> cumulative 5,000)
    stage1[4000:5000] = 1
    stage2[4000:5000] = 1
    stage3[4000:5000] = 1
    stage4[4000:5000] = 1
    
    # Password Created (additional 1,000 -> cumulative 6,000)
    stage1[5000:6000] = 1
    stage2[5000:6000] = 1
    stage3[5000:6000] = 1
    
    # Email Entered (additional 2,000 -> cumulative 8,000)
    stage1[6000:8000] = 1
    stage2[6000:8000] = 1
    
    # Sign Up completed (additional 2,000 -> cumulative 10,000)
    stage1[8000:10000] = 1
    
    df = pd.DataFrame({
        'user_id': np.arange(100001, 100001 + total_users),
        'signup_completed': stage1,
        'email_entered': stage2,
        'password_created': stage3,
        'email_verified': stage4,
        'payment_added': stage5,
        'first_purchase': stage6
    })
    
    df.to_csv(filepath, index=False)
    logging.info(f"Successfully generated sequential funnel CSV at {filepath}")
    return df


def load_data(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Ingest raw funnel data.
    
    Args:
        filepath: CSV path.
        
    Returns:
        pd.DataFrame.
    """
    logging.info(f"Loading funnel data from {filepath}")
    if not os.path.exists(filepath):
        generate_funnel_data(filepath)
    df = pd.read_csv(filepath)
    logging.info(f"Ingested {len(df)} user sessions.")
    return df


def compute_funnel_stages(df: pd.DataFrame) -> dict[str, int]:
    """
    Task 1: Track user counts through each sequential step.
    
    Args:
        df: Ingested DataFrame.
        
    Returns:
        dict: Stage name mapping to user counts.
    """
    logging.info("--- Task 1: Tracking Funnel Volumes ---")
    stage1_signup = len(df[df['signup_completed'] == 1])
    stage2_email = len(df[df['email_entered'] == 1])
    stage3_password = len(df[df['password_created'] == 1])
    stage4_verified = len(df[df['email_verified'] == 1])
    stage5_payment = len(df[df['payment_added'] == 1])
    stage6_purchase = len(df[df['first_purchase'] == 1])

    stages = {
        'Sign Up': stage1_signup,
        'Email Entered': stage2_email,
        'Password Created': stage3_password,
        'Email Verified': stage4_verified,
        'Payment Added': stage5_payment,
        'First Purchase': stage6_purchase
    }
    
    # Assert sequential progression (each step should have fewer or equal users than the previous)
    stage_values = list(stages.values())
    for i in range(len(stage_values) - 1):
        assert stage_values[i] >= stage_values[i+1], (
            f"Funnel is non-sequential: {list(stages.keys())[i]} ({stage_values[i]}) has fewer users "
            f"than {list(stages.keys())[i+1]} ({stage_values[i+1]})"
        )
        
    logging.info(f"Funnel progression verified. Stage counts: {stages}")
    return stages


def compute_drop_offs(stages: dict[str, int]) -> pd.DataFrame:
    """
    Task 2: Compute drop-off and completion rates between consecutive steps.
    
    Args:
        stages: Dictionary of user counts per stage.
        
    Returns:
        pd.DataFrame: Tabular drop-off details.
    """
    logging.info("--- Task 2: Calculating Drop-offs and Completion Rates ---")
    stage_list = list(stages.values())
    stage_names = list(stages.keys())

    drop_off = []
    for i in range(len(stage_list) - 1):
        users_before = stage_list[i]
        users_after = stage_list[i+1]
        users_lost = users_before - users_after
        drop_pct = (users_lost / users_before) * 100
        completion_pct = (users_after / users_before) * 100
        
        drop_off.append({
            'from_stage': stage_names[i],
            'to_stage': stage_names[i+1],
            'users_before': users_before,
            'users_after': users_after,
            'users_lost': users_lost,
            'completion_rate': completion_pct,
            'drop_rate': drop_pct
        })

    funnel_df = pd.DataFrame(drop_off)
    logging.info(f"\nDrop-off Metrics:\n{funnel_df[['from_stage', 'to_stage', 'users_lost', 'completion_rate', 'drop_rate']]}")
    
    # Identify the highest drop-off rate
    biggest_drop_rate_row = funnel_df.loc[funnel_df['drop_rate'].idxmax()]
    logging.info(f"Highest Drop-off Rate: {biggest_drop_rate_row['from_stage']} -> {biggest_drop_rate_row['to_stage']} ({biggest_drop_rate_row['drop_rate']:.1f}%)")
    
    return funnel_df


def visualize_funnel(stages: dict[str, int], output_path: str = FUNNEL_PLOT_PATH) -> None:
    """
    Task 3: Visual Funnel chart.
    
    Args:
        stages: Funnel stage user counts.
        output_path: Filepath to save visualization PNG.
    """
    if not HAS_PLOTTING:
        logging.warning("Matplotlib is not installed. Skipping plot creation.")
        return
        
    logging.info("--- Task 3: Generating Visual Funnel Chart ---")
    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
    bars = ax.bar(stages.keys(), stages.values(), color=colors, edgecolor='black', alpha=0.85)

    ax.set_ylabel('Active Users', fontsize=12, fontweight='bold')
    ax.set_xlabel('Funnel Stages', fontsize=12, fontweight='bold')
    ax.set_title('Signup Funnel Analysis: Volume & Progression', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylim(0, max(stages.values()) * 1.15)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    # Annotate counts and percentages of base
    base_val = list(stages.values())[0]
    for bar in bars:
        height = bar.get_height()
        pct_of_base = (height / base_val) * 100
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{int(height):,}\n({pct_of_base:.1f}%)",
            ha='center',
            va='bottom',
            fontweight='bold',
            fontsize=10
        )

    plt.xticks(rotation=15, fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logging.info(f"Saved funnel chart to {output_path}")


def calculate_business_impact(funnel_df: pd.DataFrame, revenue_per_customer: float = 100.0) -> pd.DataFrame:
    """
    Task 4: Calculate monetary impact of users lost at each step.
    
    Formula: revenue_lost = users_lost * revenue_per_customer
    
    Args:
        funnel_df: Drop-off DataFrame.
        revenue_per_customer: Lifetime value value per customer.
        
    Returns:
        pd.DataFrame: Ranked impact analysis.
    """
    logging.info("--- Task 4: Modeling Business Impact of Drop-offs ---")
    impact_analysis = []
    for idx, row in funnel_df.iterrows():
        users_lost = row['users_lost']
        revenue_lost = users_lost * revenue_per_customer
        # Priority thresholds: High if revenue lost > $100,000, else Medium
        priority = 'HIGH' if revenue_lost > 100000 else 'MEDIUM'
        
        impact_analysis.append({
            'drop_point': f"{row['from_stage']} -> {row['to_stage']}",
            'users_lost': int(users_lost),
            'revenue_lost_val': revenue_lost,
            'revenue_impact': f"${revenue_lost:,.0f}",
            'priority': priority,
            'drop_rate_val': row['drop_rate']
        })

    impact_df = pd.DataFrame(impact_analysis)
    # Rank by business impact (revenue lost descending, then drop rate descending as tie breaker)
    impact_df = impact_df.sort_values(['revenue_lost_val', 'drop_rate_val'], ascending=[False, False]).reset_index(drop=True)
    
    logging.info(f"\nRanked Business Impact of Drop-offs:\n{impact_df[['drop_point', 'users_lost', 'revenue_impact', 'priority']]}")
    return impact_df


def generate_recommendation_report(funnel_df: pd.DataFrame, impact_df: pd.DataFrame, revenue_per_customer: float = 100.0, output_path: str = SUMMARY_TXT_PATH) -> str:
    """
    Task 5: Identify the highest priority bottleneck, explain why, outline hypotheses, and estimate impact.
    
    Args:
        funnel_df: Drop-off DataFrame.
        impact_df: Ranked business impact DataFrame.
        revenue_per_customer: Value per customer.
        output_path: Path to save txt report.
        
    Returns:
        str: Recommendations text.
    """
    logging.info("--- Task 5: Formulating Actionable Optimization Strategy ---")
    
    # The highest impact drop-point by absolute users lost:
    highest_impact_row = impact_df.iloc[0]
    drop_point_name = highest_impact_row['drop_point']
    from_stage, to_stage = drop_point_name.split(" -> ")
    
    # Retrieve the drop rate and completion rate from funnel_df for this stage
    stage_metrics = funnel_df[(funnel_df['from_stage'] == from_stage) & (funnel_df['to_stage'] == to_stage)].iloc[0]
    users_lost = stage_metrics['users_lost']
    drop_rate = stage_metrics['drop_rate']
    revenue_lost = highest_impact_row['revenue_lost_val']
    
    # Formulate playbooks and recommendations
    report = f"""FUNNEL OPTIMIZATION & DROP-OFF DETECTION REPORT
================================================

1. EXECUTIVE LEADERBOARD (BUSINESS IMPACT RANKING)
-------------------------------------------------
We assign a baseline Customer Lifetime Value (LTV) of ${revenue_per_customer:,.0f} per completed checkout.
Below is the ranked breakdown of revenue leaks across each transition step:

"""
    for idx, row in impact_df.iterrows():
        report += f"Rank {idx+1}: {row['drop_point']}\n"
        report += f"  - Users Lost: {row['users_lost']:,}\n"
        report += f"  - Revenue Lost: {row['revenue_impact']}\n"
        report += f"  - Intervention Priority: {row['priority']}\n\n"
        
    report += f"""2. CRITICAL BOTTLENECK ANALYSIS
--------------------------------
The single highest-priority leak in our signup flow is:
* Stage: {drop_point_name}
* Absolute Users Lost: {users_lost:,.0f}
* Drop Rate: {drop_rate:.1f}%
* Monthly Revenue Impact: ${revenue_lost:,.0f}

Why this occurs:
- The drop-off from {from_stage} to {to_stage} represents a 50% leakage rate. Although payment credentials have been added, users fail to execute their first transaction.
- Primary Hypotheses:
  1. High friction on checkout: Checkout page loading latency or buggy credit card validation forms.
  2. Hidden charges: Unexplained shipping fees, tax markups, or service charges revealed only at checkout.
  3. Lack of motivation: Absence of immediate incentives (e.g., first-purchase discount code) or trust badges to prompt closure.

3. ACTIONABLE STRATEGY & Measurable success criteria
----------------------------------------------------
- Suggested Interventions:
  1. Simplify Checkout UX: Reduce payment form fields to the absolute minimum and deploy one-click express payment methods (e.g. Apple Pay, Google Pay).
  2. Incentive Integration: Send an automated email / SMS reminder within 15 minutes of payment method addition offering a 10% first-purchase coupon.
  3. Pricing Transparency: Display all taxes and shipping costs upfront at the signup stage rather than hiding them until the final screen.

- Expected Business Impact:
  If we successfully optimize the completion rate of the {drop_point_name} transition by 10% (moving the rate from 50% to 55%):
  * Additional conversions recovered: {int(users_lost * 0.1):,} customers.
  * Monthly Revenue Recovery: ${int(users_lost * 0.1 * revenue_per_customer):,.0f}.

- Success Criteria:
  1. A/B test the simplified checkout layout against the current baseline.
  2. Validate that the {from_stage} to {to_stage} completion rate increases by at least 5% within 14 days of launch.
  3. Verify that overall funnel conversion increases from 20% to 22%+.
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
        
    logging.info(f"Saved recommendation report to {output_path}")
    return report


def main() -> None:
    """Run the complete funnel analysis pipeline."""
    logging.info("=== STARTING SIGNUP FUNNEL ANALYSIS PIPELINE ===")
    
    # 1. Ingest Data
    df = load_data(RAW_DATA_PATH)
    
    # 2. Count Users (Task 1)
    stages = compute_funnel_stages(df)
    
    # 3. Compute Drop-Offs (Task 2)
    funnel_df = compute_drop_offs(stages)
    
    # 4. Generate Visualizations (Task 3)
    visualize_funnel(stages, FUNNEL_PLOT_PATH)
    
    # 5. Model Business Impact (Task 4)
    impact_df = calculate_business_impact(funnel_df)
    
    # 6. Generate Recommendations (Task 5)
    report = generate_recommendation_report(funnel_df, impact_df)
    print("\n" + report)
    
    logging.info("=== SIGNUP FUNNEL ANALYSIS PIPELINE COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
