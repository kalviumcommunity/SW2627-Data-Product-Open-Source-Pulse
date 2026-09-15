"""Named SQL queries loaded from sql/analytics/*.sql.

Each query returns a pandas DataFrame via pandas.read_sql.
"""

QUERIES = {
    "first_time_journey": "sql/analytics/first_time_journey.sql",
    "review_wait_vs_return": "sql/analytics/review_wait_vs_return.sql",
}

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

def load_query(name):
    """Load a query's SQL text by name."""
    if name not in QUERIES:
        raise KeyError(f"Unknown query: {name}")
    return (PROJECT_ROOT / QUERIES[name]).read_text(encoding="utf-8")

def run_query(name, engine, params=None):
    """Execute a named query and return a pandas DataFrame."""
    return pd.read_sql_query(load_query(name), engine, params=params or {})
