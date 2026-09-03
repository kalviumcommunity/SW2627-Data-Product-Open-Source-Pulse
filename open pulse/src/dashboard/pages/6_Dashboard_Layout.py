"""Page: four-level information hierarchy demonstrated on real data.

Level 1 (Status)    - five KPI cards, current value + change + trend arrow
Level 2 (Trend)     - the trend behind each status
Level 3 (Segments)  - where revenue and risk sit by segment
Level 4 (Detail)    - filters, a data table, and an export

The hierarchy is progressive disclosure: a glance answers "are we on
track?", and only a deliberate interaction reveals the rows underneath a
status. Colour is never the only carrier of meaning - every KPI pairs its
colour with an arrow and a written word.

Reached through ``src/dashboard/app.py``.
"""

import pandas as pd
import streamlit as st

from src.dashboard import components, data_loader, kpi, layout_charts, theme


def render():
    """Draw the whole page."""
    components.page_header(
        "Dashboard Layout",
        "Four levels of information: status, trend, segment, detail.",
        question="Are we on track, and where does the answer come from?",
    )

    try:
        values, context, source = data_loader.load_kpi_values()
        daily = data_loader.load_daily_metrics()
        customers = data_loader.load_customer_segment_data()
    except data_loader.MissingArtifactError as error:
        components.missing_artifact_warning(error)
        return

    table = kpi.build_kpi_table(values)

    # ------------------------------------------------------------------ LEVEL 1
    st.subheader("Level 1 - Status: are we on track?")
    components.kpi_cards(table)
    st.caption(
        f"Current period: {context['current_month']} (first "
        f"{context['window_days']} business days) against the matched window of "
        f"{context['prior_month']}. Source: {source}."
    )
    st.caption(
        "The five metrics answer five different questions - revenue growth, "
        "purchase frequency, basket size, the top of the funnel, and retention. "
        "A direction arrow and a written word pair with every colour, so the "
        "message survives greyscale and colour-vision deficiency."
    )
    st.divider()

    # ------------------------------------------------------------------ LEVEL 2
    st.subheader("Level 2 - Trend: what is behind the numbers")
    col_a, col_b = st.columns(2)
    with col_a:
        components.plotly_block(
            layout_charts.build_revenue_trend(daily),
            insight=(
                f"Daily revenue runs to {theme.fmt_currency(daily['daily_revenue'].max())} "
                f"with a period average of {theme.fmt_currency(daily['daily_revenue'].mean())}. "
                "The dashed success line is the period average, not a business target, "
                "so it moves with a fresh extract."
            ),
            filename="layout_revenue_trend",
            key="layout_rev_trend",
        )
    with col_b:
        components.plotly_block(
            layout_charts.build_transactions_trend(daily),
            insight=(
                "The bars swing week to week; the blue 7-day average is the signal "
                "to read off it. Transactions underpin every revenue figure, so "
                "watching volume alongside value separates a basket-driven change "
                "from a traffic-driven one."
            ),
            filename="layout_transactions_trend",
            key="layout_txn_trend",
        )

    if not table.empty:
        revenue_change = table.loc[table["Key"] == "revenue", "Change_Pct"].iloc[0]
        txn_change = table.loc[table["Key"] == "transactions", "Change_Pct"].iloc[0]
        aov_change = table.loc[table["Key"] == "avg_order_value", "Change_Pct"].iloc[0]
        st.info(
            f"Revenue is {revenue_change:+.1f}%, transactions {txn_change:+.1f}%, "
            f"average order value {aov_change:+.1f}%. Where the two diverge, ask "
            "whether the growth is volume-led or value-led.",
            icon=":material/lightbulb:",
        )
    st.divider()

    # ------------------------------------------------------------------ LEVEL 3
    st.subheader("Level 3 - Segments: where revenue and risk sit")
    col_c, col_d = st.columns(2)
    with col_c:
        components.plotly_block(
            layout_charts.build_segment_revenue(customers),
            insight=(
                "Segment lifetime values show which customer group carries the "
                "book. The segment with the largest revenue is the one worth "
                "protecting first."
            ),
            filename="layout_segment_revenue",
            key="layout_seg_rev",
        )
    with col_d:
        components.plotly_block(
            layout_charts.build_segment_risk(customers),
            insight=(
                f"Segments above the {kpi.CHURN_TARGET:.0%} retention target are "
                "revenue at risk. The danger reference line makes the threshold "
                "readable at a glance; any bar crossing it is a retention target."
            ),
            filename="layout_segment_risk",
            key="layout_seg_risk",
        )

    segment_metrics = (
        customers.groupby("customer_type")
        .agg(
            customers=("customer_id", "count"),
            revenue=("lifetime_value", "sum"),
            churn=("churn", "mean"),
        )
        .sort_values("revenue", ascending=False)
    )
    display = segment_metrics.copy()
    display["revenue"] = display["revenue"].map(theme.fmt_currency)
    display["churn"] = display["churn"].map("{:.1%}".format)
    display.columns = ["Customers", "Lifetime value", "Churn rate"]
    st.dataframe(display, width="stretch", hide_index=True)
    st.divider()

    # ------------------------------------------------------------------ LEVEL 4
    st.subheader("Level 4 - Detail: drill down and export")
    st.caption(
        "Progressive disclosure: the summary above answers the question at a "
        "glance; only a deliberate filter below reveals the individual rows "
        "underneath a status."
    )

    with st.sidebar:
        st.header("Filters")
        segment_choices = ["All"] + sorted(customers["customer_type"].unique().tolist())
        selected_segment = st.selectbox("Customer segment", segment_choices)
        tier_choices = ["All"] + sorted(customers["product_tier"].unique().tolist())
        selected_tier = st.selectbox("Product tier", tier_choices)
        min_retention = st.slider(
            "Min retention (days)", 0, int(customers["retention_days"].max()), 0
        )

    detail = customers.copy()
    if selected_segment != "All":
        detail = detail[detail["customer_type"] == selected_segment]
    if selected_tier != "All":
        detail = detail[detail["product_tier"] == selected_tier]
    if min_retention > 0:
        detail = detail[detail["retention_days"] >= min_retention]

    st.caption(f"Showing {len(detail):,} of {len(customers):,} customers")
    st.dataframe(
        detail[
            [
                "customer_id",
                "customer_type",
                "region",
                "product_tier",
                "lifetime_value",
                "churn",
                "support_tickets",
                "retention_days",
            ]
        ],
        width="stretch",
        hide_index=True,
        height=320,
    )

    st.download_button(
        "Download filtered data (CSV)",
        data=detail.to_csv(index=False).encode("utf-8"),
        file_name="filtered_customers.csv",
        mime="text/csv",
        key="download_filtered",
    )

    with st.expander("Why this hierarchy"):
        st.markdown(
            f"""
The page follows the four-level information hierarchy:

| Level | Content | Question answered |
|---|---|---|
| 1. Status | Five KPI cards | *Are we on track?* |
| 2. Trend | Two time-series charts | *What is behind the status?* |
| 3. Segments | Two comparison charts + table | *Where does revenue and risk sit?* |
| 4. Detail | Filters, table, export | *Which rows explain it?* |

Design principles applied:

1. **Progressive disclosure** - the summary is visible immediately; detail is
   behind a deliberate filter interaction.
2. **Spatial organisation** - the most important question (status) sits first,
   top-left, before any chart.
3. **Consistent metaphor** - green means on track, red means off track, amber
   means flat, across every element. Colour is never the only carrier of the
   message; an arrow and a word pair with it.
4. **Context over numbers** - every metric compares against a prior period or
   a target rather than standing alone.

Palette lives in `theme.py` and is shared by every chart on every page, so a
colour means the same thing no matter where the reader is.
            """
        )
        if st.button("Reset my filters"):
            st.session_state.clear()
            st.rerun()


render()
