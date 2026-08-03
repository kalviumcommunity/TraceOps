import pandas as pd

from scripts.enforce_types import (
    cast_columns_to_types,
    compare_dtypes,
    convert_currency_to_float,
    convert_integers_to_boolean,
    convert_string_dates_to_datetime,
)


def test_type_enforcement_pipeline():
    df = pd.DataFrame(
        {
            "transaction_date": ["2025-01-15", "2025-02-20", "2025-03-10"],
            "amount": ["$150.50", "$200.00", "$75.25"],
            "is_active": [1, 0, 1],
            "signup_date": ["2024-01-01", "2024-02-15", "2024-03-01"],
        }
    )

    df_typed = convert_string_dates_to_datetime(df, ["transaction_date", "signup_date"], date_format="%Y-%m-%d")
    df_typed = convert_currency_to_float(df_typed, ["amount"])
    df_typed = convert_integers_to_boolean(df_typed, ["is_active"])

    assert pd.api.types.is_datetime64_any_dtype(df_typed["transaction_date"])
    assert pd.api.types.is_float_dtype(df_typed["amount"])
    assert pd.api.types.is_bool_dtype(df_typed["is_active"])

    comparison = compare_dtypes(df, df_typed)
    assert comparison["changed"].sum() >= 3

    typed_df, conversion_log = cast_columns_to_types(
        df_typed,
        {
            "transaction_date": "datetime64[ns]",
            "amount": "float64",
            "is_active": "bool",
        },
    )
    assert conversion_log["amount"]["status"] == "success"
