"""Read the artifacts produced by the analysis scripts.

This is the only module in the dashboard that touches disk. Pages and chart
builders call these functions instead of reading CSV or JSON directly, so a
change to an upstream output format is corrected in exactly one place.

Nothing here modifies an analysis script. Where a script exposes a reusable
pure function, that function is imported and called; otherwise the committed
artifact in ``output/`` is read.
"""

import importlib.util
import json
import sys

import pandas as pd

from src.dashboard import config


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------
def _cache(func):
    """Cache results under Streamlit, and act as a no-op anywhere else.

    ``scripts/build_charts.py`` imports these same loaders from a plain shell,
    where Streamlit's cache has no runtime to attach to and logs a warning per
    call. Applying the decorator only inside a live Streamlit session keeps the
    command line output clean.
    """
    try:
        import streamlit as st
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx(suppress_warning=True) is not None:
            return st.cache_data(show_spinner=False)(func)
    except Exception:
        pass
    return func


class MissingArtifactError(FileNotFoundError):
    """Raised when an analysis script has not been run yet."""


def _require(path, produced_by):
    """Return the path, or explain which script needs to run first."""
    if not path.exists():
        raise MissingArtifactError(
            f"{path.name} is missing from output/. "
            f"Run `python scripts/{produced_by}` to generate it."
        )
    return path


_SCRIPT_MODULES = {}


