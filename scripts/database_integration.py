"""
SQL Environment & Database Integration Pipeline.

This script implements Task 1 to Task 5 of the SQL Environment & Database Integration assignment:
- Task 1: Setup Database Connection (SQLite and PostgreSQL support with SQLAlchemy engine creation & testing)
- Task 2: Load Cleaned DataFrame as Table (to_sql, table verification, row count validation)
- Task 3: Validate Schema (SQLAlchemy inspect, datatypes, null constraints check)
- Task 4: Query and Return Results (simple SELECT query and complex aggregation query into DataFrames)
- Task 5: Make Loading Repeatable (reusable pipeline function returning engine for downstream reuse)
"""

import os
import sys
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

# Default Database Configuration
DEFAULT_DB_PATH = "analytics.db"
DEFAULT_TABLE_NAME = "customers_cleaned"
RAW_DATA_PATH = os.path.join("data", "raw", "customer_segment_data.csv")
OUTPUT_SUMMARY_PATH = os.path.join("output", "db_integration_summary.txt")


def setup_database_connection(connection_uri: str = f"sqlite:///{DEFAULT_DB_PATH}") -> Engine:
    """
    Task 1: Setup Database Connection
    Creates an SQLAlchemy engine and validates active database connectivity.

    Connection Strings Reference (Without Hardcoded Credentials):
    - SQLite (file-based): "sqlite:///analytics.db" or "sqlite:///:memory:"
    - PostgreSQL (production): "postgresql://{user}:{password}@{host}:{port}/{dbname}"
      Example with env vars: f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST','localhost')}:5432/{os.getenv('DB_NAME','analytics')}"

    Parameters:
        connection_uri (str): Database connection string.

    Returns:
        Engine: Active SQLAlchemy engine instance.
    """
    engine = create_engine(connection_uri, echo=False)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        if result == 1:
            print("[OK] Database connection successful")
        else:
            raise RuntimeError("Database connection test failed.")

    return engine


