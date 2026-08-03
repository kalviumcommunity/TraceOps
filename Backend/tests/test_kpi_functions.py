from __future__ import annotations

import os
import json
import pytest
import numpy as np
import pandas as pd

from kpis.kpi_functions import (
    generate_transaction_data,
    load_data,
    calculate_mau,
    calculate_revenue_per_customer,
    calculate_churn_rate,
    calculate_payment_success_rate,
    calculate_customer_acquisition_cost,
    validate_kpis
)


@pytest.fixture
def temp_csv_path(tmp_path):
    """Fixture providing a temporary CSV path."""
    return os.path.join(tmp_path, "test_kpi_transactions.csv")


@pytest.fixture
def sample_tx_df():
    """Fixture providing a clean controlled transaction DataFrame with relative dates."""
    now = pd.Timestamp('2026-07-23 12:00:00')
    
    # 5 customers
    # C1: active in P1 (day -45) and active in P2 (day -15) -> Not churned
    # C2: active in P1 (day -40) but not in P2 -> Churned
    # C3: active in P2 (day -10) but not in P1 -> New Customer
    # C4: active in P1 (day -50) but not in P2 -> Churned
    # C5: has failed transaction in P2 -> Churned if no successful transactions
    
    tx_dates = [
        now - pd.Timedelta(days=45),  # C1 - P1 success
        now - pd.Timedelta(days=40),  # C2 - P1 success
        now - pd.Timedelta(days=15),  # C1 - P2 success
        now - pd.Timedelta(days=10),  # C3 - P2 success (New)
        now - pd.Timedelta(days=50),  # C4 - P1 success
        now - pd.Timedelta(days=5)    # C5 - P2 failed
    ]
    
    return pd.DataFrame({
        'transaction_id': ['T01', 'T02', 'T03', 'T04', 'T05', 'T06'],
        'customer_id': ['C1', 'C2', 'C1', 'C3', 'C4', 'C5'],
        'transaction_date': tx_dates,
        'amount': [100.0, 50.0, 150.0, 80.0, 200.0, 120.0],
        'customer_type': ['Enterprise', 'SMB', 'Enterprise', 'Startup', 'SMB', 'Startup'],
        'product': ['Analytics Pro', 'Basic Tier', 'Analytics Pro', 'Cloud API', 'Basic Tier', 'Cloud API'],
        'payment_status': ['Success', 'Success', 'Success', 'Success', 'Success', 'Failed']
    })


def test_generate_transaction_data(temp_csv_path):
    """Verify generated dataset columns, types, and sequence constraints."""
    df = generate_transaction_data(temp_csv_path, n_samples=50)
    
    assert os.path.exists(temp_csv_path)
    assert len(df) == 50
    assert list(df.columns) == ['transaction_id', 'customer_id', 'transaction_date', 'amount', 'customer_type', 'product', 'payment_status']
    assert pd.api.types.is_datetime64_any_dtype(df['transaction_date'])
    assert df['customer_id'].nunique() <= 50
    
    # Sort order is chronological
    assert df['transaction_date'].is_monotonic_increasing


def test_load_data(temp_csv_path):
    """Verify loading dataset."""
    generate_transaction_data(temp_csv_path, n_samples=10)
    df = load_data(temp_csv_path)
    
    assert len(df) == 10
    assert pd.api.types.is_datetime64_any_dtype(df['transaction_date'])


def test_calculate_mau(sample_tx_df):
    """Verify MAU counts successful active users in the last 30 days."""
    ref_date = pd.Timestamp('2026-07-23 12:00:00')
    
    # Active in last 30 days with successful payment: C1, C3
    # C5 is in last 30 days but has Failed transaction
    # C2, C4 are in P1 (>30 days ago)
    mau = calculate_mau(sample_tx_df, days=30, reference_date=ref_date)
    assert mau == 2


def test_calculate_revenue_per_customer(sample_tx_df):
    """Verify revenue per customer aggregates only successful transactions."""
    # Successful transactions: C1 (100 + 150 = 250), C2 (50), C3 (80), C4 (200)
    # Total revenue = 250 + 50 + 80 + 200 = 580
    # Unique successful customers: C1, C2, C3, C4 = 4
    # Expected RPC = 580 / 4 = 145.0
    rpc = calculate_revenue_per_customer(sample_tx_df)
    assert abs(rpc - 145.0) < 1e-5


def test_calculate_churn_rate(sample_tx_df):
    """Verify customer churn calculation between period windows."""
    ref_date = pd.Timestamp('2026-07-23 12:00:00')
    
    # Period 1 (45 to 30 days ago): Active successful customers are C1, C2, C4
    # Period 2 (30 to 0 days ago): Active successful customers are C1, C3
    # C1 active in both -> Not churned
    # C2 active in P1, not P2 -> Churned
    # C4 active in P1, not P2 -> Churned
    # Total active P1: C1, C2, C4 = 3
    # Churned: C2, C4 = 2
    # Expected churn rate = 2 / 3 = 66.7%
    churn = calculate_churn_rate(sample_tx_df, period_days=30, reference_date=ref_date)
    assert abs(churn - (2.0 / 3.0)) < 1e-5


def test_calculate_payment_success_rate(sample_tx_df):
    """Verify success rate of payment attempts."""
    # Successful: 5, Failed: 1 -> Total: 6
    # Expected = 5 / 6 = 83.3%
    success_rate = calculate_payment_success_rate(sample_tx_df)
    assert abs(success_rate - (5.0 / 6.0)) < 1e-5


def test_calculate_customer_acquisition_cost(sample_tx_df):
    """Verify CAC calculation based on new customers acquired."""
    ref_date = pd.Timestamp('2026-07-23 12:00:00')
    
    # First transaction date:
    # C1: day -45
    # C2: day -40
    # C3: day -10
    # C4: day -50
    # C5: day -5 (but failed transaction, not a successful customer)
    # New customers in last 30 days (first purchase >= day -30): only C3
    # Spend = 1000.0, new customers = 1 -> Expected CAC = 1000 / 1 = 1000.0
    cac = calculate_customer_acquisition_cost(sample_tx_df, total_spend=1000.0, period_days=30, reference_date=ref_date)
    assert abs(cac - 1000.0) < 1e-5


def test_validate_kpis(tmp_path):
    """Verify target range validation checks."""
    kpis = {
        'mau': 5500,                    # PASS
        'revenue_per_customer': 105.0,  # PASS
        'churn_rate': 0.08,             # ALERT (threshold is 0.05)
        'payment_success_rate': 0.98,   # PASS
        'customer_acquisition_cost': 35.0 # PASS
    }
    
    # Create target config JSON in temp directory
    targets_path = os.path.join(tmp_path, "test_targets.json")
    with open(targets_path, 'w') as f:
        json.dump({
            "mau": {"min": 5000, "max": 6000},
            "revenue_per_customer": {"min": 90, "max": 110},
            "churn_rate": {"min": 0.0, "max": 0.05},
            "payment_success_rate": {"min": 0.95, "max": 1.0},
            "customer_acquisition_cost": {"min": 0.0, "max": 50.0}
        }, f)
        
    validation_df = validate_kpis(kpis, targets_path=targets_path)
    
    assert len(validation_df) == 5
    # Check that churn rate validation is flagged as ALERT
    churn_row = validation_df[validation_df['kpi_name'] == 'churn_rate'].iloc[0]
    assert churn_row['status'] == 'ALERT'
    
    # Check that mau is flagged as PASS
    mau_row = validation_df[validation_df['kpi_name'] == 'mau'].iloc[0]
    assert mau_row['status'] == 'PASS'
