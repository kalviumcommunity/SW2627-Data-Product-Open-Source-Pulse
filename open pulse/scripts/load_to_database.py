"""
Database Loading & Validation Tasks

Loads the cleaned DataFrame into a SQLite analytics database,
validates schema, runs queries, and provides a repeatable loader.

Connection string documentation:
    SQLite (default):  sqlite:///analytics.db   -> file-based, zero setup, no credentials needed
    PostgreSQL (prod): postgresql://username:password@host:5432/analytics
    Credentials should come from environment variables, never hardcoded:
        import os
        engine = create_engine(
            f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:5432/{os.environ['DB_NAME']}"
        )

Run: python scripts/load_to_database.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine, inspect


# ---------------------------------------------------------------- Task 1 ----
def setup_connection(database_path="analytics.db"):
    """Create SQLAlchemy engine for SQLite and test the connection.

    Parameters
    ----------
    database_path : str
        Path to the SQLite database file (default 'analytics.db').

    Returns
    -------
    sqlalchemy.Engine : live engine connected to the database.
    """
    # SQLite is file-based with zero setup; swap the URL for PostgreSQL in prod:
    #   create_engine(f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@localhost:5432/analytics")
    engine = create_engine(f"sqlite:///{database_path}")

    with engine.connect() as conn:
        print("[Task 1] Database connection successful")

    return engine


# ---------------------------------------------------------------- Task 2 ----
def load_dataframe_as_table(df_clean, table_name, engine):
    """Load cleaned DataFrame as a database table and verify it.

    Parameters
    ----------
    df_clean : pd.DataFrame
        Cleaned data to persist.
    table_name : str
        Target table name.
    engine : sqlalchemy.Engine
        Active database engine.

    Returns
    -------
    int : number of rows loaded.
    """
    df_clean.to_sql(table_name, engine, if_exists="replace", index=False)

    inspector = inspect(engine)
    assert table_name in inspector.get_table_names(), f"{table_name} was not created"

    count = pd.read_sql(f"SELECT COUNT(*) AS row_count FROM {table_name}", engine)
    rows_loaded = int(count.iloc[0]["row_count"])
    print(f"[Task 2] Table '{table_name}' created | Rows loaded: {rows_loaded}")
    assert rows_loaded == len(df_clean), "Row count mismatch after load"
    return rows_loaded


# ---------------------------------------------------------------- Task 3 ----
def validate_schema(engine, table_name, expected_types):
    """Inspect table schema and validate column types.

    Parameters
    ----------
    engine : sqlalchemy.Engine
        Active database engine.
    table_name : str
        Table to inspect.
    expected_types : dict
        Mapping of column name -> expected type substring (e.g. {'id': 'INTEGER'}).

    Returns
    -------
    list[dict] : column metadata from the inspector.
    """
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)

    print(f"\n[Task 3] TABLE SCHEMA ({table_name}):")
    for col in columns:
        print(f"  {col['name']:12} {str(col['type']):15} {'NOT NULL' if not col['nullable'] else ''}")

    print("\nDATATYPE VALIDATION:")
    all_ok = True
    for col_name, expected_type in expected_types.items():
        matches = [c["type"] for c in columns if c["name"] == col_name]
        if not matches:
            print(f"x {col_name}: column missing")
            all_ok = False
            continue
        status = "OK" if expected_type.upper() in str(matches[0]).upper() else "MISMATCH"
        if status != "OK":
            all_ok = False
        print(f"{status}: {col_name}: {matches[0]} (expected {expected_type})")

    assert all_ok, "Schema validation failed"
    return columns


# ---------------------------------------------------------------- Task 4 ----
def query_results(engine):
    """Run simple and aggregation SELECT queries, returning DataFrames."""
    simple_query = "SELECT * FROM customers_cleaned WHERE active = 1"
    results = pd.read_sql(simple_query, engine)
    print(f"\n[Task 4] Retrieved {len(results)} active rows")
    print(results.head())

    agg_query = """
        SELECT
            active,
            COUNT(*)   AS count,
            AVG(score) AS avg_score,
            AVG(age)   AS avg_age
        FROM customers_cleaned
        GROUP BY active
        ORDER BY avg_score DESC
    """
    summary = pd.read_sql(agg_query, engine)
    print("\nSummary by segment:")
    print(summary)
    return results, summary


# ---------------------------------------------------------------- Task 5 ----
def load_cleaned_data_to_database(df, table_name, database_path="analytics.db"):
    """Load cleaned DataFrame to database - repeatable function.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned DataFrame to load.
    table_name : str
        Name of the target table (replaced if it already exists).
    database_path : str
        Path to the SQLite database file (default 'analytics.db').

    Returns
    -------
    sqlalchemy.Engine : engine for further querying by callers.
    """
    engine = create_engine(f"sqlite:///{database_path}")

    # Load
    df.to_sql(table_name, engine, if_exists="replace", index=False)

    # Validate
    count = pd.read_sql(f"SELECT COUNT(*) AS ct FROM {table_name}", engine)
    rows_loaded = int(count.iloc[0]["ct"])
    assert rows_loaded == len(df), f"Expected {len(df)} rows, found {rows_loaded}"

    print(f"\n[Task 5] Loaded {rows_loaded} rows to {table_name}")
    return engine


if __name__ == "__main__":
    cleaned_path = os.path.join("output", "processed.csv")
    df_clean = pd.read_csv(cleaned_path)

    # Task 1: connection
    engine = setup_connection()

    # Task 2: load + verify
    load_dataframe_as_table(df_clean, "customers_cleaned", engine)

    # Task 3: schema validation (types adapted to this project's columns)
    validate_schema(
        engine,
        "customers_cleaned",
        {
            "id": "BIGINT",
            "name": "TEXT",
            "age": "FLOAT",
            "score": "FLOAT",
            "active": "BOOLEAN",
        },
    )

    # Task 4: queries
    query_results(engine)

    # Task 5: repeatable loader
    engine = load_cleaned_data_to_database(df_clean, "customers_cleaned")
    sample = pd.read_sql("SELECT * FROM customers_cleaned LIMIT 10", engine)
    print(sample)
