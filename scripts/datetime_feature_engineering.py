"""
Date & Time Transformation Pipeline script.

This script demonstrates date and time feature engineering in pandas:
1. Parsing string timestamps with an explicit format string.
2. Extracting temporal features (day of week, hour of day).
3. Extracting ISO week numbers and performing time-series resampling.
4. Computing days-since-event (recency metrics) using datetime arithmetic.
5. Building multi-dimensional time-indexed aggregations and pivot tables.
"""

import os
import pandas as pd
import numpy as np

# Optional matplotlib import for saving visualization plots (use non-interactive 'Agg' backend)
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

# Path definitions
RAW_DATA_PATH = "data/raw/datetime_transactions.csv"
PROCESSED_DATA_PATH = "data/processed/datetime_features.csv"
OUTPUT_DIR = "output"


def load_raw_data(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Load raw transaction dataset from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    df = pd.read_csv(filepath)
    print(f"[LOAD] Ingested {len(df)} records from {filepath}")
    return df


def parse_timestamps(df: pd.DataFrame, date_col: str = 'transaction_date', date_format: str = '%Y-%m-%d %H:%M:%S') -> pd.DataFrame:
    """
    Task 1: Convert string dates to datetime type with explicit format.

    Why explicit format is required:
    - Avoids silent corruption from date component swapping (e.g., DD/MM vs MM/DD).
    - Significantly faster execution compared to guessing format across rows.
    - Ensures predictable parsing across different locale settings.

    Args:
        df: Input DataFrame.
        date_col: Name of the string timestamp column.
        date_format: Explicit datetime format specifier.

    Returns:
        DataFrame with parsed datetime column.
    """
    df_transformed = df.copy()
    print("\n--- Task 1: Parse Timestamp Strings with Explicit Format ---")
    print(f"Original dtype of '{date_col}': {df_transformed[date_col].dtype}")
    
    # Parse explicitly
    df_transformed[date_col] = pd.to_datetime(
        df_transformed[date_col],
        format=date_format
    )
    
    # Verify dtype
    dtype_str = str(df_transformed[date_col].dtype)
    print(f"Parsed dtype of '{date_col}': {dtype_str}")
    assert 'datetime64' in dtype_str, f"Expected datetime64, got {dtype_str}"
    print(f"Min date: {df_transformed[date_col].min()}")
    print(f"Max date: {df_transformed[date_col].max()}")
    return df_transformed


def extract_day_and_hour(df: pd.DataFrame, date_col: str = 'transaction_date') -> pd.DataFrame:
    """
    Task 2: Extract Day-of-Week and Hour-of-Day.

    Args:
        df: DataFrame with parsed datetime column.
        date_col: Name of datetime column.

    Returns:
        DataFrame enriched with 'day_of_week', 'dow_numeric', and 'hour'.
    """
    df_transformed = df.copy()
    print("\n--- Task 2: Extract Day-of-Week and Hour-of-Day ---")
    
    # Extract readable day names and numeric hour
    df_transformed['day_of_week'] = df_transformed[date_col].dt.day_name()
    df_transformed['dow_numeric'] = df_transformed[date_col].dt.dayofweek
    df_transformed['hour'] = df_transformed[date_col].dt.hour
    
    # Hourly volume distribution
    hourly_volume = df_transformed.groupby('hour').size()
    print("Hourly Volume Distribution:")
    print(hourly_volume)
    
    daily_volume = df_transformed.groupby('day_of_week').size()
    print("\nDaily Volume Distribution:")
    print(daily_volume)
    
    # Plot histogram / bar chart of hour distribution
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if HAS_PLOTTING:
        plt.figure(figsize=(10, 5))
        hourly_counts = df_transformed['hour'].value_counts().sort_index()
        plt.bar(hourly_counts.index, hourly_counts.values, color='#4A90E2', edgecolor='black', alpha=0.8)
        plt.title("Transaction Distribution by Hour of Day", fontsize=14, fontweight='bold')
        plt.xlabel("Hour of Day (0-23)", fontsize=12)
        plt.ylabel("Transaction Count", fontsize=12)
        plt.xticks(range(0, 24))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plot_path = os.path.join(OUTPUT_DIR, "hourly_distribution.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()
        print(f"[PLOT] Saved hourly distribution plot to {plot_path}")
    
    return df_transformed


def compute_week_and_resample(df: pd.DataFrame, date_col: str = 'transaction_date', value_col: str = 'amount') -> tuple:
    """
    Task 3: Compute Week Number and Resample Data.

    Args:
        df: DataFrame with datetime column.
        date_col: Name of datetime column.
        value_col: Name of column to resample and aggregate.

    Returns:
        tuple of (df_transformed with 'week_num', weekly_metrics DataFrame)
    """
    df_transformed = df.copy()
    print("\n--- Task 3: Compute Week Number and Resample Data ---")
    
    # Extract week number using ISO calendar
    df_transformed['week_num'] = df_transformed[date_col].dt.isocalendar().week
    print(f"Extracted week numbers: {sorted(df_transformed['week_num'].unique())}")
    
    # Resample weekly by setting datetime as index
    df_ts = df_transformed.set_index(date_col)
    weekly_metrics = df_ts[value_col].resample('W').agg(['sum', 'count', 'mean']).rename(
        columns={'sum': 'total_revenue', 'count': 'transaction_count', 'mean': 'avg_transaction_value'}
    )
    print("\nWeekly Trend Aggregation:")
    print(weekly_metrics)
    
    return df_transformed, weekly_metrics


def compute_recency_metrics(df: pd.DataFrame, customer_col: str = 'customer_id', date_col: str = 'transaction_date', reference_date: pd.Timestamp = None) -> tuple:
    """
    Task 4: Compute Days-Since-Event Metric (Recency).

    Args:
        df: DataFrame with datetime column and customer_id.
        customer_col: Column identifying customers.
        date_col: Name of datetime column.
        reference_date: Reference timestamp for recency calculation (defaults to max date + 1 day).

    Returns:
        tuple of (df_transformed with customer recency, customer_recency summary DataFrame)
    """
    df_transformed = df.copy()
    print("\n--- Task 4: Compute Days-Since-Event Metric ---")
    
    if reference_date is None:
        # Use fixed reference date or max date in dataset for deterministic results
        reference_date = df_transformed[date_col].max() + pd.Timedelta(days=1)
    
    print(f"Reference Date for Recency Calculation: {reference_date}")
    
    # Compute days since transaction for each row
    df_transformed['days_since_transaction'] = (reference_date - df_transformed[date_col]).dt.days
    
    # Customer-level last purchase recency
    customer_last_purchase = df_transformed.groupby(customer_col)[date_col].max()
    recency_series = (reference_date - customer_last_purchase).dt.days
    
    customer_recency_df = pd.DataFrame({
        'last_purchase_date': customer_last_purchase,
        'days_since_last_purchase': recency_series
    })
    
    # Map customer recency back to transaction level DataFrame
    df_transformed['days_since_last_purchase'] = df_transformed[customer_col].map(recency_series)
    
    print("\nCustomer Recency Summary (.describe()):")
    print(customer_recency_df['days_since_last_purchase'].describe())
    
    # Identify inactive customers (> 14 days since last purchase relative to reference date)
    inactive_threshold = 14
    inactive_customers = customer_recency_df[customer_recency_df['days_since_last_purchase'] > inactive_threshold]
    print(f"\nInactive Customers (>{inactive_threshold} days since last purchase): {len(inactive_customers)}")
    print(inactive_customers)
    
    return df_transformed, customer_recency_df


def build_time_indexed_aggregations(df: pd.DataFrame, date_col: str = 'transaction_date', value_col: str = 'amount') -> tuple:
    """
    Task 5: Build Time-Indexed Aggregation (Day x Hour).

    Args:
        df: Transformed DataFrame with day_of_week and hour columns.
        date_col: Datetime column.
        value_col: Value column to aggregate.

    Returns:
        tuple of (hourly_daily multi-level groupby, pivot_table DataFrame)
    """
    print("\n--- Task 5: Build Time-Indexed Aggregation ---")
    
    # Order days of week logically
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_transformed = df.copy()
    df_transformed['day_of_week'] = pd.Categorical(df_transformed['day_of_week'], categories=day_order, ordered=True)
    
    # Multi-level groupby: day_of_week and hour
    hourly_daily = df_transformed.groupby(['day_of_week', 'hour'], observed=False)[value_col].agg(['sum', 'count', 'mean'])
    print("Multi-level Groupby (Day of Week x Hour) - First 10 rows:")
    print(hourly_daily.dropna().head(10))
    
    # Pivot table (hour x day_of_week heatmap matrix)
    pivot_table = pd.pivot_table(
        df_transformed,
        values=value_col,
        index='hour',
        columns='day_of_week',
        aggfunc='sum',
        fill_value=0,
        observed=False
    )
    print("\nPivot Table (Hour x Day of Week - Sum of Amounts):")
    print(pivot_table)
    
    # Identify peak activity windows (busiest day/hour windows by count and sum)
    busiest_by_count = df_transformed.groupby(['day_of_week', 'hour'], observed=False).size().sort_values(ascending=False).head(3)
    busiest_by_revenue = df_transformed.groupby(['day_of_week', 'hour'], observed=False)[value_col].sum().sort_values(ascending=False).head(3)
    
    print("\nPeak Activity Windows (by Transaction Count):")
    print(busiest_by_count)
    print("\nPeak Activity Windows (by Revenue Sum):")
    print(busiest_by_revenue)
    
    # Plot heatmap
    if HAS_PLOTTING:
        plt.figure(figsize=(10, 6))
        sns.heatmap(pivot_table, cmap="YlGnBu", annot=True, fmt=".1f", linewidths=.5)
        plt.title("Transaction Amount Heatmap (Hour vs Day of Week)", fontsize=14, fontweight='bold')
        plt.xlabel("Day of Week", fontsize=12)
        plt.ylabel("Hour of Day (0-23)", fontsize=12)
        plt.tight_layout()
        heatmap_path = os.path.join(OUTPUT_DIR, "hour_day_heatmap.png")
        plt.savefig(heatmap_path, dpi=300)
        plt.close()
        print(f"[PLOT] Saved hour x day heatmap plot to {heatmap_path}")
        
    return hourly_daily, pivot_table


def test_edge_case_formats():
    """Test format string behavior across various raw string date patterns."""
    print("\n--- Edge Cases & Timezone Format Testing ---")
    test_dates = [
        '2025-01-15 14:30:45',        # Standard ISO format
        '2025-1-15 14:30:45',         # Single-digit month
        '15/01/2025 14:30:45',        # European format
        '2025-01-15T14:30:45Z',       # ISO format with timezone (UTC Z)
    ]

    for date_str in test_dates:
        try:
            parsed = pd.to_datetime(date_str, format='%Y-%m-%d %H:%M:%S')
            print(f"[OK] Parsed with standard format: '{date_str}' -> {parsed}")
        except Exception as e:
            # Fallback handling demonstration
            parsed_fallback = pd.to_datetime(date_str)
            print(f"[FAIL] Format mismatch for '{date_str}': {e}. Parsed via fallback -> {parsed_fallback}")


def run_pipeline():
    """Execute full Date & Time Transformation Pipeline."""
    df_raw = load_raw_data()
    
    # Task 1: Parse timestamps explicitly
    df_parsed = parse_timestamps(df_raw, date_col='transaction_date', date_format='%Y-%m-%d %H:%M:%S')
    
    # Task 2: Extract day of week and hour
    df_features = extract_day_and_hour(df_parsed, date_col='transaction_date')
    
    # Task 3: Week number and resampling
    df_features, weekly_trend = compute_week_and_resample(df_features, date_col='transaction_date', value_col='amount')
    
    # Task 4: Recency metrics
    df_features, customer_recency = compute_recency_metrics(df_features, customer_col='customer_id', date_col='transaction_date')
    
    # Task 5: Time-indexed aggregation & pivot table
    hourly_daily, pivot = build_time_indexed_aggregations(df_features, date_col='transaction_date', value_col='amount')
    
    # Testing verification metrics (from testing instructions)
    print("\n--- Pipeline Verification Summary ---")
    print(f"Min date: {df_features['transaction_date'].min()}")
    print(f"Max date: {df_features['transaction_date'].max()}")
    print(f"Days in dataset: {(df_features['transaction_date'].max() - df_features['transaction_date'].min()).days}")
    print(f"Hours with data: {sorted(df_features['hour'].unique())}")
    print(f"Weeks in dataset: {df_features['week_num'].nunique()}")
    print(f"Min days since purchase: {df_features['days_since_last_purchase'].min()}")
    print(f"Max days since purchase: {df_features['days_since_last_purchase'].max()}")
    
    # Run edge case tests
    test_edge_case_formats()
    
    # Save processed dataframe
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
    df_features.to_csv(PROCESSED_DATA_PATH, index=False)
    print(f"\n[SUCCESS] Pipeline completed successfully. Output saved to {PROCESSED_DATA_PATH}")


if __name__ == '__main__':
    run_pipeline()
