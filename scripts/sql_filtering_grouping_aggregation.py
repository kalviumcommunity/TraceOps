"""
SQL Filtering, Grouping & Aggregation Pipeline.

This script implements Task 1 to Task 5 of the SQL Filtering, Grouping & Aggregation assignment:
- Task 1: WHERE Filtering (Filter data quality issues before grouping)
- Task 2: GROUP BY and Aggregation (Multi-dimensional slicing across customer_type and month)
- Task 3: HAVING Filtering (Filter aggregate group metrics after grouping)
- Task 4: WHERE + HAVING Combined (Real-world data quality AND aggregate metric threshold filtering)
- Task 5: ORDER BY Ranking (Surface top performers using RANK() window function)

Additional Team Documentation Included:
1. WHERE vs HAVING distinction
2. GROUP BY semantics and aggregation unit
3. HAVING filter examples for business rules
4. Query optimization: Why WHERE before GROUP BY increases execution speed
5. Percentage share computation (% of total revenue within groups)
"""

import os
import sys
import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DEFAULT_DB_PATH = "analytics.db"
OUTPUT_SUMMARY_PATH = os.path.join("output", "sql_filtering_grouping_aggregation_summary.txt")


def setup_database_connection(connection_uri: str = f"sqlite:///{DEFAULT_DB_PATH}") -> Engine:
    """
    Setup database connection using SQLAlchemy engine.
    """
    engine = create_engine(connection_uri, echo=False)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine


def seed_database_tables(engine: Engine) -> None:
    """
    Populate database tables (customers, transactions) with realistic test data
    supporting customer_type, industry, transaction_status, transaction_date, amount.
    """
    # 1. Customers Table
    customers_df = pd.DataFrame({
        'customer_id': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        'customer_type': ['Enterprise', 'Enterprise', 'SMB', 'SMB', 'Startup', 'Enterprise', 'SMB', 'Startup', 'Enterprise', 'SMB'],
        'industry': ['Finance', 'Healthcare', 'Tech', 'Retail', 'Tech', 'Finance', 'Healthcare', 'Retail', 'Tech', 'Finance'],
        'email': [f"customer_{i}@example.com" for i in range(101, 111)],
        'signup_date': ['2024-01-10', '2024-01-15', '2024-02-01', '2024-02-10', '2024-03-01', '2024-03-15', '2024-04-01', '2024-04-10', '2024-05-01', '2024-05-15']
    })
    customers_df.to_sql('customers', engine, if_exists='replace', index=False)

    # 2. Transactions Table
    # Create multiple transactions per customer to support HAVING COUNT(*) >= 5 and SUM > 10000 tests
    today = datetime.date(2024, 12, 31)
    
    transactions_data = []
    order_id = 5001

    # Customer 101 (Enterprise, Finance) - 6 transactions, > $10,000 total
    for i in range(6):
        transactions_data.append({
            'order_id': order_id,
            'customer_id': 101,
            'customer_type': 'Enterprise',
            'transaction_date': f"2024-{min(i+1, 9):02d}-15",
            'amount': 2500.0,
            'transaction_status': 'completed'
        })
        order_id += 1

    # Customer 102 (Enterprise, Healthcare) - 5 transactions, > $10,000 total
    for i in range(5):
        transactions_data.append({
            'order_id': order_id,
            'customer_id': 102,
            'customer_type': 'Enterprise',
            'transaction_date': f"2024-{min(i+2, 9):02d}-10",
            'amount': 2200.0,
            'transaction_status': 'completed'
        })
        order_id += 1

    # Customer 103 (SMB, Tech) - 3 transactions, completed
    for i in range(3):
        transactions_data.append({
            'order_id': order_id,
            'customer_id': 103,
            'customer_type': 'SMB',
            'transaction_date': f"2024-{min(i+1, 9):02d}-05",
            'amount': 450.0,
            'transaction_status': 'completed'
        })
        order_id += 1

    # Customer 104 (SMB, Retail) - 2 transactions (1 pending, 1 refund)
    transactions_data.append({
        'order_id': order_id,
        'customer_id': 104,
        'customer_type': 'SMB',
        'transaction_date': '2024-03-01',
        'amount': -100.0,  # refund
        'transaction_status': 'completed'
    })
    order_id += 1
    transactions_data.append({
        'order_id': order_id,
        'customer_id': 104,
        'customer_type': 'SMB',
        'transaction_date': '2024-03-05',
        'amount': 300.0,
        'transaction_status': 'pending'  # pending, should be filtered out by WHERE
    })
    order_id += 1

    # Customer 106 (Enterprise, Finance) - 6 transactions, > $10,000
    for i in range(6):
        transactions_data.append({
            'order_id': order_id,
            'customer_id': 106,
            'customer_type': 'Enterprise',
            'transaction_date': f"2024-{min(i+3, 9):02d}-20",
            'amount': 3000.0,
            'transaction_status': 'completed'
        })
        order_id += 1

    # Customer 109 (Enterprise, Tech) - 4 transactions completed
    for i in range(4):
        transactions_data.append({
            'order_id': order_id,
            'customer_id': 109,
            'customer_type': 'Enterprise',
            'transaction_date': f"2024-{min(i+1, 9):02d}-12",
            'amount': 1500.0,
            'transaction_status': 'completed'
        })
        order_id += 1

    transactions_df = pd.DataFrame(transactions_data)
    transactions_df.to_sql('transactions', engine, if_exists='replace', index=False)


