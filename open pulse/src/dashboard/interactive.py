"""Interactive Plotly counterparts to the static charts.

These builders answer the follow-up questions a static image cannot: hover
reveals the exact value, the dropdown switches metric without a reload, and
zoom, pan, and box select let a viewer explore a region on their own.

They sit alongside ``charts.py`` rather than replacing it. The static PNGs
remain the print and report path; these are the exploration path. Both read
the same loaders and draw from the same palette in ``theme.py``, so a colour
means the same thing in both.

Every builder is pure: it takes data and returns a ``plotly.graph_objects``
figure, writing nothing. ``scripts/build_interactive_charts.py`` exports them
as standalone HTML and the Streamlit page renders the same objects.
"""

import numpy as np
import plotly.graph_objects as go

from src.dashboard import theme
from src.dashboard.theme import PALETTE


def _currency_axis_prefix():
    """Return the tick settings that render an axis as compact currency."""
    return {"tickprefix": "$", "tickformat": ",.0f"}


# ---------------------------------------------------------------------------
# Chart 1: revenue trend with a rich hover and a date range selector
# ---------------------------------------------------------------------------
def build_revenue_trend(trend):
    """Daily revenue with rolling averages, rich hover, and range controls.

    The hover carries four fields the axes do not show - order count, average
    order value, and the 7-day average - so a viewer can read the full daily
    picture without the chart surface carrying any data labels.
    """
    theme.register_plotly_template()

    orders = trend["orders"].to_numpy(dtype=float)
    revenue = trend["revenue"].to_numpy(dtype=float)
    average_order_value = np.divide(
        revenue, orders, out=np.zeros_like(revenue), where=orders > 0
    )
    customdata = np.column_stack(
        [orders, average_order_value, trend["revenue_ma7"].to_numpy(dtype=float)]
    )

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=trend.index,
            y=trend["revenue"],
            mode="lines+markers",
            name="Daily revenue",
            line={"color": PALETTE["neutral"], "width": 1},
            marker={"size": 5, "color": theme.CHART_COLORS[0]},
            customdata=customdata,
            hovertemplate=(
                "<b>%{x|%a %d %b %Y}</b><br>"
                "Revenue: <b>$%{y:,.0f}</b><br>"
                "Orders: %{customdata[0]:,.0f}<br>"
                "Average order: $%{customdata[1]:,.2f}<br>"
                "7-day average: $%{customdata[2]:,.0f}"
                "<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=trend.index,
            y=trend["revenue_ma7"],
            mode="lines",
            name="7-day average",
            line={"color": theme.CHART_COLORS[0], "width": 2.5},
            hovertemplate="7-day average: $%{y:,.0f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=trend.index,
            y=trend["revenue_ma30"],
            mode="lines",
            name="30-day average",
            line={"color": theme.CHART_COLORS[1], "width": 2.5, "dash": "dash"},
            hovertemplate="30-day average: $%{y:,.0f}<extra></extra>",
        )
    )

    mean_revenue = float(trend["revenue"].mean())
    figure.add_hline(
        y=mean_revenue,
        line={"color": PALETTE["success"], "width": 2, "dash": "dot"},
        annotation_text=f"Period average ${mean_revenue:,.0f}",
        annotation_position="top left",
    )

    peak_date = trend["revenue"].idxmax()
    peak_value = float(trend["revenue"].max())
    figure.add_annotation(
        # Serialised as an ISO string rather than a pandas Timestamp: Plotly's
        # own encoder handles Timestamp, but stricter JSON encoders used by
        # image export and some embedding paths do not.
        x=peak_date.isoformat(),
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

    # Range controls. The source spans 59 days, so the buttons are expressed in
    # days and weeks; the month-and-quarter buttons of a twelve-month chart
    # would select ranges this dataset does not contain.
    figure.update_xaxes(
        rangeselector={
            "buttons": [
                {"count": 7, "label": "7D", "step": "day", "stepmode": "backward"},
                {"count": 14, "label": "14D", "step": "day", "stepmode": "backward"},
                {"count": 1, "label": "1M", "step": "month", "stepmode": "backward"},
                {"step": "all", "label": "All"},
            ],
            "bgcolor": "#f2f2f2",
            "activecolor": theme.CHART_COLORS[0],
            "x": 0,
            "y": 1.10,
        },
        rangeslider={"visible": True, "thickness": 0.08},
        type="date",
    )
    figure.update_layout(
        title={
            "text": "Daily Revenue Trend - hover for detail, drag to zoom",
            "y": 0.97,
            "yanchor": "top",
        },
        xaxis_title="Date",
        yaxis_title="Revenue (USD)",
        yaxis=_currency_axis_prefix(),
        hovermode="x unified",
        height=600,
        margin={"l": 70, "r": 30, "t": 150, "b": 60},
        dragmode="zoom",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.24, "x": 0},
    )
    return figure


