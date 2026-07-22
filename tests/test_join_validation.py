import os
import pytest
import pandas as pd
import numpy as np
from scripts.join_validation import (
    generate_sample_data,
    CUSTOMERS_PATH,
    ORDERS_PATH,
)

@pytest.fixture(scope="module")
def setup_test_data(tmp_path_factory):
    """Generates mock datasets for module-level tests."""
    temp_dir = tmp_path_factory.mktemp("raw_data")
    cust_path = temp_dir / "customers_large.csv"
    ord_path = temp_dir / "orders_large.csv"
    
    # Generate the mock datasets
    generate_sample_data(customers_path=str(cust_path), orders_path=str(ord_path))
    
    df_cust = pd.read_csv(cust_path)
    df_ord = pd.read_csv(ord_path)
    return df_cust, df_ord

def test_generate_sample_data(setup_test_data):
    """Ensure mock datasets have correct rows and columns."""
    df_cust, df_ord = setup_test_data
    
    assert len(df_cust) == 1000
    assert len(df_ord) == 5000
    assert set(df_cust.columns) == {'customer_id', 'name', 'email', 'signup_date'}
    assert set(df_ord.columns) == {'order_id', 'customer_id', 'order_date', 'amount'}

def test_join_row_count_validation(setup_test_data):
    """Task 1 Test: Ensure left join returns expected row count and increases correctly."""
    df_cust, df_ord = setup_test_data
    
    df_merged = pd.merge(df_cust, df_ord, on='customer_id', how='left')
    
    # Left join result contains matched orders plus unmatched customers
    assert len(df_merged) >= len(df_cust)
    assert len(df_merged) - len(df_cust) > 0

def test_detect_unmatched_keys(setup_test_data):
    """Task 2 Test: Validate identification of unmatched keys on both sides."""
    df_cust, df_ord = setup_test_data
    
    unmatched_cust = df_cust[~df_cust['customer_id'].isin(df_ord['customer_id'])]
    unmatched_ord = df_ord[~df_ord['customer_id'].isin(df_cust['customer_id'])]
    
    # Assert we have unmatched records on both sides due to randomness bounds
    assert len(unmatched_cust) > 0
    assert len(unmatched_ord) > 0
    # Customer IDs in unmatched orders must not be in customers table
    assert not unmatched_ord['customer_id'].isin(df_cust['customer_id']).any()

def test_compare_join_types(setup_test_data):
    """Task 3 Test: Verify math relationship of row counts: Inner <= Left <= Outer."""
    df_cust, df_ord = setup_test_data
    
    inner = pd.merge(df_cust, df_ord, how='inner')
    left = pd.merge(df_cust, df_ord, how='left')
    outer = pd.merge(df_cust, df_ord, how='outer')
    
    assert len(inner) <= len(left)
    assert len(left) <= len(outer)
    # Inner join is smaller than left join if there are unmatched customers
    assert len(inner) < len(left)
    # Left join is smaller than outer join if there are orphaned orders
    assert len(left) < len(outer)

def test_no_unexpected_duplication(setup_test_data):
    """Task 4 Test: Verify column layout and ensure maximum order count is reasonable."""
    df_cust, df_ord = setup_test_data
    
    df_merged = pd.merge(df_cust, df_ord, on='customer_id', how='left')
    
    # Check no duplicate columns with suffix _x or _y exist
    suffixes = [col for col in df_merged.columns if col.endswith('_x') or col.endswith('_y')]
    assert len(suffixes) == 0
    
    # Check max orders per customer is reasonable (e.g. at least 1 and less than 100)
    key_counts = df_merged['customer_id'].value_counts()
    assert key_counts.max() > 0
    assert key_counts.max() < 100
