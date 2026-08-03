"""
Customer Feature Engineering Pipeline script.

This script implements customer feature engineering tasks:
1. Aggregating transaction-level data to the customer level.
2. Computing ratio features (transactions_per_month, avg_spend_per_transaction, lifetime_value_per_month).
3. Equal-width binning for engagement rate.
4. Quantile binning for customer spending.
5. Computing composite RFM scores.
6. Validating engineered features.
"""

import os
import pandas as pd
import numpy as np

# Path definitions
CUSTOMERS_PATH = "data/raw/customers_large.csv"
ORDERS_PATH = "data/raw/orders_large.csv"
PROCESSED_PATH = "data/processed/customer_features.csv"


def load_and_aggregate_data(customers_path: str = CUSTOMERS_PATH, orders_path: str = ORDERS_PATH) -> pd.DataFrame:
    """
    Load raw customers and orders data, and aggregate to customer level.
    """
    if not os.path.exists(customers_path):
        raise FileNotFoundError(f"Customers data not found at: {customers_path}")
    if not os.path.exists(orders_path):
        raise FileNotFoundError(f"Orders data not found at: {orders_path}")

    # Load datasets
    df_customers = pd.read_csv(customers_path)
    df_orders = pd.read_csv(orders_path)

    # Cast dates to datetime objects
    df_customers['signup_date'] = pd.to_datetime(df_customers['signup_date'])
    df_orders['order_date'] = pd.to_datetime(df_orders['order_date'])

    # Determine reference date: max order_date + 1 day
    reference_date = df_orders['order_date'].max() + pd.Timedelta(days=1)
    print(f"[PREPARATION] Reference Date: {reference_date.strftime('%Y-%m-%d')}")

    # Aggregate orders per customer
    orders_agg = df_orders.groupby('customer_id').agg(
        purchase_count=('order_id', 'count'),
        total_spent=('amount', 'sum'),
        last_purchase_date=('order_date', 'max')
    ).reset_index()

    # Merge customers with aggregated order statistics
    df = pd.merge(df_customers, orders_agg, on='customer_id', how='left')

    # Fill NaNs for customers with 0 transactions to prevent missing values in basic fields
    df['purchase_count'] = df['purchase_count'].fillna(0).astype(int)
    df['total_transactions'] = df['purchase_count']
    df['total_spent'] = df['total_spent'].fillna(0.0)

    # Calculate days as customer, clip at 1 day to prevent division by zero
    df['days_as_customer'] = (reference_date - df['signup_date']).dt.days.clip(lower=1)

    # Calculate days since last purchase (recency)
    # If a customer has no transactions, fill last purchase date with signup_date (conservative assumption)
    df['last_purchase_date'] = df['last_purchase_date'].fillna(df['signup_date'])
    df['days_since_last_purchase'] = (reference_date - df['last_purchase_date']).dt.days.clip(lower=1)

    print(f"[PREPARATION] Loaded and aggregated {len(df)} customers.")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run Tasks 1 to 5 to engineer customer business features.
    """
    df_transformed = df.copy()

    # Filter out customers with 0 transactions to guarantee no NaNs in RFM / ratio scoring
    # (Since RFM and average spend are only mathematically valid for active customers)
    df_transformed = df_transformed[df_transformed['total_transactions'] > 0].copy()

    # Task 1: Compute Ratio Features (1 mark)
    print("\n--- Task 1: Compute Ratio Features ---")
    df_transformed['transactions_per_month'] = df_transformed['total_transactions'] / (df_transformed['days_as_customer'] / 30)
    df_transformed['avg_spend_per_transaction'] = df_transformed['total_spent'] / df_transformed['total_transactions']
    df_transformed['lifetime_value_per_month'] = df_transformed['total_spent'] / (df_transformed['days_as_customer'] / 30)

    print("Task 1 Output (Summary Statistics):")
    print(df_transformed[['transactions_per_month', 'avg_spend_per_transaction']].describe())

    # Task 2: Binning with Equal-Width Bins (1 mark)
    print("\n--- Task 2: Binning with Equal-Width Bins ---")
    df_transformed['engagement_tier'] = pd.cut(
        df_transformed['transactions_per_month'],
        bins=[0, 2, 10, float('inf')],
        labels=['low', 'medium', 'high']
    )

    print("Task 2 Output (Engagement Tier Counts):")
    print(df_transformed['engagement_tier'].value_counts())

    # Task 3: Binning with Quantiles (1 mark)
    print("\n--- Task 3: Binning with Quantiles ---")
    df_transformed['spend_quartile'] = pd.qcut(
        df_transformed['total_spent'],
        q=4,
        labels=['Q1', 'Q2', 'Q3', 'Q4']
    )

    print("Task 3 Output (Spend Quartile Counts):")
    print(df_transformed['spend_quartile'].value_counts())

    # Task 4: Composite Score (1 mark)
    print("\n--- Task 4: Composite Score ---")
    df_transformed['recency_score'] = pd.qcut(df_transformed['days_since_last_purchase'].rank(method='first'), q=5, labels=[5,4,3,2,1])
    df_transformed['frequency_score'] = pd.qcut(df_transformed['purchase_count'].rank(method='first'), q=5, labels=[1,2,3,4,5])
    df_transformed['monetary_score'] = pd.qcut(df_transformed['total_spent'].rank(method='first'), q=5, labels=[1,2,3,4,5])

    df_transformed['rfm_score'] = (df_transformed['recency_score'].astype(int) + 
                       df_transformed['frequency_score'].astype(int) + 
                       df_transformed['monetary_score'].astype(int))

    print("Task 4 Output (RFM Scores computed successfully)")

    # Task 5: Feature Validation (1 mark)
    print("\n--- Task 5: Feature Validation ---")
    # Check ranges are sensible
    print(f"Engagement tier distribution:\n{df_transformed['engagement_tier'].value_counts()}")
    print(f"RFM score range: {df_transformed['rfm_score'].min()}-{df_transformed['rfm_score'].max()}")

    # Ensure no NaNs introduced
    missing_counts = df_transformed[['engagement_tier', 'spend_quartile', 'rfm_score']].isna().sum()
    print(f"Missing values:\n{missing_counts}")
    assert missing_counts.sum() == 0, f"Error: NaNs introduced during feature engineering!"

    return df_transformed


def main():
    print("=" * 60)
    print("STARTING CUSTOMER FEATURE ENGINEERING PIPELINE")
    print("=" * 60)

    # 1. Load and aggregate
    df_agg = load_and_aggregate_data()

    # 2. Engineer features
    df_features = engineer_features(df_agg)

    # 3. Output results
    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    df_features.to_csv(PROCESSED_PATH, index=False)
    print(f"\n[SUCCESS] Feature engineering complete. Saved to: {PROCESSED_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
