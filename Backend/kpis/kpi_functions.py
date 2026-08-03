from __future__ import annotations

import os
import sys
import json
import logging
import numpy as np
import pandas as pd

# Path definitions
RAW_DATA_PATH = "data/raw/kpi_transactions.csv"
TARGETS_JSON_PATH = "kpis/kpi_validation_targets.json"
OUTPUT_DIR = "output"
VALIDATION_REPORT_PATH = os.path.join(OUTPUT_DIR, "kpi_validation_report.json")
LOG_FILE = os.path.join(OUTPUT_DIR, "kpis.log")

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


def generate_transaction_data(filepath: str = RAW_DATA_PATH, n_samples: int = 10000) -> pd.DataFrame:
    """
    Generate synthetic transaction-level data with dates relative to execution local time.
    
    This ensures that 30-day window checks yield correct, predictable results.
    
    Args:
        filepath: CSV file path to save data.
        n_samples: Number of transaction records to generate.
        
    Returns:
        Generated pd.DataFrame.
    """
    logging.info(f"Generating synthetic transaction dataset at {filepath} ({n_samples} records)")
    np.random.seed(42)
    
    # 5,500 unique customer IDs
    customer_ids = [f"CUST{i:04d}" for i in range(1, 5501)]
    
    # Randomly assign customer types to these customer IDs
    segment_choices = ['Enterprise', 'SMB', 'Startup']
    segment_probs = [0.05, 0.40, 0.55]
    customer_type_map = {cid: np.random.choice(segment_choices, p=segment_probs) for cid in customer_ids}
    
    # Transaction IDs
    tx_ids = [f"TXN{i:06d}" for i in range(1, n_samples + 1)]
    
    # Timestamps randomly distributed over the last 90 days from now
    now = pd.Timestamp.now()
    random_days = np.random.uniform(0, 90, size=n_samples)
    random_seconds = np.random.randint(0, 86400, size=n_samples)
    
    tx_dates = []
    for d, s in zip(random_days, random_seconds):
        dt = now - pd.Timedelta(days=d) - pd.Timedelta(seconds=s)
        tx_dates.append(dt.strftime('%Y-%m-%d %H:%M:%S'))
        
    # Transaction amounts: Enterprise has larger carts, Startup smaller
    amounts = []
    customer_types = []
    products = []
    payment_statuses = []
    selected_customers = np.random.choice(customer_ids, size=n_samples)
    
    for cid in selected_customers:
        ctype = customer_type_map[cid]
        customer_types.append(ctype)
        
        if ctype == 'Enterprise':
            amt = np.random.normal(5000, 500)
            prod = np.random.choice(['Enterprise Suite', 'Analytics Pro'], p=[0.7, 0.3])
        elif ctype == 'SMB':
            amt = np.random.normal(200, 30)
            prod = np.random.choice(['Basic Tier', 'Cloud API', 'Analytics Pro'], p=[0.5, 0.3, 0.2])
        else: # Startup
            amt = np.random.normal(45, 8)
            prod = np.random.choice(['Cloud API', 'Basic Tier', 'Analytics Pro'], p=[0.5, 0.3, 0.2])
            
        amounts.append(round(max(5.0, amt), 2))
        products.append(prod)
        # Payment status: 98% Success, 2% Failed
        status = np.random.choice(['Success', 'Failed'], p=[0.98, 0.02])
        payment_statuses.append(status)
        
    df = pd.DataFrame({
        'transaction_id': tx_ids,
        'customer_id': selected_customers,
        'transaction_date': tx_dates,
        'amount': amounts,
        'customer_type': customer_types,
        'product': products,
        'payment_status': payment_statuses
    })
    
    # Sort chronologically
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df = df.sort_values('transaction_date').reset_index(drop=True)
    df.to_csv(filepath, index=False)
    
    logging.info("Saved generated transaction CSV.")
    return df


