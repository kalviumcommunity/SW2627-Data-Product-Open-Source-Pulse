"""Tests for the shared SQL metrics in queries/ and their runner.

Covers Tasks 1-5: the .sql files exist and run, return the contracted
columns, pass validation, and reproduce the source-of-truth totals.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import inspect

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from run_shared_queries import (  # noqa: E402
    DB_PATH,
    get_engine,
    load_query,
    run_metric,
    validate_metrics,
)

import init_db  # noqa: E402

SHARED_QUERIES = (
    "monthly_active_users",
    "revenue_by_segment",
    "conversion_funnel",
)

EXPECTED_COLUMNS = {
    "monthly_active_users": {
        "month", "active_users", "enterprise_users", "smb_users"},
    "revenue_by_segment": {
        "customer_type", "month", "order_count", "monthly_revenue",
        "avg_order_value", "unique_customers", "revenue_per_customer"},
    "conversion_funnel": {
        "signup_date", "signups", "email_verified", "first_purchase",
        "conversion_pct"},
}


@pytest.fixture(scope="module")
def engine():
    """Engine to the analytics warehouse, bootstrapping it if needed."""
    eng = get_engine()
    if "transactions" not in inspect(eng).get_table_names():
        init_db.build_analytics_db(str(DB_PATH))
    return eng


# ---------------------------------------------------------------- Task 1 ----
def test_load_query_reads_shared_files():
    sql = load_query("monthly_active_users")
    assert "COUNT(DISTINCT customer_id)" in sql
    assert "FILTER (WHERE" in sql  # requirement: conditional aggregation


# ---------------------------------------------------------------- Task 2 ----
def test_revenue_query_joins_and_metrics():
    sql = load_query("revenue_by_segment")
    assert "JOIN customers" in sql
    assert "monthly_revenue" in sql and "revenue_per_customer" in sql


# ---------------------------------------------------------------- Task 3 ----
def test_funnel_query_computes_conversion_pct():
    sql = load_query("conversion_funnel")
    assert "conversion_pct" in sql and "100.0 *" in sql


@pytest.mark.parametrize("name", SHARED_QUERIES)
def test_query_returns_contracted_columns(engine, name):
    df = run_metric(name, engine)
    assert not df.empty, f"{name} returned no rows"
    assert EXPECTED_COLUMNS[name] == set(df.columns), \
        f"{name} columns drifted from the shared contract"
    assert df.isnull().sum().sum() == 0, f"{name} returned nulls"


# ---------------------------------------------------------------- Task 5 ----
def test_validate_metrics_passes_on_shared_results(engine):
    mau = run_metric("monthly_active_users", engine)
    revenue = run_metric("revenue_by_segment", engine)
    funnel = run_metric("conversion_funnel", engine)
    assert validate_metrics(mau, revenue, funnel) is True


def test_validate_metrics_fails_on_corrupted_revenue():
    with pytest.raises(AssertionError):
        validate_metrics(
            pd.DataFrame({"active_users": [1], "enterprise_users": [1],
                          "smb_users": [0]}),
            pd.DataFrame({"order_count": [0], "monthly_revenue": [-10.0]}),
            pd.DataFrame({"signups": [1], "email_verified": [1],
                          "first_purchase": [0], "conversion_pct": [0.0]}),
        )


def test_revenue_matches_source_of_truth(engine):
    """'One number, one truth' proof: shared metric == raw fact sum."""
    revenue = run_metric("revenue_by_segment", engine)
    truth = pd.read_sql(
        """
        SELECT SUM(amount) AS total_revenue
        FROM transactions
        WHERE transaction_date >= DATE('now', 'start of month', '-12 months')
        """,
        engine,
    )
    assert revenue["monthly_revenue"].sum() == pytest.approx(
        truth["total_revenue"].iloc[0]
    )


def test_mau_segments_sum_to_total(engine):
    mau = run_metric("monthly_active_users", engine)
    assert (mau["enterprise_users"] + mau["smb_users"]
            == mau["active_users"]).all()


def test_funnel_stages_never_exceed_signups(engine):
    funnel = run_metric("conversion_funnel", engine)
    assert (funnel["email_verified"] <= funnel["signups"]).all()
    assert (funnel["first_purchase"] <= funnel["signups"]).all()
