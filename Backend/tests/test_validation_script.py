"""
Unit tests for SQL-Based Insight Validation pipeline (validation_script.py).
"""

import os
import pytest
import pandas as pd
from sqlalchemy import create_engine, text

from validation_script import (
    setup_database_connection,
    seed_validation_database,
    compute_python_active_users,
    compute_python_aov,
    compute_python_churn,
    validate_metrics,
    run_full_validation_workflow,
    VALIDATION_REPORT_PATH
)


@pytest.fixture
def test_db_engine():
    """Fixture providing SQLAlchemy engine and seeding test data."""
    engine = create_engine("sqlite:///analytics.db")
    seed_validation_database(engine)
    return engine


def test_database_seeding(test_db_engine):
    """Test that logins and orders tables are properly seeded."""
    with test_db_engine.connect() as conn:
        logins_cnt = conn.execute(text("SELECT COUNT(*) FROM logins")).fetchone()[0]
        orders_cnt = conn.execute(text("SELECT COUNT(*) FROM orders")).fetchone()[0]
        
        assert logins_cnt > 0, "logins table should not be empty"
        assert orders_cnt > 0, "orders table should not be empty"


def test_compute_python_metrics(test_db_engine):
    """Test individual Python metric calculations."""
    active_users = compute_python_active_users(test_db_engine)
    aov = compute_python_aov(test_db_engine)
    churn = compute_python_churn(test_db_engine)

    assert active_users == 75, f"Expected 75 active users, got {active_users}"
    assert aov > 0, "AOV should be positive"
    assert churn == 20, f"Expected 20 churned customers, got {churn}"


def test_validate_metrics_uncorrected(test_db_engine):
    """Test validate_metrics with buggy SQL churn query, verifying failure detection."""
    report = validate_metrics(test_db_engine, tolerance_pct=0.1, use_fixed_sql=False)
    
    assert isinstance(report, pd.DataFrame)
    assert len(report) == 3
    
    churn_row = report[report['Metric'] == 'Churn'].iloc[0]
    assert churn_row['Status'] == 'FAIL'
    assert churn_row['Pct_Difference'] > 0.1


def test_validate_metrics_corrected(test_db_engine):
    """Test validate_metrics with fixed SQL churn query, verifying all pass."""
    report = validate_metrics(test_db_engine, tolerance_pct=0.1, use_fixed_sql=True)
    
    assert isinstance(report, pd.DataFrame)
    assert len(report) == 3
    
    for _, row in report.iterrows():
        assert row['Status'] == 'PASS', f"Metric {row['Metric']} should pass but failed."
        assert row['Pct_Difference'] <= row['Tolerance']


def test_full_validation_workflow(test_db_engine):
    """Test full workflow and report CSV output generation."""
    final_report = run_full_validation_workflow(test_db_engine)
    
    assert os.path.exists(VALIDATION_REPORT_PATH)
    saved_df = pd.read_csv(VALIDATION_REPORT_PATH)
    assert len(saved_df) == 3
    assert set(saved_df['Metric']) == {'Active Users', 'AOV', 'Churn'}
    assert (saved_df['Status'] == 'PASS').all()