def load_data(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Ingest raw transaction data and parse date column.
    
    Args:
        filepath: CSV path.
        
    Returns:
        pd.DataFrame.
    """
    logging.info(f"Loading transaction data from {filepath}")
    if not os.path.exists(filepath):
        generate_transaction_data(filepath)
    df = pd.read_csv(filepath)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    logging.info(f"Loaded {len(df)} transactions.")
    return df


def calculate_mau(df: pd.DataFrame, days: int = 30, reference_date: pd.Timestamp = None) -> int:
    """
    Monthly Active Users: distinct customers with at least one successful transaction in last N days.
    
    Args:
        df: Input DataFrame.
        days: Time window size in days.
        reference_date: Reference timestamp. Defaults to max date in dataset.
        
    Returns:
        int: Unique active customer count.
    """
    df_success = df[df['payment_status'] == 'Success']
    if reference_date is None:
        reference_date = df['transaction_date'].max()
    cutoff = reference_date - pd.Timedelta(days=days)
    
    active_users = df_success[df_success['transaction_date'] >= cutoff]['customer_id'].nunique()
    return int(active_users)


def calculate_revenue_per_customer(df: pd.DataFrame) -> float:
    """
    Average revenue per unique customer across successful transactions.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        float: Revenue per customer.
    """
    df_success = df[df['payment_status'] == 'Success']
    total_rev = df_success['amount'].sum()
    unique_custs = df_success['customer_id'].nunique()
    return float(total_rev / unique_custs) if unique_custs > 0 else 0.0


def calculate_churn_rate(df: pd.DataFrame, period_days: int = 30, reference_date: pd.Timestamp = None) -> float:
    """
    Churn Rate: Customers who were active in P1 (prior window) but had no activity in P2 (current window).
    
    Args:
        df: Input DataFrame.
        period_days: Window size in days.
        reference_date: Reference timestamp. Defaults to max date in dataset.
        
    Returns:
        float: Churn rate percentage decimal.
    """
    df_success = df[df['payment_status'] == 'Success']
    if reference_date is None:
        reference_date = df['transaction_date'].max()
        
    period_1_end = reference_date - pd.Timedelta(days=period_days)
    period_1_start = period_1_end - pd.Timedelta(days=period_days)
    period_2_start = period_1_end
    period_2_end = reference_date
    
    active_p1 = df_success[(df_success['transaction_date'] >= period_1_start) & 
                           (df_success['transaction_date'] < period_1_end)]['customer_id'].unique()
    active_p2 = df_success[(df_success['transaction_date'] >= period_2_start) & 
                           (df_success['transaction_date'] <= period_2_end)]['customer_id'].unique()
    
    if len(active_p1) == 0:
        return 0.0
        
    churned = len([x for x in active_p1 if x not in active_p2])
    return float(churned / len(active_p1))


def calculate_payment_success_rate(df: pd.DataFrame) -> float:
    """
    Payment Success Rate: Successful payment attempts divided by total payment attempts.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        float: Ratio of successful transactions.
    """
    success_count = len(df[df['payment_status'] == 'Success'])
    total_attempts = len(df)
    return float(success_count / total_attempts) if total_attempts > 0 else 1.0


def calculate_customer_acquisition_cost(df: pd.DataFrame, total_spend: float = 75000.0, period_days: int = 30, reference_date: pd.Timestamp = None) -> float:
    """
    Customer Acquisition Cost (CAC): Marketing cost divided by count of new transacting customers in last N days.
    
    A new customer is defined as one whose first successful transaction falls in the window.
    
    Args:
        df: Input DataFrame.
        total_spend: Marketing spend in the period.
        period_days: Time window in days.
        reference_date: Reference timestamp. Defaults to max date in dataset.
        
    Returns:
        float: Acquisition cost.
    """
    df_success = df[df['payment_status'] == 'Success']
    if reference_date is None:
        reference_date = df['transaction_date'].max()
    cutoff = reference_date - pd.Timedelta(days=period_days)
    
    # Calculate first transaction date for each customer
    first_transaction = df_success.groupby('customer_id')['transaction_date'].min()
    new_customers = len(first_transaction[first_transaction >= cutoff])
    
    return float(total_spend / new_customers) if new_customers > 0 else 0.0


def validate_kpis(current_kpis: dict[str, float], targets_path: str = TARGETS_JSON_PATH) -> pd.DataFrame:
    """
    Task 3: Compare actual computed KPIs against validation target thresholds.
    
    Args:
        current_kpis: Dict of KPI values.
        targets_path: Path to target ranges JSON.
        
    Returns:
        pd.DataFrame: Status validation report.
    """
    logging.info("--- Task 3: Validating KPIs Against Targets ---")
    if not os.path.exists(targets_path):
        raise FileNotFoundError(f"KPI Targets JSON configuration not found at {targets_path}")
        
    with open(targets_path, 'r') as f:
        targets = json.load(f)
        
    validation_report = []
    for kpi_name, target_range in targets.items():
        actual = current_kpis.get(kpi_name, 0.0)
        min_val = target_range['min']
        max_val = target_range['max']
        
        status = 'PASS' if min_val <= actual <= max_val else 'ALERT'
        
        # Readable form formatting
        if kpi_name == 'revenue_per_customer' or kpi_name == 'customer_acquisition_cost':
            actual_str = f"${actual:,.2f}"
            range_str = f"${min_val:,.0f} - ${max_val:,.0f}"
        elif kpi_name == 'churn_rate' or kpi_name == 'payment_success_rate':
            actual_str = f"{actual:.2%}"
            range_str = f"{min_val:.1%} - {max_val:.1%}"
        else: # mau
            actual_str = f"{int(actual):,}"
            range_str = f"{min_val:,} - {max_val:,}"
            
        validation_report.append({
            'kpi_name': kpi_name,
            'actual_value': actual,
            'formatted_actual': actual_str,
            'target_range': range_str,
            'status': status
        })
        
    validation_df = pd.DataFrame(validation_report)
    
    # Save report
    with open(VALIDATION_REPORT_PATH, 'w') as f:
        json.dump(validation_report, f, indent=2)
        
    logging.info(f"\nValidation Report:\n{validation_df[['kpi_name', 'formatted_actual', 'target_range', 'status']]}")
    
    failures = validation_df[validation_df['status'] == 'ALERT']
    if len(failures) > 0:
        logging.warning(f"[ALERT] {len(failures)} KPIs OUT OF TARGET RANGE - REVIEW REQUIRED")
    else:
        logging.info("[OK] All KPIs within target range.")
        
    return validation_df


def decompose_revenue(df: pd.DataFrame) -> None:
    """
    Task 4: Revenue KPI decomposition down to Segment and Product hierarchies.
    
    Args:
        df: Input DataFrame.
    """
    logging.info("--- Task 4: KPI Decomposition (Revenue) ---")
    df_success = df[df['payment_status'] == 'Success']
    
    total_rev = df_success['amount'].sum()
    revenue_by_segment = df_success.groupby('customer_type')['amount'].sum()
    
    # Decompose further: by product within each customer segment
    revenue_by_segment_product = df_success.groupby(['customer_type', 'product'])['amount'].sum()
    
    decomposition = f"""
KPI DECOMPOSITION: Total Cumulative Revenue
============================================

Level 1 (Top-level Revenue): ${total_rev:,.2f}

Level 2 (By Customer Segment):
  Enterprise: ${revenue_by_segment.get('Enterprise', 0.0):,.2f} ({revenue_by_segment.get('Enterprise', 0.0)/total_rev*100:.1f}%)
  SMB:        ${revenue_by_segment.get('SMB', 0.0):,.2f} ({revenue_by_segment.get('SMB', 0.0)/total_rev*100:.1f}%)
  Startup:    ${revenue_by_segment.get('Startup', 0.0):,.2f} ({revenue_by_segment.get('Startup', 0.0)/total_rev*100:.1f}%)

Level 3 (Segment x Product Breakdown):
"""
    for (seg, prod), rev in revenue_by_segment_product.items():
        segment_total = revenue_by_segment.get(seg, 1.0)
        decomposition += f"  - {seg} -> {prod}: ${rev:,.2f} ({rev/segment_total*100:.1f}% of segment)\n"
        
    print(decomposition)
    logging.info("Revenue decomposition completed successfully.")


def main() -> None:
    """Run the complete KPI calculation and validation pipeline."""
    logging.info("=== STARTING KPI COMPUTATION & VALIDATION PIPELINE ===")
    
    # Generate data if missing
    if not os.path.exists(RAW_DATA_PATH):
        generate_transaction_data(RAW_DATA_PATH)
        
    # Ingest
    df = load_data(RAW_DATA_PATH)
    
    # Calculate
    ref_date = df['transaction_date'].max()
    mau = calculate_mau(df, reference_date=ref_date)
    rpc = calculate_revenue_per_customer(df)
    churn = calculate_churn_rate(df, reference_date=ref_date)
    pay_rate = calculate_payment_success_rate(df)
    cac = calculate_customer_acquisition_cost(df, total_spend=120000.0, reference_date=ref_date)
    
    current_kpis = {
        'mau': mau,
        'revenue_per_customer': rpc,
        'churn_rate': churn,
        'payment_success_rate': pay_rate,
        'customer_acquisition_cost': cac
    }
    
    # Display computed actuals
    print("\n=== COMPUTED BUSINESS METRIC ACTUALS ===")
    print(f"Monthly Active Users (MAU): {mau:,}")
    print(f"Revenue per Customer (RPC): ${rpc:.2f}")
    print(f"Churn Rate:                 {churn:.2%}")
    print(f"Payment Success Rate:       {pay_rate:.2%}")
    print(f"Customer Acquisition Cost:  ${cac:.2f}")
    
    # Validate against targets (Task 3)
    _ = validate_kpis(current_kpis)
    
    # Decomposition (Task 4)
    decompose_revenue(df)
    
    logging.info("=== KPI COMPUTATION & VALIDATION PIPELINE COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
