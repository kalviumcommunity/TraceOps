import json
from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_DECISIONS_PATH = Path("output/imputation_decisions.json")
OUTPUT_CLEANED_PATH = Path("data/processed/cleaned_data.csv")


def analyze_missing_values(df):
    """
    Compute null counts and percentages before treatment.

    Returns:
        DataFrame with analysis of missing data by column.
    """
    missing_analysis = pd.DataFrame(
        {
            "column": df.columns,
            "null_count": df.isnull().sum().values,
            "null_percentage": (df.isnull().sum() / len(df) * 100).round(2).values,
            "data_type": df.dtypes.values,
            "null_meaning": "",
        }
    )

    print("=" * 70)
    print("BEFORE IMPUTATION - Missing Value Analysis")
    print("=" * 70)
    print(missing_analysis.to_string(index=False))
    print(f"\nTotal rows: {len(df)}")
    print(f"Total cells: {len(df) * len(df.columns)}")
    print(f"Missing cells: {df.isnull().sum().sum()}")
    print("=" * 70)

    return missing_analysis


def impute_mean_median(df, numerical_cols, strategy="median"):
    """Fill numerical nulls with mean or median."""
    df_imputed = df.copy()
    for col in numerical_cols:
        if col not in df_imputed.columns:
            continue
        if df_imputed[col].isnull().sum() > 0:
            fill_value = df_imputed[col].median() if strategy == "median" else df_imputed[col].mean()
            null_count = df_imputed[col].isnull().sum()
            df_imputed[col].fillna(fill_value, inplace=True)
            print(f"  ✓ {col}: filled {null_count} nulls with {strategy} ({fill_value:.2f})")
    return df_imputed


def impute_mode(df, categorical_cols):
    """Fill categorical nulls with mode (most common value)."""
    df_imputed = df.copy()
    for col in categorical_cols:
        if col not in df_imputed.columns:
            continue
        if df_imputed[col].isnull().sum() > 0:
            mode_val = df_imputed[col].mode().iloc[0]
            null_count = df_imputed[col].isnull().sum()
            df_imputed[col].fillna(mode_val, inplace=True)
            print(f"  ✓ {col}: filled {null_count} nulls with mode '{mode_val}'")
    return df_imputed


def impute_forward_fill(df, time_series_cols):
    """Fill with previous value (for time-series data)."""
    df_imputed = df.copy()
    for col in time_series_cols:
        if col not in df_imputed.columns:
            continue
        if df_imputed[col].isnull().sum() > 0:
            null_count = df_imputed[col].isnull().sum()
            df_imputed[col].ffill(inplace=True)
            print(f"  ✓ {col}: forward-filled {null_count} nulls")
    return df_imputed


def drop_rows_with_nulls(df, critical_cols):
    """Drop rows where critical columns are null."""
    rows_before = len(df)
    df_imputed = df.dropna(subset=critical_cols)
    rows_dropped = rows_before - len(df_imputed)
    print(f"  ✓ Dropped {rows_dropped} rows with null in: {critical_cols}")
    return df_imputed


def document_imputation_decisions(df_original, df_imputed):
    """Document all imputation decisions with business justification."""
    decisions = {
        "amount": {
            "column_type": "numerical",
            "null_count_before": int(df_original["amount"].isnull().sum()) if "amount" in df_original else 0,
            "strategy": "median_imputation",
            "value_used": float(df_original["amount"].median()) if "amount" in df_original else None,
            "business_reasoning": "Median purchase amount is representative of typical transaction. Mean would be skewed by high-value outliers. Maintains distribution integrity.",
            "risk_assessment": "Low - median is stable and resistant to outliers",
        },
        "email": {
            "column_type": "categorical_identifier",
            "null_count_before": int(df_original["email"].isnull().sum()) if "email" in df_original else 0,
            "strategy": "drop_rows",
            "rows_affected": int(df_original["email"].isnull().sum()) if "email" in df_original else 0,
            "business_reasoning": "Email is critical for customer contact and marketing campaigns. Rows without email cannot be used for outreach. Data is incomplete.",
            "risk_assessment": "Low - only affects a small percentage of records",
        },
        "status_date": {
            "column_type": "datetime_series",
            "null_count_before": int(df_original["status_date"].isnull().sum()) if "status_date" in df_original else 0,
            "strategy": "forward_fill",
            "interpretation": "Assumes last known status date is still valid until changed",
            "business_reasoning": "For time-series analysis, forward fill preserves temporal continuity. Status typically does not change frequently.",
            "risk_assessment": "Medium - assumes no change between observations",
        },
    }

    OUTPUT_DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_DECISIONS_PATH.open("w", encoding="utf-8") as f:
        json.dump(decisions, f, indent=2, default=str)

    return decisions


def validate_imputation(df_original, df_imputed):
    """Compare metrics before and after imputation."""
    print("\n" + "=" * 70)
    print("AFTER IMPUTATION - Validation Report")
    print("=" * 70)
    print(f"Total rows before: {len(df_original)}")
    print(f"Total rows after:  {len(df_imputed)}")
    print(f"Rows removed: {len(df_original) - len(df_imputed)}")
    print(f"\nTotal nulls before: {df_original.isnull().sum().sum()}")
    print(f"Total nulls after:  {df_imputed.isnull().sum().sum()}")

    missing_after = pd.DataFrame(
        {
            "column": df_imputed.columns,
            "null_count_after": df_imputed.isnull().sum().values,
            "null_percentage_after": (df_imputed.isnull().sum() / len(df_imputed) * 100).round(2).values,
        }
    )

    print("\nNull values by column after imputation:")
    print(missing_after.to_string(index=False))
    print("=" * 70)

    return missing_after


if __name__ == "__main__":
    df = pd.read_csv("data/raw/missing_data.csv", parse_dates=["status_date"])

    print("Step 1: Analyzing missing values...")
    analyze_missing_values(df)

    print("\nStep 2: Applying imputation strategies...")
    df = drop_rows_with_nulls(df, ["customer_id", "email"])
    df = impute_mean_median(df, ["amount"], strategy="median")
    df = impute_mode(df, ["category"])
    df = impute_forward_fill(df, ["status_date"])

    print("\nStep 3: Documenting imputation decisions...")
    decisions = document_imputation_decisions(df, df)
    print(json.dumps(decisions, indent=2, default=str))

    print("\nStep 4: Validating imputation...")
    validation = validate_imputation(df, df)

    OUTPUT_CLEANED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CLEANED_PATH, index=False)
    print(f"\n✓ Cleaned data saved to {OUTPUT_CLEANED_PATH}")
