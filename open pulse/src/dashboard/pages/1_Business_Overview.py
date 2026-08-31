"""Page: the five core business relationships, one chart each.

Reached through ``src/dashboard/app.py``, which puts the project root on
sys.path before this module is imported.
"""

import streamlit as st

from src.dashboard import charts, components, config, data_loader, theme



def render():
    """Draw the whole page."""
    components.page_header(
        "Business Overview",
        "Five relationships in the data, each matched to the chart type built for it.",
        question="Where does revenue come from, where is it going, and what drives it?",
    )

    try:
        revenue_by_product = data_loader.load_revenue_by_product()
        pivot = data_loader.load_segment_product_pivot()
        segment_metrics = data_loader.load_segment_metrics()
        trend = data_loader.load_revenue_trend()
        trend_summary = data_loader.load_revenue_trend_summary()
        customers = data_loader.load_customer_segment_data()
        distribution = data_loader.load_value_distribution_stats()
    except data_loader.MissingArtifactError as error:
        components.missing_artifact_warning(error)
        return

    total_revenue = float(revenue_by_product.sum())
    leader = str(revenue_by_product.index[0])
    leader_share = float(revenue_by_product.iloc[0]) / total_revenue
    top_segment = str(segment_metrics["total_revenue"].idxmax())

    components.kpi_row(
        [
            {
                "label": "Total revenue",
                "value": theme.fmt_currency(total_revenue),
                "help": "Sum across all product lines and customer segments.",
            },
            {
                "label": "Leading product",
                "value": leader,
                "caption": f"{leader_share:.1%} of revenue",
                "help": "Product line with the largest revenue contribution.",
            },
            {
                "label": "Revenue trend",
                "value": trend_summary["trend_direction"].upper(),
                "delta": f"{trend_summary['trend_magnitude_pct']:.1f}% over {len(trend)} days",
                "help": "Direction of the 30-day rolling average over the period.",
            },
            {
                "label": "Median customer value",
                "value": theme.fmt_currency(distribution["median"]),
                "caption": f"mean {theme.fmt_currency(distribution['mean'])}",
                "help": (
                    "The distribution is right-skewed, so the median is the "
                    "honest description of a typical customer."
                ),
            },
            {
                "label": "Leading segment",
                "value": top_segment,
                "caption": f"{segment_metrics['revenue_contribution'].max():.1f}% of revenue",
                "help": "Customer segment contributing the most revenue.",
            },
        ]
    )

    st.divider()

    tabs = st.tabs(
        [
            "Which product earns most?",
            "Is revenue really growing?",
            "What is a customer worth?",
            "What makes up each segment?",
            "What drives support load?",
        ]
    )

    with tabs[0]:
        components.chart_block(
            charts.build_revenue_by_product(revenue_by_product),
            insight=(
                f"{leader} generates {theme.fmt_currency(total_revenue * leader_share)}, "
                f"{leader_share:.1%} of all revenue. Only this tier sits above the "
                "per-product average."
            ),
            filename=config.CHART_FILES[1].name,
            chart_type="Bar chart",
            rationale=(
                "Product lines are discrete categories, so the relationship is "
                "**comparison**. The eye judges bar length far more accurately than "
                "angle or area, which is why a bar chart beats a pie chart here. "
                "Bars run horizontally because the category names are words."
            ),
            key="chart1",
        )

    with tabs[1]:
        components.chart_block(
            charts.build_revenue_trend(trend),
            insight=(
                f"The 30-day average rose {trend_summary['trend_magnitude_pct']:.1f}% "
                f"across {len(trend)} days. The raw series swings weekly, but both "
                "rolling averages climb steadily, so the growth is a trend and not noise."
            ),
            filename=config.CHART_FILES[2].name,
            chart_type="Line chart",
            rationale=(
                "Time is continuous, so a line is the correct mark: it implies that "
                "the values between two points are meaningful. Plotting the raw series "
                "underneath its own moving averages separates signal from weekly noise. "
                "Note the scope: this source holds "
                f"**{len(trend)} days** and carries no product dimension."
            ),
            key="chart2",
        )

    with tabs[2]:
        components.chart_block(
            charts.build_value_distribution(customers, distribution),
            insight=(
                f"Values run from {theme.fmt_currency(distribution['min'])} to "
                f"{theme.fmt_currency(distribution['max'])} with skewness "
                f"{distribution['skewness']:.2f}. The mean sits "
                f"{distribution['mean'] / distribution['median']:.1f}x above the median, "
                "and the log axis exposes three distinct customer populations that an "
                "average would hide entirely."
            ),
            filename=config.CHART_FILES[3].name,
            chart_type="Histogram",
            rationale=(
                "The question is about **spread**, not comparison, so the mark is a "
                "histogram. The value axis is logarithmic because the range spans more "
                "than 5,000x; on a linear axis every customer below $50K collapses into "
                "one bar and the shape disappears. Statistics come from "
                "`analyze_revenue_distribution.analyze_revenue()`."
            ),
            key="chart3",
        )

    with tabs[3]:
        components.chart_block(
            charts.build_revenue_composition(pivot, segment_metrics),
            insight=(
                f"The {top_segment} segment is "
                f"{segment_metrics['revenue_contribution'].max():.1f}% of revenue from "
                f"just {int(segment_metrics.loc[top_segment, 'customer_count'])} customers. "
                "Within every segment the Enterprise product tier is the largest slice."
            ),
            filename=config.CHART_FILES[4].name,
            chart_type="Stacked bar chart",
            rationale=(
                "This is a **part-to-whole** relationship: total bar height gives the "
                "segment total while the stacks give the composition, so both read at "
                "once. Three products stay well inside the five-segment limit beyond "
                "which stacks become unreadable."
            ),
            key="chart4",
        )

    with tabs[4]:
        figure, correlation = charts.build_tickets_vs_value(customers)
        components.chart_block(
            figure,
            insight=(
                f"Pearson r = {correlation['pearson']:.2f}, Spearman rho = "
                f"{correlation['spearman']:.2f}. Ticket volume rises with customer "
                "value, which reframes support cost as a function of account size "
                "rather than a symptom of dissatisfaction. Association only, not causation."
            ),
            filename=config.CHART_FILES[5].name,
            chart_type="Scatter plot",
            rationale=(
                "Two continuous measures per observation makes this a **correlation** "
                "question, and a scatter plot is the only chart that shows every point, "
                "its clusters, and its outliers at once. Ticket counts are integers, so "
                "the points carry a small horizontal jitter to reveal density."
            ),
            key="chart5",
        )

    st.divider()
    with st.expander("Design system: palette, labelling, and accessibility"):
        components.palette_swatches()
        st.markdown(
            """
Every chart on this page carries a title stating the finding, both axes
labelled with units, a legend wherever more than one series is drawn, readable
data labels, and at least one annotation or reference line.

Colour never carries meaning alone. Product tier uses a light-to-dark
sequential ramp, so luminance separates the tiers in greyscale. Customer
segment adds a distinct marker shape per segment. Categorical colours come
from the Okabe-Ito set, which stays distinguishable under all common forms of
colour vision deficiency.

Currency labels scale to the value: `$7.3K` for product revenue, `$253.7K` for
customer value. A fixed divide-by-a-million would label every product tick
`$0.0M`.
            """
        )
        if config.CHARTS_README.exists():
            st.caption(f"Full chart documentation: `output/{config.CHARTS_README.name}`")


render()
