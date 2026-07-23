"""
Data Normalization & Vectorization script using NumPy.
"""

import os
import sys
import time
import numpy as np
import pandas as pd

RAW_DATA_PATH = 'data/raw/outliers_data.csv'
PROCESSED_DATA_PATH = 'data/processed/normalized_data.csv'


def load_data(filepath=RAW_DATA_PATH):
    """Load input dataset from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    df = pd.read_csv(filepath)
    print(f"[LOAD] Ingested {len(df)} records from {filepath}")
    return df


def run_normalization_pipeline(df):
    """
    Execute Tasks 1 to 5 to normalize and rank data using NumPy vectorization.
    """
    print("\n" + "=" * 60)
    print("RUNNING NUMPY NORMALIZATION PIPELINE")
    print("=" * 60)

    # Task 1: Replace Loop with NumPy Vectorization (1 mark)
    print("\n--- Task 1: Replace Loop with NumPy Vectorization ---")
    
    # SLOW: Loop
    normalized_loop = []
    for val in df['revenue']:
        normalized_loop.append((val - df['revenue'].min()) / (df['revenue'].max() - df['revenue'].min()))

    # FAST: NumPy
    revenue_array = df['revenue'].values
    normalized_np = (revenue_array - revenue_array.min()) / (revenue_array.max() - revenue_array.min())
    df['revenue_normalized'] = normalized_np

    # Verify matching
    assert np.allclose(normalized_loop, normalized_np), "Error: Loop and NumPy normalized results do not match!"
    print("OK: Min-Max normalization successfully computed with NumPy vectorization.")
    print("Sample normalized values (first 5):", normalized_np[:5])

    # Task 2: Z-Score Normalization (1 mark)
    print("\n--- Task 2: Z-Score Normalization ---")
    revenue_array = df['revenue'].values
    z_scores = (revenue_array - revenue_array.mean()) / revenue_array.std()
    df['revenue_zscore'] = z_scores
    print("OK: Z-score normalization successfully computed.")
    print("Sample z-scores (first 5):", z_scores[:5])

    # Task 3: Bulk Ranking/Scoring (1 mark)
    print("\n--- Task 3: Bulk Ranking/Scoring ---")
    revenue_array = df['revenue'].values
    rankings = np.argsort(-revenue_array)  # Negative for descending
    ranks = np.empty_like(rankings)
    ranks[rankings] = np.arange(1, len(rankings) + 1)
    df['revenue_rank'] = ranks
    print("OK: 1-indexed rankings successfully computed via argsort.")
    print("1-indexed ranks for rows:", df['revenue_rank'].values)

    # Task 4: Time Performance Comparison (1 mark)
    print("\n--- Task 4: Time Performance Comparison ---")
    # Time loop version
    start = time.time()
    result_loop = []
    for val in df['revenue']:
        result_loop.append(val * 1.1)
    loop_time = time.time() - start

    # Time NumPy version
    start = time.time()
    result_np = df['revenue'].values * 1.1
    np_time = time.time() - start
    
    # Handle extremely small timing divisions safely
    safe_np_time = max(np_time, 1e-9)

    print(f"Loop: {loop_time:.6f}s")
    print(f"NumPy: {np_time:.6f}s")
    print(f"Speedup: {loop_time/safe_np_time:.0f}x")

    # Task 5: Integrate Back to DataFrame (1 mark)
    print("\n--- Task 5: Integrate Back to DataFrame ---")
    df['revenue_normalized'] = normalized_np
    df['revenue_zscore'] = z_scores
    df['revenue_rank'] = rankings  # Explicit Task 5 verbatim assignment

    # Verify types and shapes
    print(f"Shape: {df.shape}")
    print(f"Dtypes:\n{df.dtypes}")

    return df


def main():
    # Force stdout/stderr to use UTF-8 on Windows to prevent UnicodeEncodeError
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    df = load_data()
    df_processed = run_normalization_pipeline(df)
    
    # Save output
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
    df_processed.to_csv(PROCESSED_DATA_PATH, index=False)
    print(f"\n[SUCCESS] Normalized data saved to: {PROCESSED_DATA_PATH}")


if __name__ == "__main__":
    main()
