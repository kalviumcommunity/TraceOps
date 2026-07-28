import json
from pathlib import Path

import pandas as pd

from scripts.handle_missing import (
    analyze_missing_values,
    document_imputation_decisions,
    drop_rows_with_nulls,
    impute_forward_fill,
    impute_mean_median,
    impute_mode,
    validate_imputation,
)


def test_missing_value_workflow():
    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4, 5],
            "name": ["Alice", None, "Alice", None, "Diana"],
            "email": ["alice@example.com", None, "alice@example.com", "charlie@example.com", None],
            "amount": [100, 250, 100, None, 200],
            "category": ["A", "B", "A", "C", None],
            "status_date": pd.to_datetime(["2025-01-01", "2025-01-02", None, "2025-01-04", "2025-01-05"]),
        }
    )

    analysis = analyze_missing_values(df)
    assert analysis.loc[analysis["column"] == "amount", "null_count"].iloc[0] == 1

    df_clean = drop_rows_with_nulls(df, ["customer_id", "email"])
    df_clean = impute_mean_median(df_clean, ["amount"], strategy="median")
    df_clean = impute_mode(df_clean, ["category"])
    df_clean = impute_forward_fill(df_clean, ["status_date"])

    assert df_clean["amount"].isnull().sum() == 0
    assert df_clean["category"].isnull().sum() == 0

    decisions = document_imputation_decisions(df, df_clean)
    assert "amount" in decisions
    assert decisions["amount"]["strategy"] == "median_imputation"

    after = validate_imputation(df, df_clean)
    assert after["null_count_after"].sum() == 1
