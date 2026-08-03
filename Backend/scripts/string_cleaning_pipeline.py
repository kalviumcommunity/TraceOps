"""
String Cleaning & Text Normalization Pipeline.

This module implements a reusable string cleaning pipeline that strips whitespace,
normalizes casing, removes special characters with regex, standardizes categorical
labels via dictionary mapping, and provides a modular column cleaner.
"""

import os
import pandas as pd


RAW_DATA_PATH = "data/raw/messy_string_data.csv"
PROCESSED_DATA_PATH = "data/processed/cleaned_string_data.csv"


def strip_all_strings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 1: Strip leading and trailing whitespace from all string/object columns.

    Args:
        df: Input pandas DataFrame.

    Returns:
        DataFrame with stripped string columns and printed consolidation stats.
    """
    df_cleaned = df.copy()
    string_cols = df_cleaned.select_dtypes(include=['object', 'string']).columns

    print("\n--- Task 1: Stripping Whitespace ---")
    summary = []
    for col in string_cols:
        # Count non-null unique before
        before_unique = df_cleaned[col].nunique(dropna=True)
        before_whitespace_count = df_cleaned[col].dropna().apply(lambda x: len(str(x)) != len(str(x).strip())).sum()

        # Apply strip
        df_cleaned[col] = df_cleaned[col].str.strip()

        # Count after
        after_unique = df_cleaned[col].nunique(dropna=True)
        summary.append({
            "column": col,
            "before_unique": before_unique,
            "after_unique": after_unique,
            "whitespace_issues_fixed": before_whitespace_count
        })
        print(f"[OK] Column '{col}': {before_unique} -> {after_unique} unique values ({before_whitespace_count} rows fixed)")

    summary_df = pd.DataFrame(summary)
    total_fixed = summary_df['whitespace_issues_fixed'].sum()
    print(f"Total whitespace issues resolved across dataset: {total_fixed}")
    return df_cleaned


def normalize_casing(df: pd.DataFrame, columns_to_lower: list) -> pd.DataFrame:
    """
    Task 2: Normalize casing for specified categorical text columns to lowercase.

    Business Decision:
    Normalizing all categorical and name strings to lower case ensures consistent
    grouping and exact-match deduplication. Databases and analytical pipelines treat
    "JOHN", "john", and "John" as distinct entities if casing is not standardized.

    Args:
        df: Input DataFrame.
        columns_to_lower: List of column names to convert to lowercase.

    Returns:
        DataFrame with normalized casing.
    """
    df_cleaned = df.copy()
    print("\n--- Task 2: Normalizing Casing ---")

    for col in columns_to_lower:
        if col in df_cleaned.columns:
            before_unique = df_cleaned[col].nunique()
            df_cleaned[col] = df_cleaned[col].str.lower()
            after_unique = df_cleaned[col].nunique()
            print(f"[OK] Column '{col}' normalized to lowercase: {before_unique} -> {after_unique} unique values")
        else:
            print(f"[WARNING] Column '{col}' not found in DataFrame.")

    return df_cleaned


def remove_special_characters(df: pd.DataFrame, columns: list, regex_pattern: str = r'[^a-zA-Z0-9 ]') -> pd.DataFrame:
    """
    Task 3: Remove special non-alphanumeric characters using regex.

    Regex Explanation:
    Pattern `[^a-zA-Z0-9 ]`:
      - `[` `]` defines a character set.
      - `^` at start of character set means "NOT" (negation).
      - `a-z` matches lowercase letters, `A-Z` uppercase, `0-9` digits, and ` ` space.
      - Together, `[^a-zA-Z0-9 ]` matches any character that is NOT a letter, number, or space.
      - Non-ASCII/accented characters like 'ã', 'é', '!' are replaced with empty strings.

    Args:
        df: Input DataFrame.
        columns: List of columns from which to remove special characters.
        regex_pattern: Regex pattern identifying characters to strip out.

    Returns:
        DataFrame with special characters removed.
    """
    df_cleaned = df.copy()
    print("\n--- Task 3: Removing Special Characters with Regex ---")

    for col in columns:
        if col in df_cleaned.columns:
            # Show sample before
            sample_before = df_cleaned[col].dropna().head(3).tolist()
            df_cleaned[col] = df_cleaned[col].str.replace(regex_pattern, '', regex=True)
            sample_after = df_cleaned[col].dropna().head(3).tolist()
            print(f"[OK] Removed special characters from '{col}' using regex '{regex_pattern}'")
            print(f"  Before sample: {sample_before}")
            print(f"  After sample:  {sample_after}")

    return df_cleaned


def standardize_categories(df: pd.DataFrame, column: str, mapping: dict) -> pd.DataFrame:
    """
    Task 4: Standardize categorical labels using mapping dictionary.

    Business Rationale:
    1. B2B variations ('b2b', 'b 2 b', 'b2 b', 'business-to-business') map to 'B2B' for alignment with CRM systems.
    2. SMB variations ('sme', 'small medium enterprise') map to 'SMB' (Small-Medium Business) for standard financial reporting.
    3. Enterprise variations ('enterprise', 'Enterprise') map to 'Enterprise' for canonical tier classification.

    Args:
        df: Input DataFrame.
        column: Column name to standardize.
        mapping: Dictionary mapping original text variations to canonical forms.

    Returns:
        DataFrame with mapped category values.
    """
    df_cleaned = df.copy()
    print(f"\n--- Task 4: Standardizing Categorical Labels on '{column}' ---")

    if column not in df_cleaned.columns:
        print(f"[WARNING] Column '{column}' not found.")
        return df_cleaned

    print("Value counts BEFORE mapping:")
    print(df_cleaned[column].value_counts(dropna=False))

    # Apply mapping with fallback to original if not in mapping dictionary
    df_cleaned[column] = df_cleaned[column].map(mapping).fillna(df_cleaned[column])

    print("\nValue counts AFTER mapping:")
    print(df_cleaned[column].value_counts(dropna=False))

    return df_cleaned


def clean_text_column(series: pd.Series,
                      lowercase: True = True,
                      strip: bool = True,
                      remove_special: bool = False,
                      mapping: dict = None) -> pd.Series:
    """
    Task 5: Reusable modular text cleaning function for any pandas Series.

    Handles null values, strips whitespace, converts casing, strips special characters,
    and applies category mapping dictionaries cleanly.

    Args:
        series: Pandas Series to clean.
        lowercase: Whether to convert text to lowercase.
        strip: Whether to strip leading/trailing whitespace.
        remove_special: Whether to strip special characters using regex.
        mapping: Optional dictionary for value replacement/mapping.

    Returns:
        Cleaned pandas Series.
    """
    result = series.copy()

    if result.isna().any():
        null_count = result.isna().sum()
        print(f"Notice: {null_count} null/missing values found in column '{series.name}'. Preserving nulls.")

    # Convert to string accessor safely while preserving NaNs
    if strip:
        result = result.str.strip()

    if lowercase:
        result = result.str.lower()

    if remove_special:
        result = result.str.replace(r'[^a-zA-Z0-9 ]', '', regex=True)

    if mapping:
        # map() replaces unmapped keys with NaN, so fallback to original series values
        mapped_result = result.map(mapping)
        result = mapped_result.fillna(result)

    return result


def test_pipeline_edge_cases():
    """Execute edge-case test suite as required by assignment instructions."""
    print("\n--- Edge Case Testing ---")
    test_cases = [
        '  Product A  ',   # Leading/trailing spaces
        'PRODUCT B',      # All caps
        'Product_C',      # Special char
        None,             # Null value
        ''                # Empty string
    ]

    test_series = pd.Series(test_cases, name="test_column")
    print("Raw test series:")
    print(test_series.to_list())

    cleaned_series = clean_text_column(
        test_series,
        lowercase=True,
        strip=True,
        remove_special=True
    )

    print("\nCleaned test series:")
    print(cleaned_series.to_list())
    return cleaned_series


def main():
    """Run full string cleaning pipeline end-to-end."""
    print("=" * 60)
    print("  TraceOps Data Cleaning: String Normalization Pipeline")
    print("=" * 60)

    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"Raw data file not found at {RAW_DATA_PATH}")

    df = pd.read_csv(RAW_DATA_PATH)
    print(f"Loaded raw dataset with {len(df)} rows and {len(df.columns)} columns.")

    # Step 1: Task 1 - Strip Whitespace
    df_step1 = strip_all_strings(df)

    # Step 2: Task 2 - Normalize Casing
    casing_cols = ['customer_name', 'product_category', 'customer_segment']
    df_step2 = normalize_casing(df_step1, casing_cols)

    # Step 3: Task 3 - Remove Special Characters with Regex
    special_char_cols = ['city', 'customer_name']
    df_step3 = remove_special_characters(df_step2, special_char_cols)

    # Step 4: Task 4 - Standardize Categorical Labels
    segment_map = {
        'b2b': 'B2B',
        'b 2 b': 'B2B',
        'b2 b': 'B2B',
        'business-to-business': 'B2B',
        'sme': 'SMB',
        'small medium enterprise': 'SMB',
        'smb': 'SMB',
        'enterprise': 'Enterprise'
    }
    df_step4 = standardize_categories(df_step3, 'customer_segment', segment_map)

    # Step 5: Task 5 - Reusable Function Demonstration
    print("\n--- Task 5: Applying Reusable Function across Multiple Columns ---")
    df_step5 = df.copy()
    df_step5['customer_name'] = clean_text_column(df_step5['customer_name'], lowercase=True, strip=True, remove_special=True)
    df_step5['product_category'] = clean_text_column(df_step5['product_category'], lowercase=True, strip=True)
    df_step5['customer_segment'] = clean_text_column(df_step5['customer_segment'], lowercase=True, strip=True, mapping=segment_map)

    # Run Edge-Case tests
    test_pipeline_edge_cases()

    # Save output dataset
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
    df_step4.to_csv(PROCESSED_DATA_PATH, index=False)
    print(f"\n[OK] Successfully exported cleaned dataset to: {PROCESSED_DATA_PATH}")


if __name__ == '__main__':
    main()
