"""Pure Plotly chart builders for the four-level dashboard layout page.

These charts demonstrate the information-hierarchy pattern: status first,
then the trend behind each status, then the segment comparison, then the
drill-down detail. Each builder takes data and returns a
``plotly.graph_objects.Figure``, writing nothing, so the page stays
declarative.

Colours come from ``theme.py``, the single palette every chart in the
project shares, so ``Danger`` always means the same thing here as it does
on any other page.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.dashboard import theme
from src.dashboard.theme import PALETTE


def _currency_tick():
    return {"tickprefix": "$", "tickformat": ",.0f"}


# ---------------------------------------------------------------------------
# Level 2: revenue trend with a target reference line
# ---------------------------------------------------------------------------
def build_revenue_trend(daily, currency=True):
    """Daily revenue against a target reference line.

    The target is a period summary, not a hard-coded business number, so a
    fresh extract moves the line with the data. The peak day is annotated in
    the palette's danger colour to draw the eye to the outlier.
    """
    theme.register_plotly_template()

    frame = daily.copy()
    frame = frame.sort_values("date")

    metric = "daily_revenue"
    mean_value = float(frame[metric].mean())
    peak_date = frame.loc[frame[metric].idxmax(), "date"]
    peak_value = float(frame[metric].max())

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame[metric],
            mode="lines+markers",
            name="Daily revenue",
            line={"color": theme.CHART_COLORS[0], "width": 2},
            marker={"size": 5},
            hovertemplate=(
                "<b>%{x|%a %d %b %Y}</b><br>"
                "Revenue: <b>$%{y:,.0f}</b><extra></extra>"
            ),
        )
    )
    figure.add_hline(
        y=mean_value,
        line={"color": PALETTE["success"], "width": 2, "dash": "dot"},
        annotation_text=f"Period average ${mean_value:,.0f}",
        annotation_position="top left",
    )
    figure.add_annotation(
        x=peak_date,
        y=peak_value,
        text=f"Peak ${peak_value:,.0f}",
        showarrow=True,
        arrowhead=2,
        arrowcolor=PALETTE["danger"],
        ax=-55,
        ay=-35,
        bgcolor="#fff8dc",
        bordercolor=PALETTE["neutral"],
        borderwidth=1,
    )
    figure.update_layout(
        title="Daily Revenue Trend",
        xaxis_title="Date",
        yaxis_title="Revenue (USD)",
        yaxis=_currency_tick() if currency else {},
        hovermode="x unified",
        height=420,
        showlegend=False,
        margin={"l": 70, "r": 30, "t": 70, "b": 60},
    )
    return figure


# ---------------------------------------------------------------------------
# Level 2: transactions with rolling average to reveal signal over noise
# ---------------------------------------------------------------------------
def build_transactions_trend(daily):
    """Daily transactions with a 7-day rolling average.

    The raw series swings day to day; the rolling average is the signal the
    eye should read off. The reference line marks the period mean.
    """
    theme.register_plotly_template()

    frame = daily.copy().sort_values("date")
    frame["ma7"] = frame["transaction_count"].rolling(7).mean()
    mean_value = float(frame["transaction_count"].mean())

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=frame["date"],
            y=frame["transaction_count"],
            name="Daily transactions",
            marker={"color": "#b8cfe0", "line": {"width": 0}},
            hovertemplate=(
                "<b>%{x|%a %d %b %Y}</b><br>"
                "Transactions: <b>%{y:,.0f}</b><extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["ma7"],
            mode="lines",
            name="7-day average",
            line={"color": theme.CHART_COLORS[0], "width": 2.5},
            hovertemplate="7-day average: <b>%{y:,.0f}</b><extra></extra>",
        )
    )
    figure.add_hline(
        y=mean_value,
        line={"color": PALETTE["neutral"], "width": 1.5, "dash": "dot"},
        annotation_text=f"Mean {mean_value:,.0f}",
        annotation_position="top left",
    )
    figure.update_layout(
        title="Daily Transactions with 7-Day Average",
        xaxis_title="Date",
        yaxis_title="Transactions",
        yaxis={"tickformat": ",.0f"},
        hovermode="x unified",
        height=420,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        margin={"l": 70, "r": 30, "t": 70, "b": 60},
    )
    return figure


# ---------------------------------------------------------------------------
# Level 3: segment comparison bar chart
# ---------------------------------------------------------------------------
def build_segment_revenue(customers):
    """Revenue contribution by customer segment.

    A horizontal bar because the segment names are words. Data labels sit at
    the bar ends so exact values read without the axis doing the work. Each
    bar keeps its segment colour and marker shape for accessibility.
    """
    theme.register_plotly_template()

    by_segment = (
        customers.groupby("customer_type")
        .agg(
            customers=("customer_id", "count"),
            total_revenue=("lifetime_value", "sum"),
        )
        .sort_values("total_revenue")
    )

    colors = [theme.SEGMENT_COLORS.get(seg, PALETTE["primary"]) for seg in by_segment.index]

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=by_segment["total_revenue"],
            y=by_segment.index,
            orientation="h",
            marker={
                "color": colors,
                "line": {"color": "white", "width": 1.5},
            },
            text=[
                f"${value:,.0f}"
                for value in by_segment["total_revenue"]
            ],
            textposition="outside",
            customdata=by_segment["customers"],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Revenue: <b>$%{x:,.0f}</b><br>"
                "Customers: %{customdata:,}<br>"
                "Avg value per customer: $%{x:,.0f}/%{customdata:,}"
                "<extra></extra>"
            ),
            name="Revenue",
        )
    )

    figure.update_layout(
        title="Lifetime Value by Customer Segment",
        xaxis_title="Total Lifetime Value (USD)",
        yaxis_title="",
        xaxis=_currency_tick(),
        height=420,
        showlegend=False,
        margin={"l": 90, "r": 60, "t": 70, "b": 60},
    )
    return figure


# ---------------------------------------------------------------------------
# Level 3: segment risk comparison (churn against the target)
# ---------------------------------------------------------------------------
def build_segment_risk(customers):
    """Churn rate by segment with the retention target reference line.

    Bars over the target line are revenue at risk; a danger-coloured target
    line makes the threshold legible at a glance.
    """
    theme.register_plotly_template()

    by_segment = (
        customers.groupby("customer_type")
        .agg(churn_rate=("churn", "mean"))
        .sort_values("churn_rate", ascending=False)
    )
    colors = [theme.SEGMENT_COLORS.get(seg, PALETTE["primary"]) for seg in by_segment.index]

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=by_segment.index,
            y=by_segment["churn_rate"],
            marker={
                "color": colors,
                "line": {"color": "white", "width": 1.5},
            },
            text=[f"{value:.1%}" for value in by_segment["churn_rate"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Churn: <b>%{y:.1%}</b><extra></extra>",
            name="Churn rate",
        )
    )
    figure.add_hline(
        y=0.10,
        line={"color": PALETTE["danger"], "width": 2.5, "dash": "dash"},
        annotation_text="Retention target",
        annotation_position="top left",
    )
    figure.update_layout(
        title="Churn Rate by Segment vs Retention Target",
        xaxis_title="",
        yaxis_title="Churn rate",
        yaxis={"tickformat": ".0%"},
        height=420,
        showlegend=False,
        margin={"l": 70, "r": 30, "t": 70, "b": 60},
    )
    return figure