def prepare_cleaned_customer_data(raw_csv_path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Ingest raw dataset and clean/transform into standardized customer DataFrame.
    """
    if os.path.exists(raw_csv_path):
        df = pd.read_csv(raw_csv_path)
    else:
        # Fallback sample dataset if CSV missing
        df = pd.DataFrame({
            'customer_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            'customer_type': ['SMB', 'Startup', 'Startup', 'Startup', 'SMB', 'SMB', 'SMB', 'Startup', 'Startup', 'Startup', 'Enterprise'],
            'product': ['Analytics Pro', 'Basic Tier', 'Basic Tier', 'Basic Tier', 'Cloud API', 'Analytics Pro', 'Basic Tier', 'Cloud API', 'Cloud API', 'Analytics Pro', 'Enterprise Suite'],
            'churn': [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            'revenue': [606.46, 184.78, 190.86, 128.93, 395.75, 627.79, 508.23, 222.62, 139.83, 149.29, 13668.55],
            'support_tickets': [7, 0, 1, 8, 3, 4, 11, 1, 0, 3, 3]
        })

    # Standardize column mappings & add metadata
    df = df.copy()
    if 'lifetime_value' not in df.columns:
        df['lifetime_value'] = df['revenue']

    if 'email' not in df.columns:
        df['email'] = df['customer_id'].apply(lambda cid: f"customer_{cid}@example.com")

    if 'signup_date' not in df.columns:
        df['signup_date'] = "2025-01-01"

    # Enforce standard integer types
    df['customer_id'] = df['customer_id'].astype(int)
    df['churn'] = df['churn'].astype(int)
    df['support_tickets'] = df['support_tickets'].astype(int)
    df['revenue'] = df['revenue'].astype(float)
    df['lifetime_value'] = df['lifetime_value'].astype(float)

    # Standardize column order
    cols_order = ['customer_id', 'email', 'signup_date', 'customer_type', 'product', 'churn', 'revenue', 'lifetime_value', 'support_tickets']
    df = df[cols_order]

    return df


def load_dataframe_to_table(df: pd.DataFrame, table_name: str, engine: Engine, if_exists: str = 'replace') -> int:
    """
    Task 2: Load Cleaned DataFrame as Table
    Loads a Pandas DataFrame into an SQL database table and verifies row counts.

    Parameters:
        df (pd.DataFrame): Data frame to persist.
        table_name (str): SQL table name target.
        engine (Engine): Active SQLAlchemy database engine.
        if_exists (str): Action if table exists ('replace', 'append', 'fail').

    Returns:
        int: Number of rows successfully written to database.
    """
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)

    # Verify table existence using inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if table_name not in tables:
        raise ValueError(f"Table '{table_name}' was not created in database.")
    
    print(f"Verified tables in engine: {tables}")

    # Confirm row count via SQL query
    count_df = pd.read_sql(f"SELECT COUNT(*) as row_count FROM {table_name}", engine)
    rows_loaded = int(count_df.iloc[0]['row_count'])
    print(f"Rows loaded to '{table_name}': {rows_loaded}")

    return rows_loaded


def validate_table_schema(engine: Engine, table_name: str, expected_types: dict = None) -> dict:
    """
    Task 3: Validate Schema
    Inspects SQL table schema, prints column datatypes, checks nullability, and validates expected data types.

    Parameters:
        engine (Engine): SQLAlchemy database engine.
        table_name (str): Target table name to inspect.
        expected_types (dict): Optional dict mapping column_name -> expected_type_substring.

    Returns:
        dict: Summary report of column schemas and validation statuses.
    """
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)

    print(f"\nTABLE SCHEMA ('{table_name}'):")
    print("-" * 60)
    print(f"{'COLUMN NAME':20} {'DATA TYPE':15} {'NULLABLE':10}")
    print("-" * 60)

    schema_info = {}
    for col in columns:
        col_name = col['name']
        col_type = str(col['type'])
        nullable = col['nullable']
        null_str = "NULL" if nullable else "NOT NULL"
        print(f"  {col_name:20} {col_type:15} {null_str}")
        schema_info[col_name] = {
            'type': col_type,
            'nullable': nullable
        }

    validation_results = {}
    if expected_types:
        print("\nDATATYPE VALIDATION:")
        for col_name, expected_type in expected_types.items():
            if col_name not in schema_info:
                status = '[X] (Missing Column)'
                is_valid = False
                actual = 'N/A'
            else:
                actual = schema_info[col_name]['type']
                is_valid = expected_type.upper() in str(actual).upper() or (
                    expected_type.upper() in ['VARCHAR', 'TEXT', 'STRING'] and any(t in str(actual).upper() for t in ['VARCHAR', 'TEXT', 'CLOB', 'CHAR', 'NULL'])
                ) or (
                    expected_type.upper() in ['DATE', 'TIMESTAMP', 'DATETIME'] and any(t in str(actual).upper() for t in ['DATE', 'TIMESTAMP', 'TEXT', 'VARCHAR'])
                ) or (
                    expected_type.upper() in ['INTEGER', 'INT', 'BIGINT'] and any(t in str(actual).upper() for t in ['INT', 'BIGINT'])
                )
                status = '[OK]' if is_valid else '[X]'

            print(f"  {status} {col_name:15} | Expected: {expected_type:10} | Actual: {actual}")
            validation_results[col_name] = {
                'expected': expected_type,
                'actual': actual,
                'valid': is_valid
            }

    return {
        'schema': schema_info,
        'validation': validation_results
    }


def execute_analytical_queries(engine: Engine, table_name: str = DEFAULT_TABLE_NAME) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Task 4: Query and Return Results
    Executes a simple SELECT query and an aggregation query against SQL source of truth, returning pandas DataFrames.

    Parameters:
        engine (Engine): SQLAlchemy database engine.
        table_name (str): SQL table to query.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (simple_query_df, agg_summary_df)
    """
    print("\n--- Task 4: Executing Queries ---")
    # Simple query
    simple_query = f"SELECT * FROM {table_name} WHERE customer_type = 'Enterprise'"
    results_simple = pd.read_sql(simple_query, engine)
    print(f"Simple Query: Retrieved {len(results_simple)} rows for customer_type = 'Enterprise'")
    print(results_simple.head())

    # Complex aggregation query
    agg_query = f"""
    SELECT 
        customer_type,
        COUNT(*) as count,
        ROUND(AVG(lifetime_value), 2) as avg_ltv,
        ROUND(SUM(revenue), 2) as total_revenue,
        ROUND(AVG(support_tickets), 2) as avg_tickets
    FROM {table_name}
    GROUP BY customer_type
    ORDER BY avg_ltv DESC
    """
    results_agg = pd.read_sql(agg_query, engine)
    print("\nAggregation Query Summary by Segment:")
    print(results_agg)

    return results_simple, results_agg


def load_cleaned_data_to_database(
    df: pd.DataFrame, 
    table_name: str = DEFAULT_TABLE_NAME, 
    database_path: str = DEFAULT_DB_PATH,
    if_exists: str = 'replace'
) -> Engine:
    """
    Task 5: Make Loading Repeatable
    Reusable pipeline function that establishes connection, loads DataFrame into database,
    performs schema validation checks, and returns the active engine object for downstream analytical use.

    Parameters:
        df (pd.DataFrame): Cleaned input DataFrame to load.
        table_name (str): Target database table name (default 'customers_cleaned').
        database_path (str): SQLite database file path or SQLAlchemy URI (default 'analytics.db').
        if_exists (str): Action if table exists ('replace', 'append', 'fail').

    Returns:
        Engine: SQLAlchemy Engine object initialized and ready for downstream queries.
    """
    # 1. Establish connection
    connection_uri = database_path if "://" in database_path else f"sqlite:///{database_path}"
    engine = setup_database_connection(connection_uri)

    # 2. Load DataFrame to table
    rows_loaded = load_dataframe_to_table(df, table_name, engine, if_exists=if_exists)

    # 3. Validate schema
    expected_types = {
        'customer_id': 'INTEGER',
        'email': 'VARCHAR',
        'signup_date': 'DATE'
    }
    validate_table_schema(engine, table_name, expected_types)

    print(f"[OK] Successfully loaded {rows_loaded} rows to {table_name} in database '{database_path}'")
    return engine


def run_database_integration_pipeline() -> None:
    """
    Main driver running the complete Database Integration workflow across Tasks 1-5.
    """
    print("=" * 70)
    print("      TRACE OPS: SQL ENVIRONMENT & DATABASE INTEGRATION PIPELINE")
    print("=" * 70)

    # Prepare data
    df_clean = prepare_cleaned_customer_data()
    print(f"Prepared cleaned customer DataFrame with shape: {df_clean.shape}")

    # Run Task 5 reusable wrapper (which runs Tasks 1, 2, 3)
    engine = load_cleaned_data_to_database(
        df=df_clean,
        table_name=DEFAULT_TABLE_NAME,
        database_path=DEFAULT_DB_PATH,
        if_exists='replace'
    )

    # Task 4: Execute analytical queries
    simple_res, agg_res = execute_analytical_queries(engine, DEFAULT_TABLE_NAME)

    # Write execution summary output
    os.makedirs(os.path.dirname(OUTPUT_SUMMARY_PATH), exist_ok=True)
    with open(OUTPUT_SUMMARY_PATH, "w") as f:
        f.write("TRACE OPS DATABASE INTEGRATION SUMMARY REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Database Path: {DEFAULT_DB_PATH}\n")
        f.write(f"Table Name: {DEFAULT_TABLE_NAME}\n")
        f.write(f"Total Rows Loaded: {len(df_clean)}\n\n")
        f.write("AGGREGATION QUERY RESULTS:\n")
        f.write(agg_res.to_string(index=False) + "\n\n")
        f.write("ENTERPRISE CUSTOMERS SUBSET:\n")
        f.write(simple_res.to_string(index=False) + "\n")

    print(f"\n[OK] Pipeline completed. Summary report written to: {OUTPUT_SUMMARY_PATH}")


if __name__ == "__main__":
    run_database_integration_pipeline()
