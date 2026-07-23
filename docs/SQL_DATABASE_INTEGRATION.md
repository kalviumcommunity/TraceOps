# SQL Environment & Database Integration Guide

## Overview & Real Scenario
Transitioning data workflows from ephemeral local notebooks and disconnected CSVs to queryable SQL databases establishes a **single source of truth**. This ensures data analysis is auditable, repeatable across environments, and version-controlled.

---

## 1. Database Fundamentals: SQLite vs PostgreSQL

| Feature | SQLite | PostgreSQL |
| :--- | :--- | :--- |
| **Architecture** | Serverless, file-based, zero setup | Client-server architecture |
| **Concurrency** | Single-writer lock; limited multi-user | High concurrency, multi-user ACID compliance |
| **Scale** | Best for local tools, testing, datasets < 1GB | Production applications, enterprise data warehouses |
| **Deployment** | Self-contained single file (`analytics.db`) | Managed database instance (AWS RDS, GCP Cloud SQL, local server) |
| **Use Case** | Prototyping, lightweight pipelines, local testing | Scalable production analytics & transactional systems |

---

## 2. SQLAlchemy Abstraction Layer
SQLAlchemy serves as Python's premier Database Abstraction Layer (DAL) and Object-Relational Mapper (ORM). 

### Key Benefits:
- **Database Independence**: Standardizes python-to-SQL operations regardless of backend dialect (SQLite, PostgreSQL, MySQL, Snowflake).
- **Engine Management**: Manages connection pooling, transactions, and raw execution contexts.
- **Pandas Integration**: Works seamlessly with `pandas.read_sql()` and `DataFrame.to_sql()`.

### Connection Strings:
- **SQLite**: `sqlite:///analytics.db`
- **PostgreSQL**: `postgresql://<user>:<password>@<host>:<port>/<dbname>`

---

## 3. Pandas Database Operations (`to_sql` & `read_sql`)

### Writing Data (`to_sql`)
```python
df.to_sql(
    name='customers_cleaned',
    con=engine,
    if_exists='replace', # Options: 'fail', 'replace', 'append'
    index=False
)
```
- **`if_exists='replace'`**: Drops the table if it exists before writing new rows (used for initial loads / full refreshes).
- **`if_exists='append'`**: Appends new records to an existing table structure.
- **`index=False`**: Prevents writing the Pandas DataFrame index as an extra SQL column.

### Querying Data (`read_sql`)
```python
query = "SELECT * FROM customers_cleaned WHERE customer_type = 'Enterprise'"
df_enterprise = pd.read_sql(query, con=engine)
```
- Executes native SQL queries directly against the source of truth and returns clean Pandas DataFrames ready for analytical manipulation.

---

## 4. Schema Inspection & Validation
Schema validation prevents silent type coercion and structural bugs:
- **`sqlalchemy.inspect(engine)`**: Inspects table metadata, column names, column datatypes, and nullability flags.
- **Expected Data Types**: Validates that target SQL columns match expected business domain types (`INTEGER` for identifiers, `VARCHAR`/`TEXT` for string fields, `FLOAT` for financial metrics, `DATE` for timestamps).
- **Null Constraints**: Ensures primary keys and mandatory attributes hold `NOT NULL` constraints.

---

## 5. Schema Evolution & Migration Strategies
When data requirements evolve over time:
1. **Schema Migration Tools**: Use database migration frameworks (e.g. Alembic for SQLAlchemy) to version-control schema migrations (`ALTER TABLE`, column additions, index updates).
2. **Backwards-Compatible Defaults**: Add new columns with default values or nullable flags to avoid breaking existing queries.
3. **Audit Trails**: Retain raw data ingest histories to allow re-running cleaning scripts against historical snapshots.

---

## Pipeline Execution

Run the complete 5-task pipeline:
```bash
python scripts/database_integration.py
```

Run unit tests:
```bash
python -m pytest tests/test_database_integration.py
```
