import json
from pathlib import Path

import pandas as pd

from scripts.profile_data import (
    generate_profile_report,
    identify_quality_issues,
    profile_categorical_columns,
    profile_numerical_columns,
    profile_nulls_and_duplicates,
)


def test_profile_functions_return_expected_shapes():
    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4, 5],
            "name": ["Alice", None, "Alice", None, "Diana"],
            "email": ["alice@example.com", None, "alice@example.com", "charlie@example.com", None],
            "amount": [100, 250, 100, 500, -50],
            "status": ["active", "active", "active", "inactive", "active"],
        }
    )

    null_profile = profile_nulls_and_duplicates(df)
    assert null_profile["null_counts"]["email"] == 2
    assert null_profile["exact_duplicate_count"] == 1
    assert null_profile["duplicate_percentage"] == 20.0

    numerical = profile_numerical_columns(df)
    assert "amount" in numerical.index
    assert numerical.loc["amount", "min"] == -50.0

    categorical = profile_categorical_columns(df)
    assert categorical["name"]["unique_count"] == 2
    assert categorical["status"]["top_values"]["active"] == 4

    issues = identify_quality_issues(df)
    assert any(issue["type"] == "High nulls" for issue in issues)
    assert any(issue["type"] == "High duplicates" for issue in issues)
    assert any(issue["type"] == "Invalid range" for issue in issues)


def test_generate_profile_report_writes_json(tmp_path):
    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4, 5],
            "name": ["Alice", None, "Alice", None, "Diana"],
            "email": ["alice@example.com", None, "alice@example.com", "charlie@example.com", None],
            "amount": [100, 250, 100, 500, -50],
            "status": ["active", "active", "active", "inactive", "active"],
        }
    )

    out_path = tmp_path / "profile_report.json"
    report = generate_profile_report(df, str(out_path))
    assert out_path.exists()
    data = json.loads(out_path.read_text())
    assert data["record_count"] == 5
    assert data["column_count"] == 5
