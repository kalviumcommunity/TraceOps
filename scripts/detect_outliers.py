import os
import json
import numpy as np
import pandas as pd
from scipy import stats

RAW_DATA_PATH = 'data/raw/outliers_data.csv'
PROCESSED_DATA_PATH = 'data/processed/outliers_handled.csv'
CLEANING_LOG_PATH = 'output/cleaning_log.csv'

def load_data(filepath=RAW_DATA_PATH):
    """Load input dataset from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input data file not found: {filepath}")
    df = pd.read_csv(filepath)
    print(f"[LOAD] Ingested {len(df)} records from {filepath}")
    return df

def detect_zscore_outliers(df, column, threshold=3):
    """
    Task 1: Z-Score Outlier Detection.
    Detect outliers as values beyond +/- threshold standard deviations from mean.
    
    Returns: Tuple of (outlier_boolean_mask, z_scores)
    """
    z_scores = np.abs(stats.zscore(df[column]))
    outliers = z_scores > threshold
    return outliers, z_scores

def detect_iqr_outliers(df, column, factor=1.5):
    """
    Task 2: IQR Outlier Detection.
    Detect outliers beyond factor * IQR from quartiles.
    
    Returns: Tuple of (outlier_boolean_mask, lower_bound, upper_bound)
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR
    
    outliers = (df[column] < lower_bound) | (df[column] > upper_bound)
    return outliers, lower_bound, upper_bound

def cap_outliers(df, column, lower_bound, upper_bound):
    """
    Task 3: Cap Outliers at Boundaries.
    Apply capping strategy: replace extreme values with boundary values.
    """
    df_capped = df.copy()
    df_capped[f"{column}_capped"] = df_capped[column].clip(lower=lower_bound, upper=upper_bound)
    return df_capped

def flag_outliers(df, is_outlier_iqr, is_outlier_zscore):
    """
    Task 4: Flag Outliers with Binary Column.
    Combine multiple methods to mark anomalies without removing data.
    """
    df_flagged = df.copy()
    df_flagged['is_outlier'] = (is_outlier_iqr | is_outlier_zscore).astype(int)
    return df_flagged

def save_cleaning_log(cleaning_log, filepath=CLEANING_LOG_PATH):
    """
    Task 5: Create Cleaning Log.
    Document all outlier-related transformations to an audit file.
    """
    log_df = pd.DataFrame(cleaning_log)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    log_df.to_csv(filepath, index=False)
    print(f"OK: Saved cleaning log to {filepath}")
    return log_df

if __name__ == "__main__":
    print("\n" + "="*70)
    print("STARTING OUTLIER DETECTION & HANDLING WORKFLOW")
    print("="*70)
    
    # Load raw data
    df = load_data()
    
    cleaning_log = []
    
    # -------------------------------------------------------------------------
    # Outlier Detection & Handling for 'revenue'
    # -------------------------------------------------------------------------
    print("\n[Processing 'revenue']...")
    
    # Task 1: Z-score detection
    revenue_zscore_outliers, z_scores = detect_zscore_outliers(df, 'revenue')
    df['revenue_zscore'] = z_scores
    print(f"Z-score outliers found in 'revenue': {revenue_zscore_outliers.sum()}")
    
    # Task 2: IQR detection
    revenue_iqr_outliers, lower_rev, upper_rev = detect_iqr_outliers(df, 'revenue')
    df['is_outlier_iqr'] = revenue_iqr_outliers
    print(f"IQR outliers found in 'revenue': {revenue_iqr_outliers.sum()}")
    print(f"  IQR boundaries: [{lower_rev:.2f}, {upper_rev:.2f}]")
    
    # Task 3: Cap Outliers
    df = cap_outliers(df, 'revenue', lower_rev, upper_rev)
    print(f"Capping applied to 'revenue':")
    print(f"  Before: min={df['revenue'].min():,}, max={df['revenue'].max():,}")
    print(f"  After: min={df['revenue_capped'].min():,}, max={df['revenue_capped'].max():,}")
    
    # Task 4: Flag Outliers
    df = flag_outliers(df, df['is_outlier_iqr'], df['revenue_zscore'] > 3)
    normal = df[df['is_outlier'] == 0]
    anomalies = df[df['is_outlier'] == 1]
    print(f"Flagged records - Normal: {len(normal)}, Anomalies: {len(anomalies)}")
    
    # Task 5: Add to cleaning log
    cleaning_log.append({
        'column': 'revenue',
        'method': 'IQR',
        'action': 'cap',
        'threshold_lower': lower_rev,
        'threshold_upper': upper_rev,
        'affected_rows': int(revenue_iqr_outliers.sum()),
        'date': pd.Timestamp.now().isoformat()
    })
    
    # -------------------------------------------------------------------------
    # Outlier Detection & Handling for 'age'
    # -------------------------------------------------------------------------
    print("\n[Processing 'age']...")
    
    # Detect 'age' outliers using IQR
    age_iqr_outliers, lower_age, upper_age = detect_iqr_outliers(df, 'age')
    print(f"IQR outliers found in 'age': {age_iqr_outliers.sum()}")
    print(f"  IQR boundaries: [{lower_age:.2f}, {upper_age:.2f}]")
    
    # For age, we decide to remove rows that are outliers because they represent invalid data
    df_clean_age = df[~age_iqr_outliers].copy()
    print(f"Removal applied to 'age' outliers:")
    print(f"  Rows before: {len(df)}")
    print(f"  Rows after removal: {len(df_clean_age)}")
    
    cleaning_log.append({
        'column': 'age',
        'method': 'IQR',
        'action': 'remove',
        'threshold_lower': lower_age,
        'threshold_upper': upper_age,
        'affected_rows': int(age_iqr_outliers.sum()),
        'date': pd.Timestamp.now().isoformat()
    })
    
    # Save the handling decision logs
    save_cleaning_log(cleaning_log)
    
    # Save processed dataset
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
    df_clean_age.to_csv(PROCESSED_DATA_PATH, index=False)
    print(f"OK: Saved processed data to {PROCESSED_DATA_PATH}")
    print("="*70)
