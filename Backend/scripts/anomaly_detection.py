from __future__ import annotations

import os
import sys
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Paths
RAW_DATA_PATH = "data/raw/anomaly_monitoring_data.csv"
OUTPUT_DIR = "output"
LOG_CSV_PATH = os.path.join(OUTPUT_DIR, "anomalies_log.csv")
PLOT_PATH = os.path.join(OUTPUT_DIR, "anomaly_detection.png")
LOG_FILE = os.path.join(OUTPUT_DIR, "anomaly_detection.log")

# Ensure directories exist
os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

# Threshold Rules
ALERT_RULES = {
    'daily_revenue': {'min': 5000, 'max': 50000},
    'transaction_count': {'min': 100, 'max': 10000},
    'signup_rate': {'min': 10, 'max': 500}
}


def generate_anomaly_data(filepath: str = RAW_DATA_PATH, n_days: int = 60) -> pd.DataFrame:
    """
    Generate synthetic daily time-series data with injected operational anomalies.
    
    Args:
        filepath: Output CSV file path.
        n_days: Number of daily records.
        
    Returns:
        pd.DataFrame: Generated dataset.
    """
    logging.info(f"Generating synthetic daily anomaly monitoring data at {filepath} ({n_days} days)")
    np.random.seed(42)
    
    dates = pd.date_range(end=pd.Timestamp("2026-07-23"), periods=n_days, freq='D')
    
    # Baseline normal distributions
    base_revenue = np.random.normal(10000, 1000, size=n_days)
    base_tx_count = np.random.normal(500, 50, size=n_days)
    base_signups = np.random.normal(150, 20, size=n_days)
    
    df = pd.DataFrame({
        'date': dates,
        'daily_revenue': np.round(base_revenue, 2),
        'transaction_count': np.round(base_tx_count).astype(int),
        'signup_rate': np.round(base_signups).astype(int)
    })
    
    # Inject specific realistic anomalies for testing:
    # 1. Day 15: Silent payment gateway failure (revenue drops to $2,000, tx_count drops to 50)
    if len(df) > 14:
        df.loc[14, 'daily_revenue'] = 2000.0
        df.loc[14, 'transaction_count'] = 50
    
    # 2. Day 35: Viral marketing surge (signups surge to 650, tx_count surges to 12,000)
    if len(df) > 34:
        df.loc[34, 'signup_rate'] = 650
        df.loc[34, 'transaction_count'] = 12000
    
    # 3. Day 50: Suspicious revenue spike (4.5x normal: revenue spikes to $48,000)
    if len(df) > 49:
        df.loc[49, 'daily_revenue'] = 48000.0
    
    df['date'] = pd.to_datetime(df['date'])
    df.to_csv(filepath, index=False)
    logging.info(f"Saved generated anomaly dataset ({len(df)} records).")
    return df


