"""Churn analysis behind the written narrative.

Every number quoted in docs/CHURN_NARRATIVE.md is produced here, so the story
cannot drift from the data. Nothing in this module writes files or prints.
"""

import pandas as pd

from src.dashboard import data_loader


RETENTION_TARGET = 0.10

# Below this, two measures are treated as unrelated in plain language.
NEGLIGIBLE_CORRELATION = 0.10


def segment_economics(customers, target=RETENTION_TARGET):
    """Per-segment churn, book value, value at risk, and recoverable value."""
    segments = customers.groupby("customer_type").agg(
        customers=("customer_id", "count"),
        churn_rate=("churn", "mean"),
        avg_value=("lifetime_value", "mean"),
        avg_tickets=("support_tickets", "mean"),
        avg_retention_days=("retention_days", "mean"),
    )
    segments["book_value"] = segments["customers"] * segments["avg_value"]
    segments["value_at_risk"] = segments["book_value"] * segments["churn_rate"]
    segments["excess_churn"] = (segments["churn_rate"] - target).clip(lower=0)
    segments["recoverable"] = segments["book_value"] * segments["excess_churn"]
    return segments


def ticket_paradox(customers):
    """Pooled versus within-segment correlation of tickets against churn.

    The pooled figure and the per-segment figures point different ways. That
    reversal is the finding, not a data error: segment drives both measures.
    """
    pooled = float(customers["support_tickets"].corr(customers["churn"]))
    within = {
        segment: float(group["support_tickets"].corr(group["churn"]))
        for segment, group in customers.groupby("customer_type")
    }
    # Present segments largest-first so the reader meets the biggest groups first.
    order = (
        customers["customer_type"].value_counts().index.tolist()
    )
    within = {segment: within[segment] for segment in order if segment in within}
    return pooled, within


def retention_quartiles(customers):
    """Churn and tenure for the newest quarter of customers against the oldest.

    Tenure is the strongest single signal in this dataset, so the narrative
    quotes the gap between the shortest-tenured and longest-tenured quarters.
    """
    quartile = pd.qcut(customers["retention_days"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    grouped = customers.groupby(quartile, observed=True).agg(
        customers=("customer_id", "count"),
        churn_rate=("churn", "mean"),
        avg_days=("retention_days", "mean"),
        max_days=("retention_days", "max"),
    )
    newest, oldest = grouped.loc["Q1"], grouped.loc["Q4"]
    return {
        "table": grouped,
        "newest_churn": float(newest["churn_rate"]),
        "newest_avg_days": float(newest["avg_days"]),
        "newest_cutoff_days": float(newest["max_days"]),
        "newest_cutoff_months": float(newest["max_days"]) / 30.44,
        "oldest_churn": float(oldest["churn_rate"]),
        "oldest_avg_days": float(oldest["avg_days"]),
        "oldest_avg_months": float(oldest["avg_days"]) / 30.44,
    }


def churn_drivers(customers):
    """Correlation of each candidate measure against churn, strongest first."""
    candidates = ["retention_days", "lifetime_value", "support_tickets"]
    drivers = {
        column: float(customers[column].corr(customers["churn"]))
        for column in candidates
    }
    return dict(sorted(drivers.items(), key=lambda item: abs(item[1]), reverse=True))


def small_sample_contrast():
    """The same correlation as measured on the small raw dataset.

    ``analyze_correlations.py`` reports a strong positive link on this file.
    Quoting it alongside the large-sample result is the point: it shows how a
    twenty-row sample can point the opposite way.
    """
    path = data_loader.config.RAW_DIR / "correlation_data.csv"
    if not path.exists():
        return None, 0
    frame = pd.read_csv(path)
    return float(frame["support_tickets"].corr(frame["churn"])), len(frame)


def build_evidence(customers=None, target=RETENTION_TARGET):
    """Assemble every figure the narrative quotes."""
    if customers is None:
        customers = data_loader.load_customer_segment_data()

    segments = segment_economics(customers, target)
    pooled, within = ticket_paradox(customers)
    small_r, small_n = small_sample_contrast()
    drivers = churn_drivers(customers)

    tenure = retention_quartiles(customers)
    recoverable_total = float(segments["recoverable"].sum())
    leader = segments["recoverable"].idxmax()

    return {
        "customers": customers,
        "segments": segments,
        "target": target,
        "total_customers": int(len(customers)),
        "book_value": float(segments["book_value"].sum()),
        "value_at_risk": float(segments["value_at_risk"].sum()),
        "recoverable_total": recoverable_total,
        "leader": str(leader),
        "leader_share": (
            float(segments.loc[leader, "recoverable"]) / recoverable_total
            if recoverable_total
            else 0.0
        ),
        "leader_recoverable": float(segments.loc[leader, "recoverable"]),
        "leader_customers": int(segments.loc[leader, "customers"]),
        "leader_churn": float(segments.loc[leader, "churn_rate"]),
        "worst_rate_segment": str(segments["churn_rate"].idxmax()),
        "worst_rate": float(segments["churn_rate"].max()),
        "largest_exposure_segment": str(segments["value_at_risk"].idxmax()),
        "largest_exposure": float(segments["value_at_risk"].max()),
        "pooled_r": pooled,
        "within_r": within,
        "within_max_abs": max(abs(value) for value in within.values()),
        "small_sample_r": small_r,
        "small_sample_n": small_n,
        "drivers": drivers,
        "tenure": tenure,
        "segment_count": int(len(segments)),
        # Same flat band the KPI cards use: a segment a fraction of a percent
        # off target counts as at target, not above it. Without this the story
        # would contradict the executive summary page over Startup at 10.02%.
        "over_target": segments[
            (segments["churn_rate"] - target) / target * 100 > 2.0
        ].index.tolist(),
        "single_account_value": float(segments.loc["Enterprise", "avg_value"]),
    }
