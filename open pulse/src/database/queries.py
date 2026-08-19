"""Named SQL queries loaded from sql/analytics/*.sql.

Each query returns a pandas DataFrame via pandas.read_sql.
"""

QUERIES = {
    "first_time_journey": "sql/analytics/first_time_journey.sql",
    "review_wait_vs_return": "sql/analytics/review_wait_vs_return.sql",
}

def load_query(name):
    """Load a query's SQL text by name."""
    ...

def run_query(name, engine, params=None):
    """Execute a named query and return a pandas DataFrame."""
    ...
