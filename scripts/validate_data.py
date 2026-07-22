import os
import json
import pandas as pd
import numpy as np

RAW_DATA_PATH = "data/raw/validation_data.csv"
CLEANED_DATA_PATH = "data/processed/validated_data.csv"
FAILURES_DATA_PATH = "output/validation_failures.csv"
REPORT_PATH = "output/validation_report.json"

def load_data(filepath=RAW_DATA_PATH):
    """Load data from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    return pd.read_csv(filepath, dtype={'phone': str, 'customer_id': str})

def run_range_checks(df):
    """
    Task 1: Range Checks.
    Ensure age, price, and birth_date fall within valid boundaries.
    """
    df_checked = df.copy()
    
    # 1. Age check (0 to 150)
    df_checked['valid_age'] = (df_checked['age'] >= 0) & (df_checked['age'] <= 150)
    
    # 2. Price check (>= 0)
    df_checked['valid_price'] = df_checked['price'] >= 0
    
    # 3. Birth date check (between 1920-01-01 and today)
    birth_dates = pd.to_datetime(df_checked['birth_date'], errors='coerce')
    now = pd.Timestamp.now()
    df_checked['valid_date'] = (birth_dates >= '1920-01-01') & (birth_dates <= now)
    
    print("\n--- Task 1: Range Checks ---")
    print(f"Invalid ages (not 0-150): {(~df_checked['valid_age']).sum()}")
    print(f"Invalid prices (< 0): {(~df_checked['valid_price']).sum()}")
    print(f"Invalid birth dates (outside 1920 to present): {(~df_checked['valid_date']).sum()}")
    
    return df_checked

def run_null_constraints(df):
    """
    Task 2: Null Constraints.
    Ensure customer_id and email are never null.
    """
    df_checked = df.copy()
    
    # 1. Customer ID must not be null
    df_checked['valid_customer_id'] = df_checked['customer_id'].notna()
    
    # 2. Email must not be null
    df_checked['valid_email'] = df_checked['email'].notna()
    
    print("\n--- Task 2: Null Constraints ---")
    print(f"Missing customer IDs: {(~df_checked['valid_customer_id']).sum()}")
    print(f"Missing emails: {(~df_checked['valid_email']).sum()}")
    
    return df_checked

def run_format_patterns(df):
    """
    Task 3: Format Pattern Validation.
    Ensure email format contains @ and phone format is a 10-digit number.
    """
    df_checked = df.copy()
    
    # 1. Email format check (contains @)
    df_checked['valid_email_format'] = df_checked['email'].astype(str).str.contains('@', na=False)
    
    # 2. Phone format check (exactly 10 digits)
    df_checked['valid_phone'] = df_checked['phone'].astype(str).str.match(r'^\d{10}$', na=False)
    
    print("\n--- Task 3: Format Pattern Validation ---")
    print(f"Invalid emails (missing @): {(~df_checked['valid_email_format']).sum()}")
    print(f"Invalid phone formats (not 10 digits): {(~df_checked['valid_phone']).sum()}")
    
    return df_checked

def run_business_rules(df):
    """
    Task 4: Business Rule Validation.
    Ensure end_date is on or after start_date.
    """
    df_checked = df.copy()
    
    # campaign_end_date >= campaign_start_date
    start_dates = pd.to_datetime(df_checked['start_date'], errors='coerce')
    end_dates = pd.to_datetime(df_checked['end_date'], errors='coerce')
    
    df_checked['valid_date_order'] = (end_dates >= start_dates) & start_dates.notna() & end_dates.notna()
    
    print("\n--- Task 4: Business Rule Validation ---")
    print(f"Invalid date ranges (end < start or missing): {(~df_checked['valid_date_order']).sum()}")
    
    return df_checked

def generate_validation_report(df, validation_cols, failures_path=FAILURES_DATA_PATH, report_path=REPORT_PATH):
    """
    Task 5: Validation Report.
    Combine all checks, isolate failures, and save a structured validation report.
    """
    df_report = df.copy()
    df_report['passes_all_checks'] = df_report[validation_cols].all(axis=1)
    
    # Isolate failures and clean data
    failures = df_report[~df_report['passes_all_checks']]
    df_clean = df_report[df_report['passes_all_checks']]
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(failures_path), exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    # Save failures to CSV
    failures.to_csv(failures_path, index=False)
    print(f"\n--- Task 5: Validation Report & Failure Isolation ---")
    print(f"Isolating failures...")
    print(f"OK: Saved validation failures to {failures_path}")
    
    # Report summary stats
    total_records = len(df_report)
    passed_count = int(df_report['passes_all_checks'].sum())
    failed_count = int((~df_report['passes_all_checks']).sum())
    
    print(f"Records: {total_records}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    
    # Compile validation counts per rule
    rule_summaries = {}
    for col in validation_cols:
        passed_rule = int(df_report[col].sum())
        failed_rule = int((~df_report[col]).sum())
        rule_summaries[col] = {
            'passed': passed_rule,
            'failed': failed_rule,
            'success_rate_pct': round((passed_rule / total_records) * 100, 2) if total_records > 0 else 0.0
        }
    
    report = {
        'total_records': total_records,
        'passed_count': passed_count,
        'failed_count': failed_count,
        'overall_success_rate_pct': round((passed_count / total_records) * 100, 2) if total_records > 0 else 0.0,
        'rule_details': rule_summaries,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"OK: Saved structured validation report to {report_path}")
    
    return df_clean, failures, report

if __name__ == "__main__":
    print("\n" + "="*70)
    print("STARTING DATA VALIDATION WORKFLOW")
    print("="*70)
    
    # Load raw data
    df = load_data()
    
    # Run Task 1: Range Checks
    df = run_range_checks(df)
    
    # Run Task 2: Null Constraints
    df = run_null_constraints(df)
    
    # Run Task 3: Format Patterns
    df = run_format_patterns(df)
    
    # Run Task 4: Business Rules
    df = run_business_rules(df)
    
    # Run Task 5: Report and Isolation
    validation_cols = [
        'valid_age', 
        'valid_price', 
        'valid_customer_id', 
        'valid_email_format', 
        'valid_date_order'
    ]
    
    df_clean, failures, report = generate_validation_report(df, validation_cols)
    
    # Save clean dataset
    os.makedirs(os.path.dirname(CLEANED_DATA_PATH), exist_ok=True)
    df_clean.to_csv(CLEANED_DATA_PATH, index=False)
    print(f"OK: Saved validated clean data to {CLEANED_DATA_PATH}")
    print("="*70)
