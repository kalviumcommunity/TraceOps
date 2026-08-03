import os
import pytest
import pandas as pd
import numpy as np
from scripts.validate_data import (
    run_range_checks,
    run_null_constraints,
    run_format_patterns,
    run_business_rules,
    generate_validation_report,
)

@pytest.fixture
def sample_df():
    """Provides a sample DataFrame for testing validation rules."""
    return pd.DataFrame({
        'customer_id': ['CUST1', 'CUST2', None, 'CUST4'],
        'age': [25, -5, 160, 45],
        'price': [100.0, 50.0, -10.0, 0.0],
        'birth_date': ['1995-05-15', '2050-01-01', '1910-01-01', '1980-11-20'],
        'email': ['alice@example.com', 'bob_at_example.com', 'charlie@example.com', None],
        'phone': ['1234567890', '9876543210', '12345', '5555555555'],
        'start_date': ['2025-01-01', '2025-02-01', '2025-03-10', '2025-04-01'],
        'end_date': ['2025-01-10', '2025-02-15', '2025-03-05', '2025-04-10']
    })

def test_range_checks(sample_df):
    """Ensure range checks identify invalid ages, prices, and birth dates."""
    df_checked = run_range_checks(sample_df)
    
    # Age: CUST2 (-5) and CUST3 (160) are invalid
    assert df_checked['valid_age'].tolist() == [True, False, False, True]
    
    # Price: CUST3 (-10) is invalid
    assert df_checked['valid_price'].tolist() == [True, True, False, True]
    
    # Birth Date: CUST2 (2050 in future) and CUST3 (1910 too old) are invalid
    assert df_checked['valid_date'].tolist() == [True, False, False, True]

def test_null_constraints(sample_df):
    """Ensure null constraints flag missing critical columns (customer_id, email)."""
    df_checked = run_null_constraints(sample_df)
    
    # customer_id: third row is null
    assert df_checked['valid_customer_id'].tolist() == [True, True, False, True]
    
    # email: fourth row is null
    assert df_checked['valid_email'].tolist() == [True, True, True, False]

def test_format_patterns(sample_df):
    """Ensure format patterns correctly identify malformed emails and phone numbers."""
    df_checked = run_format_patterns(sample_df)
    
    # email format: second row (bob_at_example.com) lacks @
    assert df_checked['valid_email_format'].tolist() == [True, False, True, False]
    
    # phone format: third row (12345) is not 10 digits
    assert df_checked['valid_phone'].tolist() == [True, True, False, True]

def test_business_rules(sample_df):
    """Ensure business rules validate ordering (end_date >= start_date)."""
    df_checked = run_business_rules(sample_df)
    
    # third row: start_date=2025-03-10, end_date=2025-03-05 is invalid
    assert df_checked['valid_date_order'].tolist() == [True, True, False, True]

def test_validation_report(sample_df, tmp_path):
    """Ensure validation report is compiled correctly and failures are isolated."""
    df = run_range_checks(sample_df)
    df = run_null_constraints(df)
    df = run_format_patterns(df)
    df = run_business_rules(df)
    
    validation_cols = ['valid_age', 'valid_price', 'valid_customer_id', 
                      'valid_email_format', 'valid_date_order']
                      
    failures_file = tmp_path / "validation_failures.csv"
    report_file = tmp_path / "validation_report.json"
    
    df_clean, failures, report = generate_validation_report(
        df, 
        validation_cols, 
        failures_path=str(failures_file), 
        report_path=str(report_file)
    )
    
    # Verify outputs
    assert len(df_clean) == 1  # Only CUST1 passes all 5 validation checks
    assert len(failures) == 3  # CUST2, CUST3, CUST4 fail at least one check
    assert os.path.exists(failures_file)
    assert os.path.exists(report_file)
    
    # Verify report structure
    assert report['total_records'] == 4
    assert report['passed_count'] == 1
    assert report['failed_count'] == 3
    assert report['overall_success_rate_pct'] == 25.0
    assert 'valid_age' in report['rule_details']
    assert report['rule_details']['valid_age']['failed'] == 2
