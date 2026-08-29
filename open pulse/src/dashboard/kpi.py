"""KPI definitions, period comparison, and trend indicators.

Five metrics answering "are we on track?" in one glance. The rules that make
a KPI card correct live here rather than in the page, so the numbers, the
arrows, and the colours cannot disagree with each other.

Two things this module is careful about.

Period comparison is like-for-like. The newest month in the data is almost
always partial, so comparing it against a complete prior month understates
every additive metric. Each comparison is cut to the same number of days.

Direction is a property of the metric, not of the number. Revenue rising is
good; churn rising is not. Every spec declares its direction and the colour
follows from that, so a rising churn rate can never render green.
"""

import numpy as np
import pandas as pd

from src.dashboard import theme


# A change smaller than this reads as flat rather than as movement.
FLAT_THRESHOLD_PCT = 2.0

# Comparison basis for a metric that has no time dimension in this project.
CHURN_TARGET = 0.10


class Direction:
    """Whether a rising value is good news or bad news."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


KPI_SPECS = [
    {
        "key": "revenue",
        "label": "Revenue",
        "direction": Direction.HIGHER_IS_BETTER,
        "format": "currency",
        "question": "Are we bringing in more money than last period?",
        "source": "vw_kpi_summary -> vw_kpi_period_totals -> daily_metrics",
        "basis": "period",
    },
    {
        "key": "transactions",
        "label": "Transactions",
        "direction": Direction.HIGHER_IS_BETTER,
        "format": "count",
        "question": "Are customers buying more often?",
        "source": "vw_kpi_summary -> vw_kpi_period_totals -> daily_metrics",
        "basis": "period",
    },
    {
        "key": "avg_order_value",
        "label": "Avg order value",
        "direction": Direction.HIGHER_IS_BETTER,
        "format": "currency_precise",
        "question": "Is each purchase getting larger or smaller?",
        "source": "vw_kpi_summary, revenue / transactions over the matched window",
        "basis": "period",
    },
    {
        "key": "signups",
        "label": "New signups",
        "direction": Direction.HIGHER_IS_BETTER,
        "format": "count",
        "question": "Is the top of the funnel growing?",
        "source": "vw_kpi_summary -> vw_kpi_period_totals -> daily_metrics",
        "basis": "period",
    },
    {
        "key": "churn_rate",
        "label": "Churn rate",
        "direction": Direction.LOWER_IS_BETTER,
        "format": "percent",
        "question": "Are we keeping the customers we win?",
        "source": "vw_churn_kpi -> customer_segments",
        "basis": "target",
    },
]

SPECS_BY_KEY = {spec["key"]: spec for spec in KPI_SPECS}


# ---------------------------------------------------------------------------
# Period selection
# ---------------------------------------------------------------------------
def matched_month_windows(daily, date_column="date"):
    """Split a daily frame into current and prior month windows of equal length.

    The newest month is usually incomplete. Taking the same number of days from
    the start of each month keeps the two sums comparable; without this, a
    partial month always looks like a collapse.

    Returns the current window, the prior window, and a dict describing them.
    """
    frame = daily.copy()
    frame[date_column] = pd.to_datetime(frame[date_column])
    frame["month"] = frame[date_column].dt.to_period("M")

    current_month = frame["month"].max()
    prior_month = current_month - 1

    current = frame[frame["month"] == current_month].sort_values(date_column)
    prior_full = frame[frame["month"] == prior_month].sort_values(date_column)
    prior = prior_full.head(len(current))

    context = {
        "current_month": str(current_month),
        "prior_month": str(prior_month),
        "window_days": len(current),
        "prior_month_total_days": len(prior_full),
        "current_start": current[date_column].min(),
        "current_end": current[date_column].max(),
        "prior_start": prior[date_column].min() if len(prior) else None,
        "prior_end": prior[date_column].max() if len(prior) else None,
        "prior_truncated": len(prior_full) > len(current),
    }
    return current, prior, context


def percent_change(current_value, prior_value):
    """Percentage change from prior to current, or NaN when undefined."""
    if prior_value in (None, 0) or pd.isna(prior_value) or pd.isna(current_value):
        return np.nan
    return (current_value - prior_value) / abs(prior_value) * 100


# ---------------------------------------------------------------------------
# Trend indicators
# ---------------------------------------------------------------------------
def get_trend_indicator(change_pct, direction=Direction.HIGHER_IS_BETTER):
    """Return the arrow, colour, and status for a change under a direction.

    The arrow follows the number: it points up when the value rose. The colour
    follows the business meaning: it is green only when the movement is good
    for that particular metric. Separating the two is what stops a rising churn
    rate from rendering as a green success.
    """
    if change_pct is None or pd.isna(change_pct):
        return {"arrow": "-", "color": theme.PALETTE["neutral"], "status": "no data"}

    if abs(change_pct) < FLAT_THRESHOLD_PCT:
        return {"arrow": "→", "color": theme.STATUS_COLORS["flat"], "status": "flat"}

    rising = change_pct > 0
    good = rising if direction == Direction.HIGHER_IS_BETTER else not rising
    return {
        "arrow": "↑" if rising else "↓",
        "color": theme.STATUS_COLORS["good" if good else "bad"],
        "status": "on track" if good else "off track",
    }


def format_value(value, style):
    """Format a KPI value for display."""
    if value is None or pd.isna(value):
        return "n/a"
    if style == "currency":
        return theme.fmt_currency(value)
    if style == "currency_precise":
        return f"${value:,.2f}"
    if style == "percent":
        return f"{value * 100:.1f}%"
    return f"{value:,.0f}"


def format_change(change_pct, basis="period"):
    """Format a percentage change with an explicit sign."""
    if change_pct is None or pd.isna(change_pct):
        return None
    suffix = "% vs target" if basis == "target" else "%"
    return f"{change_pct:+.1f}{suffix}"


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build_kpi_table(values):
    """Turn raw current/prior values into the display-ready KPI table.

    ``values`` maps each spec key to a dict with ``current`` and either
    ``prior`` or ``target``.
    """
    rows = []
    for spec in KPI_SPECS:
        entry = values.get(spec["key"])
        if entry is None:
            continue

        current_value = entry.get("current")
        comparison_value = entry.get("prior", entry.get("target"))
        change = entry.get(
            "change_pct", percent_change(current_value, comparison_value)
        )
        indicator = get_trend_indicator(change, spec["direction"])

        rows.append(
            {
                "Metric": spec["label"],
                "Key": spec["key"],
                "Current": current_value,
                "Prior": comparison_value,
                "Change_Pct": change,
                "Arrow": indicator["arrow"],
                "Color": indicator["color"],
                "Status": indicator["status"],
                "Direction": spec["direction"],
                "Basis": spec["basis"],
                "Value_Display": format_value(current_value, spec["format"]),
                "Change_Display": format_change(change, spec["basis"]),
                "Question": spec["question"],
                "Source": spec["source"],
            }
        )
    return pd.DataFrame(rows)


def streamlit_delta_color(direction):
    """Map a metric direction onto Streamlit's delta_color argument.

    Streamlit paints a positive delta green by default. For a metric where
    lower is better, "inverse" flips that so a rising churn rate shows red.
    """
    return (
        "normal" if direction == Direction.HIGHER_IS_BETTER else "inverse"
    )