# ---------------------------------------------------------------------------
# Chart 2: product performance with a multi-field hover
# ---------------------------------------------------------------------------
def build_product_performance(product_metrics):
    """Revenue by product line, with four supporting fields on hover."""
    theme.register_plotly_template()

    customdata = np.column_stack(
        [
            product_metrics["customers"].to_numpy(dtype=float),
            product_metrics["avg_revenue_per_customer"].to_numpy(dtype=float),
            product_metrics["revenue_share_pct"].to_numpy(dtype=float),
        ]
    )
    colors = [theme.PRODUCT_COLORS[name] for name in product_metrics.index]

    figure = go.Figure(
        go.Bar(
            x=product_metrics.index,
            y=product_metrics["revenue"],
            marker={"color": colors, "line": {"color": "white", "width": 1.5}},
            customdata=customdata,
            text=[f"${value:,.0f}" for value in product_metrics["revenue"]],
            textposition="outside",
            hovertemplate=(
                "<b>%{x} tier</b><br>"
                "Revenue: <b>$%{y:,.0f}</b><br>"
                "Customers: %{customdata[0]:,.0f}<br>"
                "Average per customer: $%{customdata[1]:,.2f}<br>"
                "Share of total revenue: %{customdata[2]:.1f}%"
                "<extra></extra>"
            ),
            name="Revenue",
        )
    )
    figure.update_layout(
        title="Revenue by Product Line - hover for customers and average value",
        xaxis_title="Product Line",
        yaxis_title="Revenue (USD)",
        yaxis=_currency_axis_prefix(),
        hovermode="closest",
        height=520,
        showlegend=False,
    )
    figure.update_yaxes(range=[0, float(product_metrics["revenue"].max()) * 1.18])
    return figure


# ---------------------------------------------------------------------------
# Chart 3: dropdown that switches metric without reloading
# ---------------------------------------------------------------------------
def build_metric_selector(product_metrics):
    """One chart, three metrics, switched by a dropdown.

    All three traces are loaded up front and the dropdown toggles visibility,
    so switching metric is instant and needs no callback, rerun, or request.
    """
    theme.register_plotly_template()

    views = [
        {
            "key": "revenue",
            "label": "Revenue",
            "title": "Revenue by Product Line",
            "axis": "Revenue (USD)",
            "values": product_metrics["revenue"],
            "text": [f"${value:,.0f}" for value in product_metrics["revenue"]],
            "hover": "Revenue: <b>$%{y:,.0f}</b>",
            "tick": {"tickprefix": "$", "tickformat": ",.0f"},
        },
        {
            "key": "customers",
            "label": "Customer count",
            "title": "Customers by Product Line",
            "axis": "Customers",
            "values": product_metrics["customers"],
            "text": [f"{value:,.0f}" for value in product_metrics["customers"]],
            "hover": "Customers: <b>%{y:,.0f}</b>",
            "tick": {"tickprefix": "", "tickformat": ",.0f"},
        },
        {
            "key": "avg_revenue_per_customer",
            "label": "Average revenue per customer",
            "title": "Average Revenue per Customer by Product Line",
            "axis": "Average revenue per customer (USD)",
            "values": product_metrics["avg_revenue_per_customer"],
            "text": [
                f"${value:,.0f}"
                for value in product_metrics["avg_revenue_per_customer"]
            ],
            "hover": "Average per customer: <b>$%{y:,.2f}</b>",
            "tick": {"tickprefix": "$", "tickformat": ",.0f"},
        },
    ]

    # Product colour is fixed across every chart in the project, so the bars
    # keep their tier colours and only the metric behind them changes. Recolouring
    # the bars per metric would break the "Basic is always this blue" rule that
    # the static charts establish.
    bar_colors = [theme.PRODUCT_COLORS[name] for name in product_metrics.index]

    figure = go.Figure()
    for index, view in enumerate(views):
        figure.add_trace(
            go.Bar(
                x=product_metrics.index,
                y=view["values"],
                name=view["label"],
                marker={"color": bar_colors, "line": {"color": "white", "width": 1.5}},
                text=view["text"],
                textposition="outside",
                hovertemplate="<b>%{x} tier</b><br>" + view["hover"] + "<extra></extra>",
                visible=index == 0,
            )
        )

    buttons = []
    for index, view in enumerate(views):
        visibility = [position == index for position in range(len(views))]
        headroom = float(max(view["values"])) * 1.18
        buttons.append(
            {
                "label": view["label"],
                "method": "update",
                "args": [
                    {"visible": visibility},
                    {
                        "title": view["title"] + " - switched without reloading",
                        "yaxis": {
                            "title": {"text": view["axis"]},
                            "range": [0, headroom],
                            "gridcolor": "#e6e6e6",
                            **view["tick"],
                        },
                    },
                ],
            }
        )

    figure.update_layout(
        title=views[0]["title"] + " - switched without reloading",
        xaxis_title="Product Line",
        yaxis={
            "title": {"text": views[0]["axis"]},
            "range": [0, float(max(views[0]["values"])) * 1.18],
            **views[0]["tick"],
        },
        height=600,
        margin={"l": 70, "r": 30, "t": 130, "b": 60},
        showlegend=False,
        updatemenus=[
            {
                "active": 0,
                "buttons": buttons,
                "direction": "down",
                "x": 1.0,
                "xanchor": "right",
                "y": 1.17,
                "yanchor": "top",
                "bgcolor": "white",
                "bordercolor": "#cccccc",
                "borderwidth": 1,
                "pad": {"l": 4, "r": 4, "t": 4, "b": 4},
            }
        ],
        annotations=[
            {
                "text": "Metric",
                "showarrow": False,
                "x": 1.0,
                "xref": "paper",
                "xanchor": "right",
                "y": 1.19,
                "yref": "paper",
                "yanchor": "bottom",
                "font": {"size": 12, "color": PALETTE["neutral"]},
            }
        ],
    )
    return figure


