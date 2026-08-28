"""
Shared Metrics Runner - write SQL once, store it, everyone uses it.

Task 4: loads the versioned SQL files from queries/ and executes them
        through SQLAlchemy into pandas DataFrames.
Task 5: validates the returned metric tables (nulls, value ranges,
        logical consistency) so a broken query or bad load fails loudly
        instead of silently showing five teams five different numbers.

Prerequisite: python scripts/init_db.py   (builds analytics.db)

Run: python scripts/run_shared_queries.py
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUERIES_DIR = PROJECT_ROOT / "queries"
DB_PATH = PROJECT_ROOT / "analytics.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

# query file stem -> human label (the contract every team imports)
SHARED_METRICS = {
    "monthly_active_users": "Monthly Active Users",
    "revenue_by_segment": "Revenue by Segment",
    "conversion_funnel": "Conversion Funnel",
}


# ---------------------------------------------------------------- Task 4 ----
def load_query(query_name):
    """Load a shared SQL query from the queries/ folder.

    Parameters
    ----------
    query_name : str
        File stem, e.g. 'monthly_active_users'
        -> queries/monthly_active_users.sql

    Returns
    -------
    str : the SQL text of the shared query.
    """
    query_path = QUERIES_DIR / f"{query_name}.sql"
    if not query_path.exists():
        raise FileNotFoundError(f"Shared query not found: {query_path}")
    with open(query_path, "r", encoding="utf-8") as f:
        return f.read()


def get_engine(database_path=DB_PATH):
    """Create the SQLAlchemy engine for the analytics warehouse."""
    return create_engine(f"sqlite:///{database_path}")


def run_metric(query_name, engine):
    """Execute one shared .sql file and return the result as a DataFrame."""
    return pd.read_sql(load_query(query_name), engine)


# ---------------------------------------------------------------- Task 5 ----
def validate_metrics(mau_df, revenue_df, funnel_df):
    """Validate metric computation across the shared queries.

    Checks
    ------
    1. Nulls        - no metric table may contain null values.
    2. Value ranges - revenue strictly positive, conversion in [0, 100].
    3. Consistency  - every segment-month has orders and revenue; the
                      segment breakdown adds up to total MAU; no funnel
                      stage can exceed the number of signups.

    Returns
    -------
    bool : True when every check passes.
    """
    # 1. Null checks ---------------------------------------------------------
    assert mau_df.isnull().sum().sum() == 0, "MAU has nulls"
    assert revenue_df.isnull().sum().sum() == 0, "Revenue has nulls"
    assert funnel_df.isnull().sum().sum() == 0, "Funnel has nulls"

    # 2. Value ranges ----------------------------------------------------------
    assert (revenue_df["monthly_revenue"] > 0).all(), "Revenue <= 0"
    assert (funnel_df["conversion_pct"] >= 0).all() and (
        funnel_df["conversion_pct"] <= 100
    ).all(), "Conversion out of range"

    # 3. Logical consistency -----------------------------------------------------
    for idx, row in revenue_df.iterrows():
        assert row["order_count"] > 0, "Zero orders"
        assert row["monthly_revenue"] > 0, "Zero revenue"

    assert (mau_df["active_users"] > 0).all(), "Zero active users"
    assert (
        mau_df["enterprise_users"] + mau_df["smb_users"] == mau_df["active_users"]
    ).all(), "Segment breakdown does not sum to MAU"
    assert (
        (funnel_df["email_verified"] <= funnel_df["signups"]).all()
        and (funnel_df["first_purchase"] <= funnel_df["signups"]).all()
    ), "Funnel stage exceeds signups"

    print("✓ All metrics validated")
    return True


def main():
    """Load shared queries, execute them, validate, and export results."""
    engine = get_engine()

    # Load and execute - all teams use these same query files
    mau = run_metric("monthly_active_users", engine)
    revenue = run_metric("revenue_by_segment", engine)
    funnel = run_metric("conversion_funnel", engine)

    print("Monthly Active Users:")
    print(mau.to_string(index=False))
    print("\nRevenue by Segment:")
    print(revenue.to_string(index=False))
    print("\nConversion Funnel:")
    print(funnel.to_string(index=False))

    # Gate the numbers before anyone quotes them
    validate_metrics(mau, revenue, funnel)

    # Persist the agreed numbers for dashboards / hand-offs
    OUTPUT_DIR.mkdir(exist_ok=True)
    exports = {
        "monthly_active_users.csv": mau,
        "revenue_by_segment.csv": revenue,
        "conversion_funnel.csv": funnel,
    }
    for filename, df in exports.items():
        df.to_csv(OUTPUT_DIR / filename, index=False)
    print(f"\nShared results exported to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
