"""The five business charts, one builder each.

Every function is pure: it takes data, returns a matplotlib ``Figure``, and
writes nothing. ``scripts/build_charts.py`` saves the figures as PNG files and
the Streamlit pages hand the same figures to ``st.pyplot``, so the printed
report and the dashboard can never drift apart.

Each chart follows the same labelling contract: a title that states the
finding rather than the chart type, both axes labelled with units, a legend
whenever more than one series is drawn, readable data labels, and at least one
annotation or reference line that says what the viewer should notice.
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from src.dashboard import theme
from src.dashboard.theme import PALETTE


def _source_note(fig, text):
    """Stamp the data source along the bottom of a figure."""
    fig.text(
        0.01,
        0.01,
        text,
        fontsize=8,
        color=PALETTE["neutral"],
        ha="left",
        va="bottom",
    )


# ---------------------------------------------------------------------------
# Chart 1: comparison across categories
# ---------------------------------------------------------------------------
def build_revenue_by_product(revenue_by_product):
    """Horizontal bar chart comparing total revenue across product lines."""
    theme.apply_matplotlib_theme()
    ordered = revenue_by_product.sort_values()
    total = float(ordered.sum())
    average = float(ordered.mean())

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [theme.PRODUCT_COLORS.get(name, PALETTE["primary"]) for name in ordered.index]
    bars = ax.barh(ordered.index, ordered.values, color=colors, edgecolor="white")

    ax.bar_label(
        bars,
        labels=[theme.fmt_currency(value) for value in ordered.values],
        padding=6,
        fontsize=11,
        fontweight="bold",
    )

    ax.axvline(
        average,
        color=PALETTE["neutral"],
        linestyle="--",
        linewidth=1.8,
        label=f"Average per product ({theme.fmt_currency(average)})",
    )

    leader = ordered.index[-1]
    leader_value = float(ordered.iloc[-1])
    ax.annotate(
        f"{leader} tier earns {leader_value / total:.1%}\nof all revenue",
        xy=(leader_value * 0.86, len(ordered) - 1.35),
        xytext=(leader_value * 0.60, len(ordered) - 1.85),
        arrowprops={"arrowstyle": "->", "color": PALETTE["danger"], "lw": 2},
        fontsize=11,
        ha="center",
        bbox=theme.annotation_box(),
    )

    ax.set_title("The Enterprise Tier Drives Six in Ten Revenue Dollars")
    ax.set_xlabel("Revenue (USD)")
    ax.set_ylabel("Product Line")
    ax.set_xlim(0, float(ordered.max()) * 1.22)
    theme.currency_axis(ax, axis="x")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right")

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _source_note(fig, "Source: output/segment_product_revenue_pivot.csv (analyze_segments.py)")
    return fig


# ---------------------------------------------------------------------------
# Chart 2: trend over time
# ---------------------------------------------------------------------------
def build_revenue_trend(trend):
    """Line chart of daily revenue against its 7- and 30-day rolling averages."""
    theme.apply_matplotlib_theme()
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(
        trend.index,
        trend["revenue"],
        color=PALETTE["neutral"],
        linewidth=1,
        alpha=0.45,
        label="Daily revenue (raw)",
    )
    ax.plot(
        trend.index,
        trend["revenue_ma7"],
        color=theme.CHART_COLORS[0],
        linewidth=2.2,
        linestyle="-",
        label="7-day moving average",
    )
    ax.plot(
        trend.index,
        trend["revenue_ma30"],
        color=theme.CHART_COLORS[1],
        linewidth=2.6,
        linestyle="--",
        label="30-day moving average",
    )

    mean_revenue = float(trend["revenue"].mean())
    ax.axhline(
        mean_revenue,
        color=PALETTE["success"],
        linestyle=":",
        linewidth=2,
        label=f"Period average ({theme.fmt_currency(mean_revenue)})",
    )

    peak_date = trend["revenue"].idxmax()
    peak_value = float(trend["revenue"].max())
    ax.annotate(
        f"Peak {theme.fmt_currency(peak_value)}\n{peak_date:%d %b %Y}",
        xy=(peak_date, peak_value),
        xytext=(-95, -6),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": PALETTE["danger"], "lw": 2},
        fontsize=10,
        ha="center",
        bbox=theme.annotation_box(),
    )

    ax.set_title("Revenue Growth Is a Sustained Trend, Not Daily Noise")
    ax.set_xlabel("Date")
    ax.set_ylabel("Revenue (USD)")
    theme.currency_axis(ax, axis="y")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=1))
    ax.legend(loc="upper left")
    fig.autofmt_xdate(rotation=45, ha="right")

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _source_note(
        fig,
        "Source: output/revenue_trend_features.csv (analyze_revenue_trends.py) "
        f"| {len(trend)} days, {trend.index.min():%d %b} to {trend.index.max():%d %b %Y}",
    )
    return fig


# ---------------------------------------------------------------------------
# Chart 3: distribution of values
# ---------------------------------------------------------------------------
def build_value_distribution(customers, statistics):
    """Histogram of customer lifetime value on a logarithmic value axis."""
    theme.apply_matplotlib_theme()
    values = customers["lifetime_value"].dropna()
    mean_value = statistics["mean"]
    median_value = statistics["median"]

    fig, ax = plt.subplots(figsize=(11, 6))
    bins = np.logspace(np.log10(values.min()), np.log10(values.max()), 40)
    ax.hist(
        values,
        bins=bins,
        color=theme.CHART_COLORS[0],
        edgecolor="white",
        linewidth=0.6,
    )
    ax.set_xscale("log")

    ax.axvline(
        median_value,
        color=PALETTE["success"],
        linestyle="-",
        linewidth=2.4,
        label=f"Median ({theme.fmt_currency(median_value)})",
    )
    ax.axvline(
        mean_value,
        color=PALETTE["danger"],
        linestyle="--",
        linewidth=2.4,
        label=f"Mean ({theme.fmt_currency(mean_value)})",
    )

    top_1pct = statistics["percentiles"]["0.99"]
    ax.annotate(
        f"Mean sits {mean_value / median_value:.1f}x above the median.\n"
        f"Skewness {statistics['skewness']:.2f}: report the median,\n"
        f"not the mean, as the typical customer.",
        xy=(mean_value, ax.get_ylim()[1] * 0.62),
        xytext=(mean_value * 3.2, ax.get_ylim()[1] * 0.74),
        arrowprops={"arrowstyle": "->", "color": PALETTE["danger"], "lw": 2},
        fontsize=10,
        ha="left",
        bbox=theme.annotation_box(),
    )
    ax.annotate(
        f"Top 1% above\n{theme.fmt_currency(top_1pct)}",
        xy=(top_1pct, ax.get_ylim()[1] * 0.08),
        xytext=(top_1pct * 0.30, ax.get_ylim()[1] * 0.30),
        arrowprops={"arrowstyle": "->", "color": PALETTE["neutral"], "lw": 1.6},
        fontsize=9,
        ha="center",
        bbox=theme.annotation_box("#f0f0f0"),
    )

    ax.set_title(f"Customer Value Is Heavily Right-Skewed (n = {statistics['count']:,})")
    ax.set_xlabel("Lifetime Value (USD, logarithmic scale)")
    ax.set_ylabel("Number of Customers")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(theme.fmt_currency))
    ax.legend(loc="upper right")

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _source_note(
        fig,
        "Source: output/customer_segment_data.csv (segment_analysis.py) | "
        "statistics via analyze_revenue_distribution.analyze_revenue()",
    )
    return fig


# ---------------------------------------------------------------------------
# Chart 4: composition / part-to-whole
# ---------------------------------------------------------------------------
def build_revenue_composition(pivot, segment_metrics):
    """Stacked bar chart of revenue composition by segment and product."""
    theme.apply_matplotlib_theme()
    ordered = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    totals = ordered.sum(axis=1)
    grand_total = float(totals.sum())

    fig, ax = plt.subplots(figsize=(10, 6.5))
    axis_top = float(totals.max()) * 1.24
    bottom = np.zeros(len(ordered))
    for product in ordered.columns:
        values = ordered[product].to_numpy(dtype=float)
        fill = theme.PRODUCT_COLORS[product]
        ax.bar(
            ordered.index,
            values,
            bottom=bottom,
            color=fill,
            edgecolor="white",
            linewidth=1.2,
            label=product,
        )
        for x_position, (value, base) in enumerate(zip(values, bottom)):
            # Label only stacks tall enough to hold the text without colliding
            # with the segment above or below it.
            if value / axis_top > 0.055:
                ax.text(
                    x_position,
                    base + value / 2,
                    theme.fmt_currency(value),
                    ha="center",
                    va="center",
                    fontsize=10,
                    color=theme.label_color(fill),
                    fontweight="bold",
                )
        bottom += values

    for x_position, total in enumerate(totals):
        ax.text(
            x_position,
            total * 1.02,
            f"{theme.fmt_currency(total)}\n({total / grand_total:.1%})",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    leader = totals.index[0]
    leader_share = segment_metrics.loc[leader, "revenue_contribution"] / 100
    ax.annotate(
        f"The {leader} segment is {leader_share:.1%} of revenue\n"
        f"from only {int(segment_metrics.loc[leader, 'customer_count'])} customers",
        xy=(0.34, float(totals.iloc[0]) * 0.80),
        xytext=(0.75, float(totals.max()) * 1.02),
        arrowprops={"arrowstyle": "->", "color": PALETTE["danger"], "lw": 2},
        fontsize=10,
        ha="left",
        bbox=theme.annotation_box(),
    )

    ax.set_title("Revenue Concentrates in One Segment and One Product Tier")
    ax.set_xlabel("Customer Segment")
    ax.set_ylabel("Revenue (USD)")
    ax.set_ylim(0, axis_top)
    theme.currency_axis(ax, axis="y")
    ax.grid(axis="x", visible=False)
    ax.legend(title="Product Line", loc="upper right")

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _source_note(fig, "Source: output/segment_product_revenue_pivot.csv (analyze_segments.py)")
    return fig


# ---------------------------------------------------------------------------
# Chart 5: correlation between two variables
# ---------------------------------------------------------------------------
def build_tickets_vs_value(customers):
    """Scatter plot relating support ticket volume to customer lifetime value."""
    theme.apply_matplotlib_theme()
    frame = customers.dropna(subset=["support_tickets", "lifetime_value"])
    tickets = frame["support_tickets"].to_numpy(dtype=float)
    value = frame["lifetime_value"].to_numpy(dtype=float)

    pearson = float(np.corrcoef(tickets, value)[0, 1])
    spearman = float(
        np.corrcoef(
            frame["support_tickets"].rank().to_numpy(),
            frame["lifetime_value"].rank().to_numpy(),
        )[0, 1]
    )

    fig, ax = plt.subplots(figsize=(11, 6.5))
    # Ticket counts are integers, so raw points collapse into vertical stripes.
    # A small deterministic horizontal jitter restores the visible density
    # without moving any point far enough to misread its ticket count.
    rng = np.random.default_rng(42)
    for segment, group in frame.groupby("customer_type", sort=False):
        jitter = rng.uniform(-0.22, 0.22, len(group))
        ax.scatter(
            group["support_tickets"] + jitter,
            group["lifetime_value"],
            s=26,
            alpha=0.45,
            color=theme.SEGMENT_COLORS.get(segment, PALETTE["primary"]),
            marker=theme.SEGMENT_MARKERS.get(segment, "o"),
            edgecolors="none",
            label=f"{segment} (n={len(group)})",
        )

    ax.set_yscale("log")
    slope, intercept = np.polyfit(tickets, np.log10(value), 1)
    line_x = np.linspace(tickets.min(), tickets.max(), 100)
    ax.plot(
        line_x,
        10 ** (slope * line_x + intercept),
        color=PALETTE["danger"],
        linewidth=2.4,
        linestyle="--",
        label="Fitted trend (log-linear)",
    )

    enterprise = frame[frame["customer_type"] == "Enterprise"]
    if not enterprise.empty:
        ax.annotate(
            f"Enterprise: {enterprise['support_tickets'].mean():.1f} tickets and\n"
            f"{theme.fmt_currency(enterprise['lifetime_value'].mean())} average value.\n"
            "Support load follows value, not dissatisfaction.",
            xy=(
                float(enterprise["support_tickets"].mean()),
                float(enterprise["lifetime_value"].mean()),
            ),
            xytext=(1.2, 32_000),
            arrowprops={
                "arrowstyle": "->",
                "color": PALETTE["danger"],
                "lw": 2,
                "connectionstyle": "arc3,rad=-0.18",
            },
            fontsize=10,
            ha="left",
            bbox=theme.annotation_box(),
        )

    ax.text(
        0.015,
        0.97,
        f"Pearson r = {pearson:.2f}\nSpearman rho = {spearman:.2f}",
        transform=ax.transAxes,
        fontsize=11,
        va="top",
        ha="left",
        bbox=theme.annotation_box("#eef4fa"),
    )

    ax.set_title("Higher-Value Customers Open More Support Tickets")
    ax.set_xlabel("Support Tickets (count per customer)")
    ax.set_ylabel("Lifetime Value (USD, logarithmic scale)")
    theme.currency_axis(ax, axis="y")

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, title="Customer Segment", loc="lower right", ncol=2)

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _source_note(
        fig,
        "Source: output/customer_segment_data.csv (segment_analysis.py) | "
        "correlation is association only, not causation",
    )
    return fig, {"pearson": pearson, "spearman": spearman}