def _load_script_module(name):
    """Import a module from scripts/ by path, without altering sys.path.

    The scripts directory is not a package, so it cannot be imported normally.
    Loading by file location keeps the analysis scripts exactly as written.
    """
    if name in _SCRIPT_MODULES:
        return _SCRIPT_MODULES[name]

    spec = importlib.util.spec_from_file_location(
        f"_opencharts_{name}", config.SCRIPTS_DIR / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _SCRIPT_MODULES[name] = module
    return module


# ---------------------------------------------------------------------------
# Segment and product revenue
# ---------------------------------------------------------------------------
@_cache
def load_segment_product_pivot():
    """Return the customer segment by product revenue pivot."""
    path = _require(config.SEGMENT_REVENUE_PIVOT, "analyze_segments.py")
    pivot = pd.read_csv(path, index_col="customer_type")
    return pivot.reindex(columns=config.PRODUCT_ORDER)


@_cache
def load_revenue_by_product():
    """Return total revenue per product line, largest first."""
    pivot = load_segment_product_pivot()
    return pivot.sum(axis=0).sort_values(ascending=False)


@_cache
def load_segment_metrics():
    """Return per-segment churn, revenue, and support metrics."""
    path = _require(config.SEGMENT_METRICS, "analyze_segments.py")
    return pd.read_csv(path, index_col="customer_type")


@_cache
def load_segment_insights():
    """Return the threshold-based segment actions table."""
    path = _require(config.SEGMENT_INSIGHTS, "analyze_segments.py")
    return pd.read_csv(path)


@_cache
def load_segment_summary():
    """Return the segment analysis summary as a dictionary."""
    path = _require(config.SEGMENT_SUMMARY, "analyze_segments.py")
    return json.loads(path.read_text(encoding="utf-8"))


@_cache
def load_product_metrics():
    """Return revenue, customer count, and average revenue per product line.

    Rolls the per-segment breakdown up to the product level and derives the
    average revenue per customer, which the interactive hover tooltips show
    alongside the plotted revenue.
    """
    path = _require(config.PRODUCT_SEGMENT_METRICS, "analyze_segments.py")
    detail = pd.read_csv(path)
    metrics = detail.groupby("product").agg(
        revenue=("total_revenue", "sum"),
        customers=("customer_count", "sum"),
    )
    metrics["avg_revenue_per_customer"] = metrics["revenue"] / metrics["customers"]
    metrics["revenue_share_pct"] = metrics["revenue"] / metrics["revenue"].sum() * 100
    return metrics.reindex(config.PRODUCT_ORDER)


# ---------------------------------------------------------------------------
# Revenue trend
# ---------------------------------------------------------------------------
@_cache
def load_revenue_trend():
    """Return the daily revenue series with its rolling averages."""
    path = _require(config.REVENUE_TREND_FEATURES, "analyze_revenue_trends.py")
    trend = pd.read_csv(path, parse_dates=["date"], index_col="date")
    return trend.sort_index()


@_cache
def load_revenue_trend_summary():
    """Return the trend direction, magnitude, and narrative."""
    path = _require(config.REVENUE_TREND_SUMMARY, "analyze_revenue_trends.py")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Customer-level data
# ---------------------------------------------------------------------------
@_cache
def load_customer_segment_data():
    """Return the 1,000-row customer dataset with value and support columns."""
    path = _require(config.CUSTOMER_SEGMENT_DATA, "../src/analytics/segment_analysis.py")
    return pd.read_csv(path)


@_cache
def load_value_distribution_stats():
    """Return lifetime-value distribution statistics.

    Delegates to ``analyze_revenue_distribution.analyze_revenue``, the function
    the distribution module already uses, so the skewness and percentile
    figures shown on the dashboard are produced by the same code path as the
    committed distribution report.
    """
    module = _load_script_module("analyze_revenue_distribution")
    customers = load_customer_segment_data()
    statistics, _high, _low = module.analyze_revenue(
        customers, revenue_column="lifetime_value"
    )
    return statistics


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
@_cache
def load_daily_metrics():
    """Return the daily business metrics used by the KPI layer."""
    path = _require(config.DAILY_METRICS, "anomaly_detection.py")
    return pd.read_csv(path, parse_dates=["date"])


def _kpis_from_views():
    """Read the KPIs out of the SQL views, or return None if unavailable.

    Preferred path: the views are the single definition of each metric. The
    database is gitignored and rebuilt by ``scripts/build_kpis.py``, so a fresh
    clone will not have it and must fall back.
    """
    if not config.DB_PATH.exists():
        return None
    try:
        from sqlalchemy import create_engine

        engine = create_engine(f"sqlite:///{config.DB_PATH}")
        with engine.connect() as connection:
            summary = pd.read_sql("SELECT * FROM vw_kpi_summary", connection)
            churn = pd.read_sql("SELECT * FROM vw_churn_kpi", connection).iloc[0]
        engine.dispose()
    except Exception:
        return None

    lookup = summary.set_index("metric")
    values = {
        metric: {
            "current": float(lookup.loc[metric, "current_value"]),
            "prior": float(lookup.loc[metric, "prior_value"]),
            "change_pct": float(lookup.loc[metric, "change_pct"]),
        }
        for metric in lookup.index
    }
    values["churn_rate"] = {
        "current": float(churn["current_value"]),
        "target": float(churn["target_value"]),
        "change_pct": float(churn["change_pct"]),
    }
    return values


def _kpis_from_pandas(daily, customers):
    """Compute the KPIs directly from the committed artifacts."""
    from src.dashboard import kpi as kpi_module

    current, prior, _context = kpi_module.matched_month_windows(daily)

    def totals(frame):
        revenue = float(frame["daily_revenue"].sum())
        transactions = float(frame["transaction_count"].sum())
        return {
            "revenue": revenue,
            "transactions": transactions,
            "signups": float(frame["signup_rate"].sum()),
            "avg_order_value": revenue / transactions if transactions else float("nan"),
        }

    current_totals, prior_totals = totals(current), totals(prior)
    values = {
        metric: {
            "current": current_totals[metric],
            "prior": prior_totals[metric],
            "change_pct": kpi_module.percent_change(
                current_totals[metric], prior_totals[metric]
            ),
        }
        for metric in current_totals
    }
    churn_now = float(customers["churn"].mean())
    values["churn_rate"] = {
        "current": churn_now,
        "target": kpi_module.CHURN_TARGET,
        "change_pct": kpi_module.percent_change(churn_now, kpi_module.CHURN_TARGET),
    }
    return values


@_cache
def load_kpi_values():
    """Return the KPI values, the reporting window, and which path produced them.

    Reads the SQL views when the analytics database is present, and falls back
    to computing the same definitions in pandas when it is not. Both paths are
    cross-validated by ``scripts/build_kpis.py``.
    """
    from src.dashboard import kpi as kpi_module

    daily = load_daily_metrics()
    customers = load_customer_segment_data()
    _current, _prior, context = kpi_module.matched_month_windows(daily)

    values = _kpis_from_views()
    if values is not None:
        source = f"SQL views in {config.DB_PATH.name}"
    else:
        values = _kpis_from_pandas(daily, customers)
        source = f"pandas over {config.DAILY_METRICS.name} (database not built)"

    return values, context, source