def load_data(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Ingest daily monitoring data and set date index.
    
    Args:
        filepath: CSV file path.
        
    Returns:
        pd.DataFrame.
    """
    logging.info(f"Loading anomaly monitoring data from {filepath}")
    if not os.path.exists(filepath):
        generate_anomaly_data(filepath)
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    logging.info(f"Loaded {len(df)} daily metric records.")
    return df


def check_thresholds(metrics: dict[str, float], rules: dict[str, dict[str, float]] = ALERT_RULES) -> list[dict[str, str | float]]:
    """
    Task 1: Threshold-Based Anomaly Detection.
    
    Args:
        metrics: Current metric values dictionary.
        rules: Alert rules dictionary with min and max boundaries.
        
    Returns:
        list[dict]: List of generated threshold alerts.
    """
    logging.info("--- Task 1: Evaluating Threshold-Based Alerts ---")
    alerts = []
    for metric_name, rule in rules.items():
        if metric_name not in metrics:
            continue
        val = metrics[metric_name]
        min_val = rule['min']
        max_val = rule['max']
        
        if val < min_val:
            alerts.append({
                'metric': metric_name,
                'value': val,
                'threshold': min_val,
                'direction': 'BELOW_MIN',
                'severity': 'HIGH'
            })
        elif val > max_val:
            alerts.append({
                'metric': metric_name,
                'value': val,
                'threshold': max_val,
                'direction': 'ABOVE_MAX',
                'severity': 'MEDIUM'
            })
            
    logging.info(f"Generated {len(alerts)} threshold alert(s).")
    return alerts


def detect_anomalies_zscore(series: pd.Series, threshold: float = 2.0) -> tuple[pd.Series, pd.Series]:
    """
    Task 2: Statistical Anomaly Detection using Z-Score.
    
    Args:
        series: Pandas Series of metric values over time.
        threshold: Standard deviation multiplier cutoff.
        
    Returns:
        tuple[pd.Series, pd.Series]: (anomalies_series, z_scores_series)
    """
    logging.info(f"--- Task 2: Statistical Z-Score Detection (Threshold: {threshold} sigma) ---")
    mean = series.mean()
    std = series.std()
    
    if std == 0:
        z_scores = pd.Series(0, index=series.index)
    else:
        z_scores = (series - mean).abs() / std
        
    anomalies = series[z_scores > threshold]
    logging.info(f"Detected {len(anomalies)} statistical anomalies out of {len(series)} data points.")
    return anomalies, z_scores


def classify_severity(value: float, mean: float, std: float) -> str:
    """
    Task 3: Categorize anomaly severity level based on Z-score standard deviation multiplier.
    
    Args:
        value: Observed metric value.
        mean: Historical mean.
        std: Historical standard deviation.
        
    Returns:
        str: Severity rating ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')
    """
    if std == 0:
        return 'LOW'
    z_score = abs((value - mean) / std)
    
    if z_score > 3.0:
        return 'CRITICAL'
    elif z_score > 2.0:
        return 'HIGH'
    elif z_score > 1.5:
        return 'MEDIUM'
    else:
        return 'LOW'


def log_anomalies(df: pd.DataFrame, metric_col: str = 'daily_revenue', output_csv: str = LOG_CSV_PATH) -> pd.DataFrame:
    """
    Task 4: Anomaly Logging and Audit Trail persistence.
    
    Args:
        df: Input DataFrame with date and metric values.
        metric_col: Name of column to monitor.
        output_csv: Path to save persistent audit log CSV.
        
    Returns:
        pd.DataFrame: Audit log DataFrame.
    """
    logging.info("--- Task 4: Logging Anomalies to Audit Trail ---")
    series = df.set_index('date')[metric_col]
    
    # 30-day lookback window analysis
    lookback_series = series.tail(30)
    mean = lookback_series.mean()
    std = lookback_series.std()
    
    anomalies, z_scores = detect_anomalies_zscore(lookback_series, threshold=2.0)
    
    anomaly_log = []
    now_ts = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for date_val, value in anomalies.items():
        severity = classify_severity(value, mean, std)
        date_str = pd.to_datetime(date_val).strftime('%Y-%m-%d')
        min_range = mean - 2 * std
        max_range = mean + 2 * std
        
        anomaly_log.append({
            'timestamp': now_ts,
            'anomaly_date': date_str,
            'metric': metric_col,
            'value': round(float(value), 2),
            'expected_range': f"{min_range:.0f}-{max_range:.0f}",
            'z_score': round(float(z_scores[date_val]), 2),
            'severity': severity,
            'status': 'OPEN'
        })
        
    anomalies_df = pd.DataFrame(anomaly_log)
    anomalies_df.to_csv(output_csv, index=False)
    
    logging.info(f"Saved {len(anomalies_df)} logged anomalies to {output_csv}")
    return anomalies_df


def visualize_anomalies(df: pd.DataFrame, metric_col: str = 'daily_revenue', output_path: str = PLOT_PATH) -> None:
    """
    Task 5: Visualization with Flagged Points and shaded ±2σ expected range.
    
    Args:
        df: Monitoring DataFrame.
        metric_col: Metric column name.
        output_path: Path to save PNG image.
    """
    logging.info(f"--- Task 5: Visualizing Time-Series Anomalies to {output_path} ---")
    
    series_df = df.copy()
    series_df = series_df.sort_values('date').reset_index(drop=True)
    
    series = series_df.set_index('date')[metric_col].tail(30)
    anomalies, z_scores = detect_anomalies_zscore(series, threshold=2.0)
    
    mean = series.mean()
    std = series.std()
    rolling_avg = series.rolling(window=7).mean()
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # 1. Raw Data
    ax.plot(series.index, series.values, marker='o', label='Daily Revenue ($)', color='#2563eb', linewidth=2)
    
    # 2. 7-day Rolling Average
    ax.plot(rolling_avg.index, rolling_avg.values, label='7-day Moving Average', color='#059669', linewidth=2, linestyle='--')
    
    # 3. Shade Expected Range ±2σ
    ax.fill_between(series.index, mean - 2*std, mean + 2*std, alpha=0.15, color='#3b82f6', label='Expected Range (±2σ)')
    
    # 4. Highlight Anomalies with Red 'X'
    for date_val, val in anomalies.items():
        ax.scatter(date_val, val, color='#dc2626', s=180, marker='X', zorder=5)
        ax.annotate(
            'ANOMALY',
            (date_val, val),
            xytext=(0, 12),
            textcoords='offset points',
            ha='center',
            fontweight='bold',
            color='#991b1b',
            fontsize=9
        )
        
    ax.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax.set_ylabel('Revenue ($)', fontsize=11, fontweight='bold')
    ax.set_title('Automated KPI Anomaly Monitoring Dashboard', fontsize=14, fontweight='bold', pad=15)
    ax.legend(loc='upper left', frameon=True)
    ax.grid(True, linestyle=':', alpha=0.5)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logging.info("Saved visualization plot successfully.")


def main() -> None:
    """Run complete anomaly detection workflow."""
    logging.info("=== STARTING ANOMALY DETECTION PIPELINE ===")
    
    # 1. Ingest Data
    df = load_data(RAW_DATA_PATH)
    
    # 2. Threshold Alerts (Task 1)
    today_metrics = {
        'daily_revenue': float(df.iloc[-1]['daily_revenue']),
        'transaction_count': float(df.iloc[-1]['transaction_count']),
        'signup_rate': float(df.iloc[-1]['signup_rate'])
    }
    threshold_alerts = check_thresholds(today_metrics, ALERT_RULES)
    
    print("\n=== THRESHOLD-BASED ALERT EVALUATION ===")
    if threshold_alerts:
        for alert in threshold_alerts:
            print(f"[ALERT] {alert['metric']} {alert['direction']}: {alert['value']} (Threshold: {alert['threshold']})")
    else:
        print("[OK] All metrics within threshold rules.")
        
    # 3. Statistical Z-Score Detection & Severity Classification (Task 2 & 3)
    series_30d = df.set_index('date')['daily_revenue'].tail(30)
    anomalies, z_scores = detect_anomalies_zscore(series_30d, threshold=2.0)
    mean_30d = series_30d.mean()
    std_30d = series_30d.std()
    
    print(f"\n=== STATISTICAL ANOMALY DETECTION (30-DAY LOOKBACK) ===")
    print(f"Detected {len(anomalies)} anomalies out of {len(series_30d)} days:")
    
    severity_records = []
    for d_val, val in anomalies.items():
        sev = classify_severity(val, mean_30d, std_30d)
        d_str = pd.to_datetime(d_val).strftime('%Y-%m-%d')
        severity_records.append({
            'date': d_str,
            'value': f"${val:,.2f}",
            'z_score': f"{z_scores[d_val]:.2f}",
            'severity': sev
        })
        print(f"  - {d_str}: ${val:,.2f} (z-score: {z_scores[d_val]:.2f}, Severity: {sev})")
        
    sev_df = pd.DataFrame(severity_records)
    high_critical = sev_df[sev_df['severity'].isin(['CRITICAL', 'HIGH'])]
    print(f"\n[ALERT] {len(high_critical)} Critical/High severity anomalies require immediate investigation.")
    
    # 4. Anomaly Audit Log (Task 4)
    log_df = log_anomalies(df, metric_col='daily_revenue')
    print("\n=== PERSISTED ANOMALY AUDIT TRAIL ===")
    print(log_df[['anomaly_date', 'metric', 'value', 'expected_range', 'z_score', 'severity', 'status']])
    
    # 5. Visualization (Task 5)
    visualize_anomalies(df, metric_col='daily_revenue')
    
    logging.info("=== ANOMALY DETECTION PIPELINE COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