def load_query(query_name: str) -> str:
    """
    Load SQL query string from file queries/{query_name}.sql.
    """
    filepath = os.path.join("queries", f"{query_name}.sql")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Query file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def execute_filtering_pipeline(engine: Engine):
    """
    Executes Tasks 1 through 5 loading SQL queries from queries/*.sql.
    Returns dictionary of DataFrames for each task.
    """
    t1_sql = load_query("where_filtering")
    t2_sql = load_query("group_by_aggregation")
    t3_sql = load_query("having_filtering")
    t4_sql = load_query("where_having_combined")
    t5_sql = load_query("order_by_ranking")

    with engine.connect() as conn:
        task1_df = pd.read_sql(text(t1_sql), conn)
        task2_df = pd.read_sql(text(t2_sql), conn)
        task3_df = pd.read_sql(text(t3_sql), conn)
        task4_df = pd.read_sql(text(t4_sql), conn)
        task5_df = pd.read_sql(text(t5_sql), conn)

    return {
        "task1_where": task1_df,
        "task2_group_by": task2_df,
        "task3_having": task3_df,
        "task4_combined": task4_df,
        "task5_ranking": task5_df,
    }


def compute_percentage_share(engine: Engine) -> pd.DataFrame:
    """
    Computes percentage share of total revenue within groups using window functions.
    """
    query = """
    SELECT 
        c.customer_type,
        SUM(t.amount) AS segment_revenue,
        ROUND(SUM(t.amount) * 100.0 / SUM(SUM(t.amount)) OVER (), 2) AS pct_share_of_total
    FROM transactions t
    JOIN customers c ON t.customer_id = c.customer_id
    WHERE t.transaction_date >= '2024-01-01'
      AND t.transaction_status = 'completed'
      AND t.amount > 0
    GROUP BY c.customer_type
    ORDER BY segment_revenue DESC;
    """
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


def validate_results(results: dict) -> bool:
    """
    Validates execution results across all 5 tasks.
    Ensures non-empty DataFrames, valid schema, no missing values, and positive metrics.
    """
    for task_name, df in results.items():
        assert isinstance(df, pd.DataFrame), f"{task_name} output is not a DataFrame"
        assert not df.empty, f"{task_name} returned empty results"
        assert df.isnull().sum().sum() == 0, f"{task_name} contains unexpected null values"

    # Task 1 check
    assert "annual_revenue" in results["task1_where"].columns
    assert (results["task1_where"]["annual_revenue"] > 0).all()

    # Task 3 check (HAVING filter check)
    assert (results["task3_having"]["annual_revenue"] > 10000).all()
    assert (results["task3_having"]["transaction_count"] >= 5).all()

    # Task 5 check (Ranking check)
    assert "revenue_rank" in results["task5_ranking"].columns

    return True


def write_summary_report(results: dict, pct_df: pd.DataFrame, output_path: str = OUTPUT_SUMMARY_PATH) -> None:
    """
    Writes complete pipeline summary report including documentation on WHERE vs HAVING,
    GROUP BY semantics, performance optimization, and query result snapshots.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("========================================================================\n")
        f.write("SQL FILTERING, GROUPING & AGGREGATION PIPELINE SUMMARY REPORT\n")
        f.write("========================================================================\n\n")

        f.write("--- TEAM DOCUMENTATION & ARCHITECTURAL PATTERNS ---\n\n")
        
        f.write("1. WHERE vs HAVING Distinction:\n")
        f.write("   - WHERE: Filters raw records BEFORE grouping occurs. Used for data quality checks\n")
        f.write("     (e.g. status = 'completed', date ranges, excluding negative/zero amounts).\n")
        f.write("   - HAVING: Filters aggregate group metrics AFTER GROUP BY calculations finish.\n")
        f.write("     Used for metric thresholds (e.g. SUM(amount) > 10000, COUNT(*) >= 5).\n\n")

        f.write("2. GROUP BY Semantics:\n")
        f.write("   - GROUP BY alters the aggregation grain of the query from a single table total\n")
        f.write("     to discrete combinations of dimension values (e.g. customer_type + month).\n\n")

        f.write("3. Optimization Consideration:\n")
        f.write("   - Applying WHERE filters prior to GROUP BY is significantly faster because it\n")
        f.write("     prunes irrelevant rows early, reducing memory footprint and computational\n")
        f.write("     overhead during hash/sort grouping operations.\n\n")

        f.write("4. Percentage Share Computation:\n")
        f.write("   - Evaluates segment revenue relative to global total using window function OVER ():\n\n")
        f.write(pct_df.to_string(index=False) + "\n\n")

        f.write("------------------------------------------------------------------------\n")
        f.write("TASK QUERY EXECUTION RESULTS SNAPSHOTS\n")
        f.write("------------------------------------------------------------------------\n\n")

        for task_key, df in results.items():
            f.write(f"=== {task_key.upper()} ===\n")
            f.write(df.to_string(index=False) + "\n\n")

        f.write("========================================================================\n")
        f.write("VALIDATION STATUS: ALL CHECKS PASSED SUCCESSFULLY\n")
        f.write("========================================================================\n")

    print(f"[SUCCESS] Summary report generated at {output_path}")


def main():
    engine = setup_database_connection()
    seed_database_tables(engine)
    results = execute_filtering_pipeline(engine)
    pct_df = compute_percentage_share(engine)
    validate_results(results)
    write_summary_report(results, pct_df)
    print("[SUCCESS] SQL Filtering, Grouping & Aggregation pipeline completed successfully.")


if __name__ == "__main__":
    main()