# ---------------------------------------------------------------------------
# Chart 4: scatter built for zoom, pan, and selection
# ---------------------------------------------------------------------------
def build_scatter_explorer(customers):
    """Support tickets against lifetime value, built for exploration.

    A thousand points is more than any static image can resolve, which is what
    makes zoom, pan, and box select worth having here: a viewer can isolate one
    segment's cluster and read individual customers out of it.
    """
    theme.register_plotly_template()

    symbols = {
        "Enterprise": "circle",
        "SMB": "square",
        "Startup": "triangle-up",
        "Individual": "diamond",
    }

    # Ticket counts are integers, so raw points collapse into vertical stripes.
    # The marker positions carry a small deterministic jitter, while the hover
    # reads the true count out of customdata rather than off the jittered axis.
    rng = np.random.default_rng(42)

    figure = go.Figure()
    for segment, group in customers.groupby("customer_type", sort=False):
        customdata = np.column_stack(
            [
                group["customer_id"].to_numpy(),
                group["region"].to_numpy(),
                group["product_tier"].to_numpy(),
                group["retention_days"].to_numpy(),
                group["support_tickets"].to_numpy(),
            ]
        )
        jitter = rng.uniform(-0.22, 0.22, len(group))
        figure.add_trace(
            go.Scattergl(
                x=group["support_tickets"] + jitter,
                y=group["lifetime_value"],
                mode="markers",
                name=f"{segment} (n={len(group)})",
                marker={
                    "size": 7,
                    "opacity": 0.6,
                    "color": theme.SEGMENT_COLORS.get(segment, PALETTE["primary"]),
                    "symbol": symbols.get(segment, "circle"),
                    "line": {"width": 0},
                },
                customdata=customdata,
                hovertemplate=(
                    "<b>Customer %{customdata[0]}</b><br>"
                    f"Segment: {segment}<br>"
                    "Region: %{customdata[1]}<br>"
                    "Tier: %{customdata[2]}<br>"
                    "Lifetime value: <b>$%{y:,.0f}</b><br>"
                    "Support tickets: %{customdata[4]:,.0f}<br>"
                    "Retention: %{customdata[3]:,.0f} days"
                    "<extra></extra>"
                ),
            )
        )

    tickets = customers["support_tickets"].to_numpy(dtype=float)
    value = customers["lifetime_value"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(tickets, np.log10(value), 1)
    line_x = np.linspace(tickets.min(), tickets.max(), 100)
    figure.add_trace(
        go.Scatter(
            x=line_x,
            y=10 ** (slope * line_x + intercept),
            mode="lines",
            name="Fitted trend",
            line={"color": PALETTE["danger"], "width": 2.5, "dash": "dash"},
            hoverinfo="skip",
        )
    )

    correlation = float(np.corrcoef(tickets, value)[0, 1])
    figure.add_annotation(
        text=f"Pearson r = {correlation:.2f}",
        xref="paper",
        yref="paper",
        x=0.01,
        y=0.99,
        showarrow=False,
        bgcolor="#eef4fa",
        bordercolor=PALETTE["neutral"],
        borderwidth=1,
        font={"size": 13},
    )

    figure.update_layout(
        title="Support Tickets vs Lifetime Value - drag to zoom, double-click to reset",
        xaxis_title="Support Tickets (count per customer)",
        yaxis_title="Lifetime Value (USD, log scale)",
        # A "$" tickprefix on a log axis only lands on the decade ticks, so the
        # minor ticks would read "50,000" beside "$100,000". The unit is carried
        # by the axis title instead, which keeps every tick label consistent.
        yaxis={"type": "log", "tickformat": ",.0f"},
        height=620,
        dragmode="zoom",
        hovermode="closest",
        legend={"title": {"text": "Customer Segment"}, "yanchor": "bottom", "y": 0.02, "x": 0.78},
    )
    return figure, {"pearson": correlation}
