from __future__ import annotations

import os
import sys
import logging
import numpy as np
import pandas as pd

# Optional plotting setup (using non-interactive 'Agg' backend)
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

# Path definitions
RAW_DATA_PATH = "data/raw/daily_revenue_data.csv"
OUTPUT_DIR = "output"
ROLLING_PLOT_PATH = os.path.join(OUTPUT_DIR, "rolling_avg.png")
CUMULATIVE_PLOT_PATH = os.path.join(OUTPUT_DIR, "cumulative.png")
TREND_TXT_PATH = os.path.join(OUTPUT_DIR, "trend_analysis.txt")
LOG_FILE = os.path.join(OUTPUT_DIR, "rolling_metrics.log")

# Ensure directories exist
os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Add console logging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)


def generate_time_series_data(filepath: str = RAW_DATA_PATH, start_date: str = '2025-01-01', periods: int = 180) -> pd.DataFrame:
    """
    Generate synthetic daily revenue and orders dataset.
    
    The dataset includes:
    1. A baseline revenue of $40k growing over time.
    2. Weekly seasonality: Tuesday ~$45k, Friday ~$35k, Sunday ~$51k.
    3. Normal daily noise (std dev = $3k).
    4. Correlated orders count (baseline ~1000 orders/day with seasonality).
    
    Args:
        filepath: Filepath to save the CSV.
        start_date: Start date for the time-series.
        periods: Number of days to generate.
        
    Returns:
        Generated pd.DataFrame.
    """
    logging.info(f"Generating synthetic daily revenue data at {filepath}")
    np.random.seed(42)
    dates = pd.date_range(start=start_date, periods=periods, freq='D')
    
    # Seasonality multipliers (0=Monday, 1=Tuesday, ..., 6=Sunday)
    # Target: Tuesday (~45k), Friday (~35k), Sunday (~51k)
    # Base is around 40k. So Sunday = 40k * 1.275 = 51k, Tuesday = 40k * 1.125 = 45k, Friday = 40k * 0.875 = 35k
    seasonality = {
        0: 1.00,  # Monday
        1: 1.125, # Tuesday (45k target)
        2: 0.95,  # Wednesday
        3: 1.05,  # Thursday
        4: 0.875, # Friday (35k target)
        5: 1.10,  # Saturday
        6: 1.275  # Sunday (51k target)
    }
    
    # Growth trend over time: starts at 40k, ends at 52k (linear growth of ~66.7 per day)
    growth_rate = 66.7
    
    revenue_list = []
    orders_list = []
    
    for i, date in enumerate(dates):
        day_of_week = date.dayofweek
        base_revenue = 40000 + (i * growth_rate)
        seasonal_mult = seasonality[day_of_week]
        noise = np.random.normal(0, 3000)
        
        # Calculate daily revenue
        daily_revenue = max(5000, round((base_revenue * seasonal_mult) + noise, 2))
        revenue_list.append(daily_revenue)
        
        # Daily orders: correlated with revenue (~$40 per order on average) + noise
        daily_orders = max(100, int((daily_revenue / 40) + np.random.normal(0, 50)))
        orders_list.append(daily_orders)
        
    df = pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'revenue': revenue_list,
        'orders': orders_list
    })
    
    df.to_csv(filepath, index=False)
    logging.info(f"Successfully generated {periods} days of data.")
    return df


