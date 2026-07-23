import os
import json
import pandas as pd
import numpy as np

CUSTOMERS_PATH = "data/raw/customers_large.csv"
ORDERS_PATH = "data/raw/orders_large.csv"
MERGED_PATH = "data/processed/merged_orders.csv"
JOIN_REPORT_PATH = "output/join_validation_report.json"

def generate_sample_data(customers_path=CUSTOMERS_PATH, orders_path=ORDERS_PATH):
    """Generate 1000 customers and 5000 orders to test join validation."""
    os.makedirs(os.path.dirname(customers_path), exist_ok=True)
    os.makedirs(os.path.dirname(orders_path), exist_ok=True)
    
    # 1000 customers
    np.random.seed(42)
    cust_ids = np.arange(1, 1001)
    df_cust = pd.DataFrame({
        'customer_id': cust_ids,
        'name': [f"Customer_{i}" for i in cust_ids],
        'email': [f"cust_{i}@example.com" for i in cust_ids],
        'signup_date': pd.date_range(start='2025-01-01', periods=1000, freq='h').strftime('%Y-%m-%d')
    })
    df_cust.to_csv(customers_path, index=False)
    
    # 5000 orders
    # We want some customers to have zero orders (e.g. IDs 901 to 1000)
    # and some order customer_ids to be outside 1-1000 range (orphaned orders, e.g. 1001 to 1020)
    order_cust_ids = np.random.choice(np.arange(1, 901), size=5000) # standard customers
    # Inject 50 orphaned orders with customer IDs between 1001 and 1020
    orphaned_indices = np.random.choice(5000, size=50, replace=False)
    order_cust_ids[orphaned_indices] = np.random.choice(np.arange(1001, 1021), size=50)
    
    df_orders = pd.DataFrame({
        'order_id': np.arange(10001, 15001),
        'customer_id': order_cust_ids,
        'order_date': pd.date_range(start='2025-02-01', periods=5000, freq='min').strftime('%Y-%m-%d'),
        'amount': np.round(np.random.uniform(10.0, 500.0, size=5000), 2)
    })
    df_orders.to_csv(orders_path, index=False)
    
    print(f"[GENERATE] Created mock customer data at {customers_path} (1000 rows)")
    print(f"[GENERATE] Created mock order data at {orders_path} (5000 rows)")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("STARTING JOIN VALIDATION WORKFLOW")
    print("="*70)
    
    # Generate data if not exists
    if not os.path.exists(CUSTOMERS_PATH) or not os.path.exists(ORDERS_PATH):
        generate_sample_data()
        
    df_customers = pd.read_csv(CUSTOMERS_PATH)
    df_orders = pd.read_csv(ORDERS_PATH)
    
    # Task 1: Explicit Join with Row Count Validation
    print("\n--- Task 1: Explicit Join with Row Count Validation ---")
    print(f"Left: {len(df_customers)}")
    print(f"Right: {len(df_orders)}")

    df_merged = pd.merge(df_customers, df_orders, on='customer_id', how='left')

    print(f"Merged: {len(df_merged)}")
    print(f"Change: {len(df_merged) - len(df_customers)}")
    
    # Task 2: Detect Unmatched Keys
    print("\n--- Task 2: Detect Unmatched Keys ---")
    unmatched_customers = df_customers[~df_customers['customer_id'].isin(df_orders['customer_id'])]
    unmatched_orders = df_orders[~df_orders['customer_id'].isin(df_customers['customer_id'])]

    print(f"Customers without orders: {len(unmatched_customers)}")
    print(f"Orphaned orders: {len(unmatched_orders)}")

    os.makedirs('output', exist_ok=True)
    unmatched_customers.to_csv('output/unmatched_customers.csv', index=False)
    unmatched_orders.to_csv('output/unmatched_orders.csv', index=False)
    print("OK: Saved unmatched customers and orders to output/")
    
    # Task 3: Compare Join Types
    print("\n--- Task 3: Compare Join Types ---")
    inner = pd.merge(df_customers, df_orders, how='inner')
    left = pd.merge(df_customers, df_orders, how='left')
    outer = pd.merge(df_customers, df_orders, how='outer')

    print(f"Inner: {len(inner)}, Left: {len(left)}, Outer: {len(outer)}")
    
    # Task 4: Validate No Unexpected Duplication
    print("\n--- Task 4: Validate No Unexpected Duplication ---")
    # Check for unexpected column conflicts
    print(df_merged.columns)

    # If customer_id appears in both, verify merge key
    key_counts = df_merged['customer_id'].value_counts()
    print(f"Max orders per customer: {key_counts.max()}")
    
    # Task 5: Document Join Decision
    print("\n--- Task 5: Document Join Decision ---")
    join_report = {
        'join_type': 'left',
        'left_table': 'customers',
        'right_table': 'orders',
        'join_key': 'customer_id',
        'left_rows': len(df_customers),
        'right_rows': len(df_orders),
        'result_rows': len(df_merged),
        'unmatched_left': len(unmatched_customers),
        'unmatched_right': len(unmatched_orders),
        'reasoning': 'Left join preserves all customers; unmatched customers have no orders'
    }

    print(json.dumps(join_report, indent=2))
    
    with open(JOIN_REPORT_PATH, 'w') as f:
        json.dump(join_report, f, indent=2)
    print(f"OK: Saved join validation report to {JOIN_REPORT_PATH}")
    
    # Save the merged dataset
    os.makedirs(os.path.dirname(MERGED_PATH), exist_ok=True)
    df_merged.to_csv(MERGED_PATH, index=False)
    print(f"OK: Saved merged orders dataset to {MERGED_PATH}")
    print("="*70)
