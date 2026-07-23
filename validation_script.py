"""
SQL-Based Insight Validation Pipeline.

This script implements Task 1 to Task 5 of the SQL-Based Insight Validation assignment:
- Task 1: Compute Three Metrics in Both SQL and Python (Active Users, AOV, Customer Churn)
- Task 2: Identify and Document Discrepancies (Compare SQL vs Python, flag > tolerance threshold)
- Task 3: Build Automated Validation Script (Reusable validate_metrics function, generate report, export CSV)
- Task 4: Root Cause Investigation & Fix Validation (Refactor SQL date logic, verify 100% agreement)
- Task 5: Follow-Up Documentation Integration
"""

import os
import sys
import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DEFAULT_DB_PATH = "analytics.db"
VALIDATION_REPORT_PATH = "validation_report.csv"
OUTPUT_REPORT_PATH = os.path.join("output", "validation_report.csv")


def setup_database_connection(connection_uri: str = f"sqlite:///{DEFAULT_DB_PATH}") -> Engine:
    """
    Setup database connection using SQLAlchemy.
    """
    engine = create_engine(connection_uri, echo=False)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine


def seed_validation_database(engine: Engine) -> None:
    """
    Ensures required tables ('logins' and 'orders') exist in the SQLite database
    with deterministic test data for active users, AOV, and customer churn metrics.
    """
    today = date.today()
    
    with engine.connect() as conn:
        # 1. Seed Logins Table
        conn.execute(text("DROP TABLE IF EXISTS logins"))
        conn.execute(text("""
            CREATE TABLE logins (
                login_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                login_date DATE
            )
        """))
        
        logins_rows = []
        # 100 unique users: 75 logged in within last 30 days, 25 logged in > 30 days ago
        for uid in range(1, 76):
            logins_rows.append({"user_id": uid, "login_date": (today - timedelta(days=5)).strftime('%Y-%m-%d')})
            logins_rows.append({"user_id": uid, "login_date": (today - timedelta(days=20)).strftime('%Y-%m-%d')})
        for uid in range(76, 101):
            logins_rows.append({"user_id": uid, "login_date": (today - timedelta(days=40)).strftime('%Y-%m-%d')})
            logins_rows.append({"user_id": uid, "login_date": (today - timedelta(days=60)).strftime('%Y-%m-%d')})
            
        pd.DataFrame(logins_rows).to_sql('logins', engine, if_exists='append', index=False)

        # 2. Seed Orders Table
        # Month N (current month), Month N-1 (previous month)
        first_day_curr_month = today.replace(day=1)
        last_day_prev_month = first_day_curr_month - timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)
        
        conn.execute(text("DROP TABLE IF EXISTS orders"))
        conn.execute(text("""
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                order_date DATE,
                order_amount REAL
            )
        """))
        
        orders_rows = []
        oid = 10001
        # Month N-1 orders: 80 active customers with order_amount > 0
        for cid in range(1, 81):
            orders_rows.append({
                "order_id": oid,
                "customer_id": cid,
                "order_date": (first_day_prev_month + timedelta(days=10)).strftime('%Y-%m-%d'),
                "order_amount": 150.0
            })
            oid += 1
            
        # Month N orders: 60 active customers (20 customers from Month N-1 churned!)
        for cid in range(1, 61):
            orders_rows.append({
                "order_id": oid,
                "customer_id": cid,
                "order_date": (first_day_curr_month + timedelta(days=5)).strftime('%Y-%m-%d'),
                "order_amount": 200.0
            })
            oid += 1
            
        pd.DataFrame(orders_rows).to_sql('orders', engine, if_exists='append', index=False)
        conn.commit()


def compute_python_active_users(engine: Engine) -> int:
    """
    Metric 1 Python: Select users who logged in at least once in the last 30 days.
    """
    logins_df = pd.read_sql("SELECT * FROM logins", engine)
    logins_df['login_date'] = pd.to_datetime(logins_df['login_date']).dt.date
    cutoff_date = date.today() - timedelta(days=30)
    active_users_py = logins_df[logins_df['login_date'] >= cutoff_date]['user_id'].nunique()
    return int(active_users_py)


def compute_python_aov(engine: Engine) -> float:
    """
    Metric 2 Python: Mean order amount for all orders.
    """
    orders_df = pd.read_sql("SELECT * FROM orders", engine)
    aov_py = float(orders_df['order_amount'].mean())
    return aov_py


def compute_python_churn(engine: Engine) -> int:
    """
    Metric 3 Python: Customers active in month N-1 but not month N (with spending > 0 in month N-1).
    """
    orders_df = pd.read_sql("SELECT * FROM orders", engine)
    orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
    
    today = date.today()
    first_curr = pd.Timestamp(today.replace(day=1))
    last_prev = first_curr - pd.Timedelta(days=1)
    first_prev = pd.Timestamp(last_prev.replace(day=1))
    first_next = (first_curr + pd.Timedelta(days=32)).replace(day=1)
    
    prev_month_cust = set(orders_df[
        (orders_df['order_date'] >= first_prev) & 
        (orders_df['order_date'] <= last_prev) & 
        (orders_df['order_amount'] > 0)
    ]['customer_id'])
    
    curr_month_cust = set(orders_df[
        (orders_df['order_date'] >= first_curr) & 
        (orders_df['order_date'] < first_next)
    ]['customer_id'])
    
    churned_py = len(prev_month_cust - curr_month_cust)
    return churned_py


# SQL Queries
SQL_ACTIVE_USERS = """
SELECT COUNT(DISTINCT user_id) as active_users
FROM logins
WHERE login_date >= DATE('now', '-30 days');
"""

