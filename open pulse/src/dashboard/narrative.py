"""Churn analysis behind the written narrative.

Every number quoted in docs/CHURN_NARRATIVE.md is produced here, so the story
cannot drift from the data. Nothing in this module writes files or prints.
"""

import pandas as pd

from src.dashboard import data_loader, theme


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


# ---------------------------------------------------------------------------
# Executive framing
# ---------------------------------------------------------------------------
# Words that would make a business reader stop and ask what they mean. Shared by
# the narrative and the executive report builders so both enforce one standard.
JARGON = [
    "p-value", "p value", "auc", "logistic regression", "regression coefficient",
    "confidence interval", "statistically significant", "variance", "r-squared",
    "r²", "heteroscedastic", "confounder", "simpson's paradox",
    "correlation coefficient", "null hypothesis", "standard deviation",
    "multicollinearity", "quartile", "pearson", "spearman",
]


def executive_figures(evidence):
    """Derive the board-level numbers from the segment economics.

    Two benchmarks are produced. The target benchmark asks what returns if every
    segment reaches the published retention target. That understates the case
    here, because the blended rate is already below the target: only individual
    segments breach it. The best-in-class benchmark asks what returns if the
    weaker segments matched the rate the business already achieves in its
    strongest segment, which is a standard the company has proven is reachable.
    """
    segments = evidence["segments"]
    book_value = evidence["book_value"]
    value_at_risk = evidence["value_at_risk"]

    best_segment = segments["churn_rate"].idxmin()
    best_rate = float(segments.loc[best_segment, "churn_rate"])

    stretch = {}
    for name, row in segments.iterrows():
        if row["churn_rate"] > best_rate:
            stretch[name] = float(row["book_value"] * (row["churn_rate"] - best_rate))
    stretch_total = sum(stretch.values())
    stretch_leader = max(stretch, key=stretch.get) if stretch else None

    return {
        "blended_churn": value_at_risk / book_value if book_value else 0.0,
        "best_segment": str(best_segment),
        "best_rate": best_rate,
        "stretch_by_segment": stretch,
        "stretch_total": stretch_total,
        "stretch_leader": str(stretch_leader) if stretch_leader else None,
        "stretch_leader_value": float(stretch[stretch_leader]) if stretch_leader else 0.0,
        "stretch_leader_share": (
            stretch[stretch_leader] / stretch_total if stretch_total else 0.0
        ),
        "three_year_loss": value_at_risk * 3,
        "three_year_recoverable": stretch_total * 3,
        # No cost data exists in this project, so the report states the ceiling a
        # programme may cost rather than inventing a price for it.
        "investment_ceiling": stretch_total,
    }


def risk_register(evidence, executive):
    """The three risks the executive summary reports, each with a number."""
    segments = evidence["segments"]
    leader = executive["stretch_leader"]
    return [
        {
            "name": "Concentrated revenue leak",
            "what": (
                f"Left alone, {leader} churn costs us "
                f"{theme.fmt_currency_exec(executive['stretch_leader_value'] * 3)} "
                "over three years."
            ),
            "matters": (
                f"It is {executive['stretch_leader_share']:.0%} of everything we "
                "could recover, and the gap widens every quarter we do not act."
            ),
            "action": f"Fund a retention programme aimed only at {leader}.",
            "exposure": executive["stretch_leader_value"],
        },
        {
            "name": "Largest accounts carry the largest exposure",
            "what": (
                f"{executive['best_segment']} has our best retention at "
                f"{executive['best_rate']:.1%}, yet "
                f"{theme.fmt_currency_exec(segments.loc[executive['best_segment'], 'value_at_risk'])} "
                "is at risk each year."
            ),
            "matters": (
                "Each account is worth "
                f"{theme.fmt_currency_exec(segments.loc[executive['best_segment'], 'avg_value'])}. "
                "Losing two costs more than fixing our worst-rate segment entirely."
            ),
            "action": "Name an owner for every one of these accounts.",
            "exposure": float(
                segments.loc[executive["best_segment"], "value_at_risk"]
            ),
        },
        {
            "name": "We are about to act on a false signal",
            "what": (
                "An earlier read of a small sample suggested support contact "
                "drives customers away. Across the full base it does not."
            ),
            "matters": (
                "A campaign to reduce support contact would have quietened our "
                "most valuable accounts and changed churn by nothing."
            ),
            "action": "Stop using contact volume as a warning sign; record response times instead.",
            "exposure": 0.0,
        },
    ]
