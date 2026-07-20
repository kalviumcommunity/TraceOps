import json
from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_REPORT_PATH = Path("output/profile_report.json")


def _duplicate_subset_columns(df):
    """Exclude identifier columns when checking for duplicate business records."""
    if "customer_id" in df.columns:
        return [col for col in df.columns if col != "customer_id"]
    return None


def profile_nulls_and_duplicates(df):
    """
    Compute null percentage and duplicate counts per column.

    Returns:
        Dictionary with null analysis by column and duplicate summary.
    """
    profile = {
        "null_counts": {},
        "null_percentages": {},
        "exact_duplicate_count": 0,
        "duplicate_percentage": 0.0,
    }

    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = round((null_count / len(df)) * 100, 2) if len(df) else 0.0
        profile["null_counts"][col] = null_count
        profile["null_percentages"][col] = null_pct

    duplicate_subset = _duplicate_subset_columns(df)
    exact_duplicate_count = int(df.duplicated(subset=duplicate_subset).sum())
    duplicate_percentage = round((exact_duplicate_count / len(df)) * 100, 2) if len(df) else 0.0

    profile["exact_duplicate_count"] = exact_duplicate_count
    profile["duplicate_percentage"] = duplicate_percentage
    return profile


def profile_numerical_columns(df):
    """
    Summarise numerical columns with statistical measures.

    Returns:
        DataFrame with min, max, mean, median, std and null_count per numerical column.
    """
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    stats = {}

    for col in numerical_cols:
        series = df[col]
        stats[col] = {
            "min": round(float(series.min()), 2) if series.notna().any() else None,
            "max": round(float(series.max()), 2) if series.notna().any() else None,
            "mean": round(float(series.mean()), 2) if series.notna().any() else None,
            "median": round(float(series.median()), 2) if series.notna().any() else None,
            "std": round(float(series.std()), 2) if series.notna().any() else None,
            "null_count": int(series.isnull().sum()),
        }

    return pd.DataFrame(stats).T


def profile_categorical_columns(df, top_n=5):
    """
    Summarise categorical columns with value distributions.

    Returns:
        Dictionary with unique counts and top values.
    """
    categorical_cols = df.select_dtypes(include=["object", "string"]).columns
    profile = {}

    for col in categorical_cols:
        series = df[col]
        value_counts = series.value_counts(dropna=True).head(top_n)
        profile[col] = {
            "unique_count": int(series.nunique(dropna=True)),
            "top_values": value_counts.to_dict(),
            "null_count": int(series.isnull().sum()),
        }

    return profile


def identify_quality_issues(df, null_threshold=30, duplicate_threshold=5):
    """
    Identify common data quality issues based on configurable thresholds.

    Returns:
        List of issues found with severity and recommendations.
    """
    issues = []

    null_pcts = (df.isnull().sum() / len(df)) * 100 if len(df) else pd.Series(dtype=float)
    for col, pct in null_pcts.items():
        if pct > null_threshold:
            issues.append(
                {
                    "type": "High nulls",
                    "column": col,
                    "severity": "HIGH",
                    "value": f"{pct:.1f}% missing",
                    "recommendation": "Consider imputation or column exclusion",
                }
            )

    duplicate_subset = _duplicate_subset_columns(df)
    dup_count = int(df.duplicated(subset=duplicate_subset).sum())
    dup_pct = (dup_count / len(df)) * 100 if len(df) else 0.0
    if dup_pct > duplicate_threshold:
        issues.append(
            {
                "type": "High duplicates",
                "column": "Full row",
                "severity": "HIGH",
                "value": f"{dup_pct:.1f}% duplicated",
                "recommendation": "Deduplication required before analysis",
            }
        )

    for col in df.select_dtypes(include=[np.number]).columns:
        if "amount" in col.lower() and (df[col] < 0).any():
            issues.append(
                {
                    "type": "Invalid range",
                    "column": col,
                    "severity": "MEDIUM",
                    "value": "Contains negative values",
                    "recommendation": "Investigate negative entries",
                }
            )

    return issues


def generate_profile_report(df, filepath):
    """
    Generate complete data quality report and save it to the specified JSON file.

    Args:
        df (pd.DataFrame): Input dataset.
        filepath (str): Dataset path label used in the report metadata.

    Returns:
        dict: The complete profiling report dictionary.
    """
    report = {
        "dataset": filepath,
        "record_count": len(df),
        "column_count": len(df.columns),
        "nulls_and_duplicates": profile_nulls_and_duplicates(df),
        "numerical_stats": profile_numerical_columns(df).to_dict(),
        "categorical_stats": profile_categorical_columns(df),
        "quality_issues": identify_quality_issues(df),
    }

    report_path = Path(filepath)
    if report_path.suffix.lower() != ".json":
        report_path = OUTPUT_REPORT_PATH

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"DATA QUALITY PROFILE: {filepath}")
    print(f"{'='*60}")
    print(f"Records: {report['record_count']}")
    print(f"Columns: {report['column_count']}")
    print(f"\nQuality Issues Found: {len(report['quality_issues'])}")
    for issue in report["quality_issues"]:
        print(f"  [{issue['severity']}] {issue['type']} in {issue['column']}")
        print(f"    Value: {issue['value']} → {issue['recommendation']}")
    print(f"{'='*60}\n")

    return report


if __name__ == "__main__":
    dataset_path = "data/raw/quality_test.csv"
    df = pd.read_csv(dataset_path)
    generate_profile_report(df, dataset_path)