SQL_AOV = """
SELECT AVG(order_amount) as aov
FROM orders;
"""

SQL_CHURN_BUGGY = """
SELECT COUNT(DISTINCT c1.customer_id) as churned_customers
FROM (
    SELECT DISTINCT customer_id
    FROM orders
    WHERE strftime('%m', order_date) = strftime('%m', 'now') - 1
      AND order_amount > 0
) c1
LEFT JOIN (
    SELECT DISTINCT customer_id
    FROM orders
    WHERE strftime('%m', order_date) = strftime('%m', 'now')
) c2 ON c1.customer_id = c2.customer_id
WHERE c2.customer_id IS NULL;
"""

SQL_CHURN_FIXED = """
SELECT COUNT(DISTINCT c1.customer_id) as churned_customers
FROM (
    SELECT DISTINCT customer_id
    FROM orders
    WHERE order_date >= DATE('now', 'start of month', '-1 month')
      AND order_date < DATE('now', 'start of month')
      AND order_amount > 0
) c1
LEFT JOIN (
    SELECT DISTINCT customer_id
    FROM orders
    WHERE order_date >= DATE('now', 'start of month')
      AND order_date < DATE('now', 'start of month', '+1 month')
) c2 ON c1.customer_id = c2.customer_id
WHERE c2.customer_id IS NULL;
"""


def validate_metrics(engine: Engine, tolerance_pct: float = 0.1, use_fixed_sql: bool = True) -> pd.DataFrame:
    """
    Validate that SQL and Python compute identical metrics.
    
    Args:
        engine: SQLAlchemy database engine
        tolerance_pct: Acceptable percentage difference (default 0.1%)
        use_fixed_sql: Whether to use fixed SQL query for churn metric
    
    Returns:
        validation_report: DataFrame with all metrics and match status
    """
    churn_sql = SQL_CHURN_FIXED if use_fixed_sql else SQL_CHURN_BUGGY
    
    metrics = {
        'Active Users': {
            'sql': SQL_ACTIVE_USERS,
            'python': lambda: compute_python_active_users(engine),
            'tolerance': 0.0  # Exact match required for count
        },
        'AOV': {
            'sql': SQL_AOV,
            'python': lambda: compute_python_aov(engine),
            'tolerance': tolerance_pct  # Percentage tolerance
        },
        'Churn': {
            'sql': churn_sql,
            'python': lambda: compute_python_churn(engine),
            'tolerance': 0.0  # Exact match required for count
        }
    }
    
    report_rows = []
    run_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for metric_name, metric_def in metrics.items():
        sql_val = pd.read_sql(metric_def['sql'], engine).iloc[0, 0]
        sql_val = float(sql_val) if sql_val is not None else 0.0
        py_val = float(metric_def['python']())
        
        difference = abs(sql_val - py_val)
        pct_diff = (difference / abs(sql_val) * 100.0) if sql_val != 0 else (0.0 if py_val == 0 else 100.0)
        
        match_status = 'PASS' if pct_diff <= metric_def['tolerance'] else 'FAIL'
        
        report_rows.append({
            'Metric': metric_name,
            'SQL': round(sql_val, 4),
            'Python': round(py_val, 4),
            'Difference': round(difference, 4),
            'Pct_Difference': round(pct_diff, 4),
            'Tolerance': metric_def['tolerance'],
            'Status': match_status,
            'Timestamp': run_timestamp
        })
        
    return pd.DataFrame(report_rows)


def run_full_validation_workflow(engine: Engine) -> pd.DataFrame:
    """
    Executes Tasks 1 through 4:
    1. Seed test dataset.
    2. Run initial check (demonstrating buggy SQL vs Python discrepancy).
    3. Run fixed check (demonstrating resolved alignment).
    4. Save report to validation_report.csv.
    """
    seed_validation_database(engine)
    
    print("==================================================")
    print("Task 1 & Task 2: Initial Validation (Uncorrected SQL)")
    print("==================================================")
    initial_report = validate_metrics(engine, tolerance_pct=0.1, use_fixed_sql=False)
    print(initial_report.to_string(index=False))
    
    print("\nDiscrepancies found in initial validation:")
    for idx, row in initial_report.iterrows():
        if row['Status'] == 'FAIL':
            print(f"  ⚠️ {row['Metric']}: {row['Pct_Difference']}% difference (SQL={row['SQL']}, Python={row['Python']})")
        else:
            print(f"  ✓ {row['Metric']}: Match within tolerance")

    print("\n==================================================")
    print("Task 3 & Task 4: Post-Fix Validation (Corrected SQL)")
    print("==================================================")
    final_report = validate_metrics(engine, tolerance_pct=0.1, use_fixed_sql=True)
    print(final_report.to_string(index=False))
    
    print("\nDiscrepancy check post-fix:")
    for idx, row in final_report.iterrows():
        if row['Status'] == 'FAIL':
            print(f"  ⚠️ {row['Metric']}: {row['Pct_Difference']}% difference")
        else:
            print(f"  ✓ {row['Metric']}: Match within tolerance (PASS)")
            
    # Save final report to validation_report.csv
    final_report.to_csv(VALIDATION_REPORT_PATH, index=False)
    print(f"\n[SUCCESS] Saved validation report to '{VALIDATION_REPORT_PATH}'.")
    
    os.makedirs("output", exist_ok=True)
    final_report.to_csv(OUTPUT_REPORT_PATH, index=False)
    
    return final_report


if __name__ == "__main__":
    db_engine = setup_database_connection()
    run_full_validation_workflow(db_engine)
