"""
Unit tests for String Cleaning & Text Normalization Pipeline.
"""

import pandas as pd
import pytest

from scripts.string_cleaning_pipeline import (
    strip_all_strings,
    normalize_casing,
    remove_special_characters,
    standardize_categories,
    clean_text_column
)


def test_strip_all_strings():
    data = {
        'name': ['  Alice  ', ' Bob', 'Carol '],
        'age': [25, 30, 35]
    }
    df = pd.DataFrame(data)
    cleaned = strip_all_strings(df)
    assert cleaned['name'].tolist() == ['Alice', 'Bob', 'Carol']
    assert cleaned['age'].tolist() == [25, 30, 35]


def test_normalize_casing():
    data = {
        'name': ['JOHN', 'John', 'john']
    }
    df = pd.DataFrame(data)
    cleaned = normalize_casing(df, ['name'])
    assert cleaned['name'].tolist() == ['john', 'john', 'john']
    assert cleaned['name'].nunique() == 1


def test_remove_special_characters():
    data = {
        'city': ['São Paulo', 'Montréal', 'New-York!']
    }
    df = pd.DataFrame(data)
    cleaned = remove_special_characters(df, ['city'])
    assert cleaned['city'].tolist() == ['So Paulo', 'Montral', 'NewYork']


def test_standardize_categories():
    data = {
        'segment': ['b2b', 'b 2 b', 'business-to-business', 'sme', 'enterprise']
    }
    df = pd.DataFrame(data)
    mapping = {
        'b2b': 'B2B',
        'b 2 b': 'B2B',
        'business-to-business': 'B2B',
        'sme': 'SMB',
        'enterprise': 'Enterprise'
    }
    cleaned = standardize_categories(df, 'segment', mapping)
    assert cleaned['segment'].tolist() == ['B2B', 'B2B', 'B2B', 'SMB', 'Enterprise']


def test_clean_text_column_edge_cases():
    test_cases = [
        '  Product A  ',   # Whitespace
        'PRODUCT B',      # Casing
        'Product_C',      # Special char
        None,             # Null
        ''                # Empty string
    ]
    series = pd.Series(test_cases, name='product')
    cleaned = clean_text_column(series, lowercase=True, strip=True, remove_special=True)

    expected = ['product a', 'product b', 'productc', None, '']
    assert cleaned.iloc[0] == expected[0]
    assert cleaned.iloc[1] == expected[1]
    assert cleaned.iloc[2] == expected[2]
    assert pd.isna(cleaned.iloc[3])
    assert cleaned.iloc[4] == expected[4]
