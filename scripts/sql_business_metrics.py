"""
SQL Business Metrics Query Design Pipeline.

This script implements Task 1 to Task 5 of the SQL Business Metrics Query Design assignment:
- Task 1: Active Users Metric (monthly_active_users.sql & active_users.sql)
- Task 2: Revenue by Segment (revenue_by_segment.sql)
- Task 3: Funnel Conversion (conversion_funnel.sql)
- Task 4: Call Queries from Python (load_query, pd.read_sql execution)
- Task 5: Validate Query Results (validate_metrics checks nulls, ranges, and consistency)
"""

import os
import sys
import re
import datetime
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DEFAULT_DB_PATH = "analytics.db"
OUTPUT_SUMMARY_PATH = os.path.join("output", "sql_business_metrics_summary.txt")


def setup_database_connection(connection_uri: str = f"sqlite:///{DEFAULT_DB_PATH}") -> Engine:
    """
    Setup database connection using SQLAlchemy.
    """
    engine = create_engine(connection_uri, echo=False)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine


def seed_database_tables(engine: Engine) -> None:
    """
    Populate seed tables (customers, transactions, users) in the database for metric querying.
    """
    # 1. Customers Table
    customers_df = pd.DataFrame({
        'customer_id': [101, 102, 103, 104, 105, 106, 107, 108],
        'customer_type': ['Enterprise', 'Enterprise', 'SMB', 'SMB', 'Startup', 'Enterprise', 'SMB', 'Startup'],
        'email': [f"cust_{i}@example.com" for i in range(101, 109)],
        'signup_date': ['2025-01-10', '2025-01-15', '2025-02-01', '2025-02-10', '2025-03-01', '2025-03-15', '2025-04-01', '2025-04-10']
    })
    customers_df.to_sql('customers', engine, if_exists='replace', index=False)

    # 2. Transactions Table
    today = datetime.date.today()
    dates = [
        (today - datetime.timedelta(days=15)).strftime('%Y-%m-%d'),
        (today - datetime.timedelta(days=20)).strftime('%Y-%m-%d'),
        (today - datetime.timedelta(days=45)).strftime('%Y-%m-%d'),
        (today - datetime.timedelta(days=50)).strftime('%Y-%m-%d'),
        (today - datetime.timedelta(days=75)).strftime('%Y-%m-%d'),
        (today - datetime.timedelta(days=100)).strftime('%Y-%m-%d'),
        (today - datetime.timedelta(days=150)).strftime('%Y-%m-%d'),
        (today - datetime.timedelta(days=200)).strftime('%Y-%m-%d'),
    ]

    transactions_df = pd.DataFrame({
        'order_id': [5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008],
        'customer_id': [101, 102, 103, 104, 105, 106, 101, 103],
        'customer_type': ['Enterprise', 'Enterprise', 'SMB', 'SMB', 'Startup', 'Enterprise', 'Enterprise', 'SMB'],
        'transaction_date': dates,
        'amount': [1250.0, 950.50, 450.0, 300.0, 150.0, 2100.0, 1400.0, 500.0]
    })
    transactions_df.to_sql('transactions', engine, if_exists='replace', index=False)

    # 3. Users Table (Funnel)
    user_dates = [(today - datetime.timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S') for i in range(1, 15)]
    users_df = pd.DataFrame({
        'user_id': range(1, 15),
        'created_at': user_dates,
        'email_verified_at': [
            d if i % 2 == 0 else None for i, d in enumerate(user_dates)
        ],
        'first_purchase_at': [
            d if i % 3 == 0 else None for i, d in enumerate(user_dates)
        ]
    })
    users_df.to_sql('users', engine, if_exists='replace', index=False)


def load_query(query_name: str) -> str:
    """
    Task 4: Load SQL query from file.
    Reads SQL content from queries/{query_name}.sql.
    """
    filepath = os.path.join("queries", f"{query_name}.sql")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Query file not found: {filepath}")
    with open(filepath, "r") as f:
        return f.read()


def adapt_query_for_sqlite(query: str, engine: Engine) -> str:
    """
    Adapts PostgreSQL SQL syntax to SQLite dialect when executing on an SQLite backend.
    """
    if engine.dialect.name == "sqlite":
        q = query
        # 1. Adapt specific interval expressions with NOW()
        q = re.sub(
            r"DATE_TRUNC\('month',\s*NOW\(\)\)\s*-\s*INTERVAL\s*'(\d+)\s*months'",
            r"date('now', 'start of month', '-\1 months')",
            q,
            flags=re.IGNORECASE,
        )
        q = re.sub(
            r"NOW\(\)\s*-\s*INTERVAL\s*'(\d+)\s*months'",
            r"date('now', '-\1 months')",
            q,
            flags=re.IGNORECASE,
        )
        q = re.sub(
            r"NOW\(\)\s*-\s*INTERVAL\s*'(\d+)\s*days'",
            r"date('now', '-\1 days')",
            q,
            flags=re.IGNORECASE,
        )

        # 2. Adapt DATE_TRUNC expressions for dates
        q = re.sub(
            r"DATE_TRUNC\('month',\s*([a-zA-Z0-9_\.]+)\)(\s*::\s*DATE)?",
            r"date(\1, 'start of month')",
            q,
            flags=re.IGNORECASE,
        )
        q = re.sub(
            r"DATE_TRUNC\('day',\s*([a-zA-Z0-9_\.]+)\)(\s*::\s*DATE)?",
            r"date(\1)",
            q,
            flags=re.IGNORECASE,
        )

        # 3. Strip remaining Postgres typecasts
        q = re.sub(r'::DATE', '', q, flags=re.IGNORECASE)
        return q
    return query


def execute_metrics_pipeline(engine: Engine = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Executes the 3 business metric SQL queries and returns result DataFrames.
    """
    if engine is None:
        engine = setup_database_connection()
        seed_database_tables(engine)

    # 1. Load and execute Monthly Active Users query
    mau_query = load_query('monthly_active_users')
    mau_exec = adapt_query_for_sqlite(mau_query, engine)
    mau_df = pd.read_sql(mau_exec, engine)

    # 2. Load and execute Revenue by Segment query
    revenue_query = load_query('revenue_by_segment')
    revenue_exec = adapt_query_for_sqlite(revenue_query, engine)
    revenue_df = pd.read_sql(revenue_exec, engine)

    # 3. Load and execute Conversion Funnel query
    funnel_query = load_query('conversion_funnel')
    funnel_exec = adapt_query_for_sqlite(funnel_query, engine)
    funnel_df = pd.read_sql(funnel_exec, engine)

    return mau_df, revenue_df, funnel_df


def validate_metrics(mau_df: pd.DataFrame, revenue_df: pd.DataFrame, funnel_df: pd.DataFrame) -> bool:
    """
    Task 5: Validate Query Results
    Checks nulls, value ranges, and logical consistency across metric DataFrames.
    """
    # Check for nulls
    assert mau_df.isnull().sum().sum() == 0, "MAU has nulls"
    assert revenue_df.isnull().sum().sum() == 0, "Revenue has nulls"
    assert funnel_df.isnull().sum().sum() == 0, "Funnel has nulls"
    
    # Check value ranges
    assert (revenue_df['monthly_revenue'] > 0).all(), "Revenue <= 0"
    assert (funnel_df['conversion_pct'] >= 0).all() and (funnel_df['conversion_pct'] <= 100).all(), "Conversion out of range"
    
    # Check consistency
    for idx, row in revenue_df.iterrows():
        assert row['order_count'] > 0, "Zero orders"
        assert row['monthly_revenue'] > 0, "Zero revenue"
    
    try:
        print("✓ All metrics validated")
    except UnicodeEncodeError:
        print("[OK] All metrics validated")
    return True


def run_full_pipeline() -> None:
    """
    Run full metric query loading, execution, and validation pipeline.
    """
    os.makedirs("output", exist_ok=True)
    engine = setup_database_connection()
    seed_database_tables(engine)

    mau_df, revenue_df, funnel_df = execute_metrics_pipeline(engine)

    print("=== TASK 1: Monthly Active Users ===")
    print(mau_df)
    print("\n=== TASK 2: Revenue by Segment ===")
    print(revenue_df)
    print("\n=== TASK 3: Conversion Funnel ===")
    print(funnel_df)

    print("\n=== TASK 5: Validating Metrics ===")
    validation_passed = validate_metrics(mau_df, revenue_df, funnel_df)

    # Save summary report
    with open(OUTPUT_SUMMARY_PATH, "w") as f:
        f.write("SQL BUSINESS METRICS QUERY DESIGN - PIPELINE SUMMARY\n")
        f.write("=====================================================\n\n")
        f.write("1. MONTHLY ACTIVE USERS METRIC\n")
        f.write(mau_df.to_string(index=False))
        f.write("\n\n2. REVENUE BY SEGMENT METRIC\n")
        f.write(revenue_df.to_string(index=False))
        f.write("\n\n3. CONVERSION FUNNEL METRIC\n")
        f.write(funnel_df.to_string(index=False))
        f.write(f"\n\nValidation Status: {'PASSED' if validation_passed else 'FAILED'}\n")

    print(f"\nSummary report written to {OUTPUT_SUMMARY_PATH}")


if __name__ == "__main__":
    run_full_pipeline()
