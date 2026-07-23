"""
SQL Views & Aggregation Layer Pipeline.

This script implements Task 1 to Task 5 of the SQL Views & Aggregation Layer Design assignment:
- Task 1: Create Two SQL Views (vw_active_customers, vw_product_performance)
- Task 2: Create One Pre-Aggregated Summary Table (agg_daily_metrics) with updated_at timestamp
- Task 3: Query Views & Aggregated Tables from Python (simulating Streamlit dashboard usage)
- Task 4: Define & Apply Naming Conventions (vw_ for views, agg_ for pre-aggregated tables)
- Task 5: View Definitions Committed as .sql Files
"""

import os
import sys
import time
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DEFAULT_DB_PATH = "analytics.db"
OUTPUT_SUMMARY_PATH = os.path.join("output", "sql_views_aggregation_summary.txt")


def setup_database_connection(connection_uri: str = f"sqlite:///{DEFAULT_DB_PATH}") -> Engine:
    """
    Setup database connection using SQLAlchemy.
    """
    engine = create_engine(connection_uri, echo=False)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine


def prepare_database_schema(engine: Engine) -> None:
    """
    Ensure base tables have required columns for views (e.g. deleted_at on customers).
    """
    with engine.connect() as conn:
        # Check if deleted_at column exists in customers table
        result = conn.execute(text("PRAGMA table_info(customers)")).fetchall()
        col_names = [row[1] for row in result]
        if 'deleted_at' not in col_names:
            conn.execute(text("ALTER TABLE customers ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL"))
            conn.commit()


def execute_sql_file(filepath: str, engine: Engine) -> None:
    """
    Reads and executes a SQL file containing CREATE VIEW or CREATE TABLE statements.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"SQL file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split commands by semicolon if file contains multiple statements
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

    with engine.connect() as conn:
        for stmt in statements:
            # Skip pure comment blocks
            lines = [line for line in stmt.split("\n") if not line.strip().startswith("--")]
            clean_stmt = "\n".join(lines).strip()
            if clean_stmt:
                conn.execute(text(clean_stmt))
        conn.commit()


def create_views_and_aggregations(engine: Engine) -> None:
    """
    Task 1 & Task 2: Create SQL views and pre-aggregated summary table.
    """
    prepare_database_schema(engine)

    vw_active_path = os.path.join("database", "views", "vw_active_customers.sql")
    vw_product_path = os.path.join("database", "views", "vw_product_performance.sql")
    agg_metrics_path = os.path.join("database", "aggregations", "agg_daily_metrics.sql")

    # Drop existing table if refreshing agg_daily_metrics
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS agg_daily_metrics"))
        conn.commit()

    execute_sql_file(vw_active_path, engine)
    execute_sql_file(vw_product_path, engine)
    execute_sql_file(agg_metrics_path, engine)


def query_data_layer(engine: Engine):
    """
    Task 3: Query views and pre-aggregated tables from Python.
    """
    # 1. Query View 1: Active Customers
    active_customers_df = pd.read_sql("""
        SELECT 
            customer_id, 
            customer_name, 
            segment,
            order_count_30d,
            revenue_30d,
            last_order_date,
            days_since_order
        FROM vw_active_customers
        ORDER BY revenue_30d DESC
        LIMIT 20
    """, engine)

    # 2. Query View 2: Product Performance
    product_performance_df = pd.read_sql("""
        SELECT 
            product_id,
            product_name,
            category,
            total_orders,
            units_sold,
            total_revenue,
            avg_unit_price,
            last_sold_date
        FROM vw_product_performance
        ORDER BY total_revenue DESC
        LIMIT 20
    """, engine)

    # 3. Query Pre-Aggregated Table: Daily Metrics
    agg_daily_df = pd.read_sql("""
        SELECT 
            aggregation_date,
            metric_name,
            metric_value,
            row_count,
            updated_at
        FROM agg_daily_metrics
        ORDER BY aggregation_date DESC
        LIMIT 30
    """, engine)

    # 4. Demonstrate Segment Aggregation via View
    active_by_segment_df = pd.read_sql("""
        SELECT 
            segment,
            COUNT(*) as customer_count,
            SUM(revenue_30d) as total_segment_revenue,
            AVG(revenue_30d) as avg_customer_revenue
        FROM vw_active_customers
        GROUP BY segment
        ORDER BY total_segment_revenue DESC
    """, engine)

    return active_customers_df, product_performance_df, agg_daily_df, active_by_segment_df


def benchmark_query_performance(engine: Engine) -> float:
    """
    Measures and returns query execution time on pre-aggregated table.
    """
    start_time = time.time()
    result_df = pd.read_sql("""
        SELECT metric_name, SUM(metric_value) as total_value, SUM(row_count) as total_rows
        FROM agg_daily_metrics
        GROUP BY metric_name
    """, engine)
    elapsed_ms = (time.time() - start_time) * 1000.0
    return elapsed_ms, result_df


def run_pipeline():
    """
    Executes complete data layer creation, querying, benchmarking, and output generation.
    """
    os.makedirs("output", exist_ok=True)
    engine = setup_database_connection()

    print("[1/4] Creating Views and Pre-Aggregated Tables...")
    create_views_and_aggregations(engine)
    print("      Created: vw_active_customers, vw_product_performance, agg_daily_metrics")

    print("[2/4] Querying Data Layer Objects...")
    active_customers, product_performance, agg_daily, active_by_segment = query_data_layer(engine)

    print(f"      vw_active_customers returned {len(active_customers)} rows")
    print(f"      vw_product_performance returned {len(product_performance)} rows")
    print(f"      agg_daily_metrics returned {len(agg_daily)} rows")

    print("[3/4] Benchmarking Pre-Aggregated Table Query Latency...")
    elapsed_ms, bench_df = benchmark_query_performance(engine)
    print(f"      Query Execution Time: {elapsed_ms:.2f} ms")

    print("[4/4] Writing Summary Report to File...")
    summary_lines = [
        "============================================================",
        "          SQL VIEWS & AGGREGATION LAYER SUMMARY REPORT      ",
        "============================================================",
        f"Generated At: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "--- VIEW 1: vw_active_customers (Top 5 Active Customers) ---",
        active_customers.head(5).to_string(index=False),
        "",
        "--- VIEW 2: vw_product_performance (Top 5 Products) ---",
        product_performance.head(5).to_string(index=False),
        "",
        "--- PRE-AGGREGATED TABLE: agg_daily_metrics (Recent 5 Days) ---",
        agg_daily.head(5).to_string(index=False),
        "",
        "--- CUSTOMER SEGMENT AGGREGATION VIA VIEW ---",
        active_by_segment.to_string(index=False),
        "",
        "--- BENCHMARK RESULTS ---",
        f"Pre-aggregated query latency: {elapsed_ms:.2f} ms",
        bench_df.to_string(index=False),
        "============================================================",
    ]

    summary_text = "\n".join(summary_lines)
    with open(OUTPUT_SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(summary_text)

    print(f"[OK] Summary successfully written to {OUTPUT_SUMMARY_PATH}")
    return active_customers, product_performance, agg_daily, active_by_segment, elapsed_ms


if __name__ == "__main__":
    run_pipeline()