def load_and_preprocess_data(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Ingest daily time-series data and convert date column to datetime type.
    
    Args:
        filepath: Path to daily revenue CSV file.
        
    Returns:
        pd.DataFrame: DataFrame with date column as datetime type.
    """
    logging.info(f"Loading data from {filepath}")
    if not os.path.exists(filepath):
        generate_time_series_data(filepath)
        
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    logging.info(f"Loaded {len(df)} records. Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    return df


def handle_missing_gaps(df: pd.DataFrame, gap_fraction: float = 0.05) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Demonstrate missing data handling in time-series:
    1. Introduce artificial gaps (missing dates).
    2. Reindex to a complete daily calendar.
    3. Fill the gaps using forward fill and linear interpolation.
    
    Args:
        df: Clean, complete daily DataFrame.
        gap_fraction: Fraction of daily records to drop.
        
    Returns:
        tuple of (df_with_gaps, df_reindexed_and_filled)
    """
    logging.info("--- Handling Gaps in Time-Series Data ---")
    np.random.seed(42)
    
    # 1. Create a copy and drop random records to simulate missing days
    df_gaps = df.copy()
    drop_indices = np.random.choice(df_gaps.index, size=int(len(df_gaps) * gap_fraction), replace=False)
    df_gaps = df_gaps.drop(drop_indices).sort_values('date').reset_index(drop=True)
    logging.info(f"Introduced gaps: {len(df) - len(df_gaps)} missing days.")
    
    # 2. Reindex to full calendar range
    full_date_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
    df_ts_gaps = df_gaps.set_index('date')
    df_reindexed = df_ts_gaps.reindex(full_date_range)
    
    logging.info(f"Reindexed to full frequency. Null values count before filling: {df_reindexed['revenue'].isnull().sum()}")
    
    # 3. Fill gaps using different strategies
    # For reporting, we will use linear interpolation for revenue and forward-fill for orders
    df_filled = df_reindexed.copy()
    df_filled['revenue'] = df_filled['revenue'].interpolate(method='linear')
    df_filled['orders'] = df_filled['orders'].ffill()
    
    # Check if there are any remaining nulls (e.g. at the start of series for bfill)
    if df_filled['orders'].isnull().any():
        df_filled['orders'] = df_filled['orders'].bfill()
        
    logging.info(f"Gaps filled. Null values count after filling: {df_filled['revenue'].isnull().sum()}")
    
    # Reset index to restore 'date' column
    df_filled = df_filled.reset_index().rename(columns={'index': 'date'})
    return df_gaps, df_filled


def resample_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Task 1: Resample daily data into weekly and monthly buckets.
    
    Args:
        df: Preprocessed DataFrame with a date column.
        
    Returns:
        tuple of (weekly_metrics, monthly_metrics)
    """
    logging.info("--- Task 1: Resampling Data by Time Period ---")
    
    # Set date as index for resampling
    df_ts = df.set_index('date')
    
    # Weekly aggregation: sum of revenue, count of daily records, mean of daily revenue
    weekly_revenue = df_ts['revenue'].resample('W').sum()
    weekly_count = df_ts['orders'].resample('W').count()
    weekly_avg = df_ts['revenue'].resample('W').mean()
    
    weekly_metrics = pd.DataFrame({
        'weekly_revenue': weekly_revenue,
        'daily_records_count': weekly_count,
        'weekly_avg_daily_revenue': weekly_avg
    })
    
    # Monthly aggregation: sum of revenue, count of daily records, mean of daily revenue
    monthly_revenue = df_ts['revenue'].resample('M').sum()
    monthly_count = df_ts['orders'].resample('M').count()
    monthly_avg = df_ts['revenue'].resample('M').mean()
    
    monthly_metrics = pd.DataFrame({
        'monthly_revenue': monthly_revenue,
        'daily_records_count': monthly_count,
        'monthly_avg_daily_revenue': monthly_avg
    })
    
    # Compare results to find period of highest revenue
    highest_weekly_val = weekly_metrics['weekly_revenue'].max()
    highest_weekly_date = weekly_metrics['weekly_revenue'].idxmax().date()
    
    highest_monthly_val = monthly_metrics['monthly_revenue'].max()
    highest_monthly_date = monthly_metrics['monthly_revenue'].idxmax().strftime('%B %Y')
    
    logging.info(f"Highest Weekly Revenue: ${highest_weekly_val:,.2f} (Week ending {highest_weekly_date})")
    logging.info(f"Highest Monthly Revenue: ${highest_monthly_val:,.2f} ({highest_monthly_date})")
    
    return weekly_metrics, monthly_metrics


def compute_rolling_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 2: Compute 7-day and 30-day rolling window averages of daily revenue.
    
    Args:
        df: Daily DataFrame.
        
    Returns:
        pd.DataFrame: DataFrame enriched with 'revenue_ma7' and 'revenue_ma30'.
    """
    logging.info("--- Task 2: Computing Rolling Window Averages ---")
    df_out = df.copy()
    df_out['revenue_ma7'] = df_out['revenue'].rolling(window=7, min_periods=1).mean()
    df_out['revenue_ma30'] = df_out['revenue'].rolling(window=30, min_periods=1).mean()
    
    logging.info("Successfully computed 7-day and 30-day moving averages.")
    return df_out


def calculate_mom_change(monthly_metrics: pd.DataFrame) -> pd.Series:
    """
    Task 3: Calculate Month-over-Month percentage change.
    
    Args:
        monthly_metrics: Monthly aggregated DataFrame.
        
    Returns:
        pd.Series: MoM percentage changes.
    """
    logging.info("--- Task 3: Calculating Month-over-Month Percentage Change ---")
    monthly_revenue = monthly_metrics['monthly_revenue']
    mom_change = monthly_revenue.pct_change() * 100
    
    growth_months = mom_change[mom_change > 0]
    decline_months = mom_change[mom_change < 0]
    
    logging.info(f"Growth Months:\n{growth_months}")
    logging.info(f"Decline Months:\n{decline_months}")
    
    return mom_change


def compute_cumulative_sum(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 4: Compute cumulative sum of revenue over time.
    
    Args:
        df: Daily DataFrame.
        
    Returns:
        pd.DataFrame: DataFrame enriched with 'cumulative_revenue'.
    """
    logging.info("--- Task 4: Computing Cumulative Sum ---")
    df_out = df.copy()
    df_out['cumulative_revenue'] = df_out['revenue'].cumsum()
    
    total_rev = df_out['cumulative_revenue'].iloc[-1]
    logging.info(f"Total revenue accumulated by end of period: ${total_rev:,.2f}")
    return df_out


def analyze_trends(df: pd.DataFrame, mom_change: pd.Series) -> str:
    """
    Task 5: Identify Trend Pattern and Business Implications.
    
    Args:
        df: Enriched daily DataFrame with rolling averages.
        mom_change: Monthly percentage change Series.
        
    Returns:
        str: Formatted trend analysis text.
    """
    logging.info("--- Task 5: Identifying Trend Pattern and Business Implications ---")
    
    # Analyze rolling average trend over the last 30 days
    recent_ma30 = df['revenue_ma30'].iloc[-30:]
    trend_direction = 'up' if recent_ma30.iloc[-1] > recent_ma30.iloc[0] else 'down'
    trend_magnitude = ((recent_ma30.iloc[-1] - recent_ma30.iloc[0]) / recent_ma30.iloc[0]) * 100
    
    # Calculate revenue volatility (standard deviation as a measure of daily noise)
    revenue_volatility = df['revenue'].std()
    
    # Prepare monthly MoM text
    mom_details = []
    for idx, val in mom_change.items():
        month_name = idx.strftime('%B %Y')
        if pd.isna(val):
            mom_details.append(f"- {month_name}: N/A (Baseline Month)")
        else:
            mom_details.append(f"- {month_name}: {val:+.1f}% MoM change")
    
    mom_details_str = "\n".join(mom_details)
    
    # Determine business implications
    if trend_direction == 'up':
        implication = "Accelerating growth - maintain current strategy"
        action = "Capitalize on positive momentum. Scale marketing spend, optimize inventory levels for high demand, and avoid unnecessary discounting."
    else:
        implication = "Declining momentum - investigate causes"
        action = "Investigate drivers of decline. Audit customer churn rates, conduct competitor price benchmarking, and design targeted promotional offers."
        
    analysis = f"""TIME-SERIES TREND ANALYSIS REPORT
=================================

1. ROLLING AVERAGE TREND (LAST 30 DAYS)
---------------------------------------
- Trend Direction: {trend_direction.upper()}
- Magnitude of Change: {trend_magnitude:+.1f}%
- Volatility (Standard Deviation of Daily Revenue): ${revenue_volatility:,.0f}
  *High volatility indicates substantial daily noise (e.g. Tuesday drop vs Sunday surge), justifying the use of rolling averages to isolate the true trend.

2. PERIOD-OVER-PERIOD MONTHLY PERFORMANCE
------------------------------------------
{mom_details_str}

3. BUSINESS IMPLICATIONS & STRATEGIC RECOMMENDATIONS
----------------------------------------------------
- Conclusion: {implication}
- Recommended Action: {action}
"""
    return analysis


def plot_metrics(df: pd.DataFrame) -> None:
    """
    Save analytical visualizations to disk.
    
    Args:
        df: Enriched daily DataFrame.
    """
    if not HAS_PLOTTING:
        logging.warning("Matplotlib is not installed. Skipping plot generation.")
        return
        
    logging.info("Generating plots...")
    
    # Plot 1: Raw vs 7-day MA vs 30-day MA
    plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['revenue'], label='Raw Daily Revenue', color='#A2C2E8', alpha=0.5, linewidth=1)
    plt.plot(df['date'], df['revenue_ma7'], label='7-Day Moving Average', color='#1F77B4', linewidth=2)
    plt.plot(df['date'], df['revenue_ma30'], label='30-Day Moving Average', color='#FF7F0E', linewidth=2.5)
    
    plt.title('Daily Revenue Trend: Raw vs. Rolling Averages', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Revenue ($)', fontsize=12)
    plt.grid(axis='both', linestyle='--', alpha=0.5)
    plt.legend(frameon=True, fontsize=10)
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"${int(x/1000)}k"))
    plt.tight_layout()
    plt.savefig(ROLLING_PLOT_PATH, dpi=300)
    plt.close()
    logging.info(f"Saved rolling average plot to {ROLLING_PLOT_PATH}")
    
    # Plot 2: Cumulative Revenue over time
    plt.figure(figsize=(10, 5))
    plt.plot(df['date'], df['cumulative_revenue'], color='#2CA02C', linewidth=2.5, label='Cumulative Revenue')
    plt.fill_between(df['date'], df['cumulative_revenue'], color='#2CA02C', alpha=0.1)
    
    plt.title('Cumulative Revenue Growth Over Time', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Accumulated Revenue ($)', fontsize=12)
    plt.grid(axis='both', linestyle='--', alpha=0.5)
    plt.legend(loc='upper left', frameon=True, fontsize=10)
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"${x:,.0f}"))
    plt.tight_layout()
    plt.savefig(CUMULATIVE_PLOT_PATH, dpi=300)
    plt.close()
    logging.info(f"Saved cumulative revenue plot to {CUMULATIVE_PLOT_PATH}")


def main() -> None:
    """Run the complete time-series analysis pipeline."""
    logging.info("=== STARTING TIME-SERIES AND ROLLING METRICS PIPELINE ===")
    
    # Generate data if missing
    if not os.path.exists(RAW_DATA_PATH):
        generate_time_series_data(RAW_DATA_PATH)
        
    # Ingest
    df = load_and_preprocess_data(RAW_DATA_PATH)
    
    # Handle missing gaps demo (we keep df clean for main reporting, but run this to verify gap handling works)
    _, df_filled = handle_missing_gaps(df)
    
    # Resample
    weekly_metrics, monthly_metrics = resample_data(df)
    
    # Compute Rolling Averages
    df = compute_rolling_averages(df)
    
    # Calculate MoM Percentage Changes
    mom_change = calculate_mom_change(monthly_metrics)
    
    # Compute Cumulative Sum
    df = compute_cumulative_sum(df)
    
    # Analyze trends and business implications
    analysis_text = analyze_trends(df, mom_change)
    print("\n" + analysis_text)
    
    # Save trend analysis text file
    with open(TREND_TXT_PATH, 'w') as f:
        f.write(analysis_text)
    logging.info(f"Saved trend analysis report to {TREND_TXT_PATH}")
    
    # Generate Plots
    plot_metrics(df)
    
    logging.info("=== TIME-SERIES AND ROLLING METRICS PIPELINE COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
