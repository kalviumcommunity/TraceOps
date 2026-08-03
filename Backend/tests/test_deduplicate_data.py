import json
import os
import pandas as pd
import numpy as np
from scripts.deduplicate_data import (
    detect_exact_duplicates,
    detect_near_duplicates,
    remove_exact_duplicates,
    remove_near_duplicates,
    log_removed_duplicates,
    compare_before_after,
)

def test_deduplication_pipeline():
    # Create test dataframe with both exact and near-duplicates
    # Note: 
    # Row 0 & 1: Exact duplicates
    # Row 2 & 3: Near-duplicates (same customer_id and transaction_date, but different amount/status and nulls)
    # Row 4: Unique row
    df = pd.DataFrame([
        {"customer_id": 1, "transaction_date": "2025-01-15", "amount": 100.0, "status": "completed"},
        {"customer_id": 1, "transaction_date": "2025-01-15", "amount": 100.0, "status": "completed"},
        {"customer_id": 2, "transaction_date": "2025-01-20", "amount": 250.0, "status": np.nan},
        {"customer_id": 2, "transaction_date": "2025-01-20", "amount": 250.0, "status": "pending"},
        {"customer_id": 3, "transaction_date": "2025-02-01", "amount": 150.0, "status": "completed"}
    ])
    
    # Store copy of original
    df_original = df.copy()
    
    # Test Task 1: Detect exact duplicates
    exact_count, exact_rows = detect_exact_duplicates(df)
    assert exact_count == 1
    assert len(exact_rows) == 2
    
    # Test Task 2: Detect near-duplicates by key columns
    near_dups = detect_near_duplicates(df, ['customer_id', 'transaction_date'])
    assert len(near_dups) == 4 # Rows 0, 1, 2, 3 have duplicates of keys
    
    # Test Task 3: Remove exact duplicates (keeping first)
    df_dedup_exact = remove_exact_duplicates(df, keep='first')
    assert len(df_dedup_exact) == 4 # Dropped index 1
    # Wait, df.drop_duplicates(keep='first') drops row at index 1
    assert 1 not in df_dedup_exact.index
    
    # Test Task 4: Remove near-duplicates (keeping most complete)
    df_dedup_near = remove_near_duplicates(df_dedup_exact, ['customer_id', 'transaction_date'], keep_strategy='most_complete')
    # For customer_id 2:
    # Row index 2: null status
    # Row index 3: status is "pending" (non-null)
    # The 'most_complete' strategy should keep row index 3 and drop row index 2.
    assert len(df_dedup_near) == 3
    assert 2 not in df_dedup_near.index
    assert 3 in df_dedup_near.index
    
    # Test Task 5: Log removed records
    removed_records, audit_summary = log_removed_duplicates(df_original, df_dedup_near)
    assert len(removed_records) == 2
    assert set(removed_records.index) == {1, 2}
    
    # Test Task 6: Compare before and after
    comparison = compare_before_after(df_original, df_dedup_near)
    assert comparison['rows_before'] == 5
    assert comparison['rows_after'] == 3
    assert comparison['rows_removed'] == 2
    assert comparison['removal_percentage'] == 40.0
