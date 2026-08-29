"""Page: five KPI cards answering "are we on track?" before any chart.

Follows the information pyramid: status first, then the trend behind the
status, then the segment breakdown, then the detail and its export.

Reached through ``src/dashboard/app.py``, which puts the project root on
sys.path before this module is imported.
"""

import pandas as pd
import streamlit as st

from src.dashboard import components, config, data_loader, interactive, kpi, theme


TREND_COLUMNS = {
    "Revenue": ("daily_revenue", True),
    "Transactions": ("transaction_count", False),
    "New signups": ("signup_rate", False),
}


def render():
    """Draw the whole page."""
    components.page_header(
        "Executive Summary",
        "Five metrics, current period against the matched prior period.",
        question="Are we on track?",
    )

    try:
        values, context, source = data_loader.load_kpi_values()
        daily = data_loader.load_daily_metrics()
        customers = data_loader.load_customer_segment_data()
    except data_loader.MissingArtifactError as error:
        components.missing_artifact_warning(error)
        return

    table = kpi.build_kpi_table(values)

    # ----- Level 1: status -------------------------------------------------
    components.kpi_cards(table)

    off_track = table[table["Status"] == "off track"]
    st.caption(
        f"{context['current_month']} ({context['current_start']:%d %b} to "
        f"{context['current_end']:%d %b %Y}) against the first "
        f"{context['window_days']} business days of {context['prior_month']}. "
        f"Source: {source}."
    )

    if off_track.empty:
        st.success("Every metric is on track.", icon=":material/check_circle:")
    else:
        st.warning(
            "Needs attention: "
            + ", ".join(
                f"**{row.Metric}** ({row.Change_Display})"
                for row in off_track.itertuples()
            ),
            icon=":material/priority_high:",
        )

    with st.expander("The same row using Streamlit's native st.metric"):
        components.kpi_native_metrics(table)
        st.caption(
            "`delta_color=\"inverse\"` gets the churn direction right, so a rising "
            "churn rate shows red. What the native widget cannot express is the "
            "flat state: any change under "
            f"{kpi.FLAT_THRESHOLD_PCT:g}% should read amber rather than green or "
            "red, which is why the cards above are rendered directly."
        )

    st.divider()

    # ----- Level 2: the trend behind the status ----------------------------
    st.subheader("What is behind the numbers")

    choice = st.radio(
        "Metric",
        list(TREND_COLUMNS),
        horizontal=True,
        label_visibility="collapsed",
    )
    column, is_currency = TREND_COLUMNS[choice]
    st.plotly_chart(
        interactive.build_kpi_period_comparison(
            daily, context, column, choice, currency=is_currency
        ),
        width="stretch",
        theme=None,
        config=theme.plotly_config(f"kpi_{column}"),
        key=f"kpi_trend_{column}",
    )

    revenue_change = table.loc[table["Key"] == "revenue", "Change_Pct"].iloc[0]
    txn_change = table.loc[table["Key"] == "transactions", "Change_Pct"].iloc[0]
    aov_change = table.loc[table["Key"] == "avg_order_value", "Change_Pct"].iloc[0]
    st.info(
        f"Transactions are up {txn_change:+.1f}% while average order value is "
        f"{aov_change:+.1f}%, so revenue grows only {revenue_change:+.1f}%. "
        "Growth is coming from volume, not from larger baskets. Worth checking "
        "whether discounting or a shift in product mix is driving the smaller "
        "average order.",
        icon=":material/lightbulb:",
    )

    st.divider()

    # ----- Level 3: segments ----------------------------------------------
    st.subheader("Where churn sits")

    by_segment = (
        customers.groupby("customer_type")
        .agg(
            customers=("customer_id", "count"),
            churn_rate=("churn", "mean"),
            avg_value=("lifetime_value", "mean"),
        )
        .sort_values("churn_rate", ascending=False)
    )
    by_segment["vs_target"] = (
        (by_segment["churn_rate"] - kpi.CHURN_TARGET) / kpi.CHURN_TARGET * 100
    )

    display = pd.DataFrame(
        {
            "Segment": by_segment.index,
            "Customers": by_segment["customers"].map("{:,}".format).values,
            "Churn rate": by_segment["churn_rate"].map("{:.1%}".format).values,
            "vs target": by_segment["vs_target"].map("{:+.0f}%".format).values,
            "Avg lifetime value": by_segment["avg_value"]
            .map(theme.fmt_currency)
            .values,
            # Same flat band the KPI cards use: a segment sitting a fraction of
            # a percent off the target reads "at target", not "over". Without
            # this, Startup shows "+0%" beside the word "over".
            "Status": [
                kpi.get_trend_indicator(
                    deviation, kpi.Direction.LOWER_IS_BETTER
                )["status"].replace("off track", "over target").replace(
                    "on track", "within target"
                ).replace("flat", "at target")
                for deviation in by_segment["vs_target"]
            ],
        }
    )
    st.dataframe(display, width="stretch", hide_index=True)
    over = by_segment[by_segment["vs_target"] > kpi.FLAT_THRESHOLD_PCT]
    st.caption(
        f"The {kpi.CHURN_TARGET:.0%} target is the threshold `analyze_segments.py` "
        f"already uses to flag a segment as high priority. "
        f"{len(over)} of {len(by_segment)} segments sit meaningfully above it, "
        f"holding {over['customers'].sum():,} of {by_segment['customers'].sum():,} "
        f"customers. A segment within {kpi.FLAT_THRESHOLD_PCT:g}% of the target "
        "reads as at target rather than over it."
    )

    st.divider()

    # ----- Level 4: detail and export -------------------------------------
    st.subheader("Detail")
    with st.expander("KPI table and daily source data"):
        st.markdown("**Computed KPIs**")
        st.dataframe(
            table[
                [
                    "Metric",
                    "Value_Display",
                    "Change_Display",
                    "Status",
                    "Basis",
                    "Source",
                ]
            ].rename(
                columns={
                    "Value_Display": "Value",
                    "Change_Display": "Change",
                    "Basis": "Compared to",
                }
            ),
            width="stretch",
            hide_index=True,
        )
        st.download_button(
            "Download KPI summary (CSV)",
            data=table.to_csv(index=False).encode("utf-8"),
            file_name="kpi_summary.csv",
            mime="text/csv",
            key="download_kpis",
        )

        st.markdown("**Daily source metrics**")
        st.dataframe(
            daily.sort_values("date", ascending=False),
            width="stretch",
            hide_index=True,
            height=260,
        )

    with st.expander("Why the prior month is truncated"):
        st.markdown(
            f"""
The newest month in the data is partial: **{context['window_days']} of the
{context['prior_month_total_days']}** business days a full month carries here.
Comparing it against a complete prior month would set
{context['window_days']} days of trading against
{context['prior_month_total_days']}, and every additive metric would appear to
collapse.

Both windows are cut to the same **{context['window_days']} days**. For revenue
this is the difference between:

| Comparison | Revenue change | Reads as |
|---|---|---|
| Matched windows | **{revenue_change:+.1f}%** | growing |
| Naive, against the full prior month | {
    (values['revenue']['current']
     / daily[pd.to_datetime(daily['date']).dt.to_period('M')
             == pd.Period(context['prior_month'])]['daily_revenue'].sum() - 1) * 100:+.1f}% | collapsing |

The naive figure is arithmetic, not business. Shipping it turns the KPI row
into a false alarm.
            """
        )
        if config.KPI_LINEAGE.exists():
            st.caption(f"Full lineage: `output/{config.KPI_LINEAGE.name}`")


render()
