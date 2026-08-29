"""Page: the churn narrative, with its evidence attached.

Named 4_Churn_Story rather than 4_Insights because a 4_insights.py stub already
exists and macOS filesystems are case-insensitive; the two names would collide.

Reached through ``src/dashboard/app.py``, which puts the project root on
sys.path before this module is imported.
"""

import streamlit as st

from src.dashboard import charts, components, config, data_loader, narrative, theme


def render():
    """Draw the whole page."""
    components.page_header(
        "Why Our Customers Leave",
        "The churn story, in business language, with the evidence behind it.",
        question="Which customers are we losing, and what change would keep the most of them?",
    )

    try:
        evidence = narrative.build_evidence()
    except data_loader.MissingArtifactError as error:
        components.missing_artifact_warning(error)
        return

    e = evidence
    segments = e["segments"]

    components.kpi_row(
        [
            {
                "label": "Customer book",
                "value": theme.fmt_currency(e["book_value"]),
                "help": "Total lifetime value of every customer on file.",
            },
            {
                "label": "Lost to churn each year",
                "value": theme.fmt_currency(e["value_at_risk"]),
                "delta": f"{e['value_at_risk'] / e['book_value']:.1%} of the book",
                "delta_color": "off",
            },
            {
                "label": "Recoverable to target",
                "value": theme.fmt_currency(e["recoverable_total"]),
                "delta": f"if all segments reach {e['target']:.0%}",
                "delta_color": "off",
            },
            {
                "label": "Concentrated in",
                "value": e["leader"],
                "delta": f"{e['leader_share']:.0%} of the opportunity",
                "delta_color": "off",
            },
        ]
    )

    st.divider()

    st.subheader("The story")
    st.markdown(
        theme.md_safe(f"""
We hold **{e['total_customers']:,} customers** worth
**{theme.fmt_currency(e['book_value'])}** in lifetime value, and churn takes
**{theme.fmt_currency(e['value_at_risk'])}** of that away every year. An earlier
look at the data pointed at support contact as the cause. **That answer was
wrong**, and acting on it would have cost us money.

Support tickets do not drive churn. Our largest customers file the most tickets
*and* stay longest, so pooling everyone together makes contact look protective.
Compare like with like and the link vanishes. Ticket volume is a symptom of how
large a customer is, not a cause of whether they stay.

The money is concentrated. **{e['leader']} holds
{e['leader_share']:.0%}** of everything we could recover -
**{theme.fmt_currency(e['leader_recoverable'])}** of
{theme.fmt_currency(e['recoverable_total'])} - from
{e['leader_customers']} customers.
        """)
    )

    st.divider()

    st.subheader("The evidence")
    tabs = st.tabs(
        [
            "Who is leaving",
            "Why tickets are a red herring",
            "Where the money is",
        ]
    )

    with tabs[0]:
        components.chart_block(
            charts.build_churn_by_segment(segments, e["target"]),
            insight=(
                f"{len(e['over_target'])} of {e['segment_count']} segments sit "
                f"meaningfully above the {e['target']:.0%} target. But exposure "
                f"does not follow the rate: {segments['value_at_risk'].idxmax()} "
                f"carries the most money at risk "
                f"({theme.fmt_currency(segments['value_at_risk'].max())}), and "
                f"Enterprise carries "
                f"{theme.fmt_currency(segments.loc['Enterprise', 'value_at_risk'])} "
                f"on our best rate."
            ),
            filename=config.NARRATIVE_CHARTS["churn_by_segment"].name,
            chart_type="Paired bar chart",
            rationale=(
                "Two panels on one x-axis because the point is the mismatch "
                "between them. Rate and exposure rank the segments differently, "
                "and stacking the panels makes that visible in one glance."
            ),
            key="narr1",
        )

    with tabs[1]:
        components.chart_block(
            charts.build_ticket_paradox(
                e["pooled_r"], e["within_r"], e["small_sample_r"], e["small_sample_n"]
            ),
            insight=(
                f"Pooled across all {e['total_customers']:,} customers, tickets "
                f"and churn move together at {e['pooled_r']:+.2f}, which looks "
                "protective. Within any single segment the strongest figure is "
                f"{e['within_max_abs']:.2f} - nothing. Segment was driving both "
                "measures all along."
            ),
            filename=config.NARRATIVE_CHARTS["paradox"].name,
            chart_type="Grouped bar chart",
            rationale=(
                "The comparison is the message, so pooled and per-segment sit on "
                "one axis with a shaded band marking the range in which a figure "
                "means nothing. The reversal is visible without reading a number."
            ),
            key="narr2",
        )

    with tabs[2]:
        components.chart_block(
            charts.build_opportunity(segments),
            insight=(
                f"{e['leader']} accounts for "
                f"{theme.fmt_currency(e['leader_recoverable'])} of the "
                f"{theme.fmt_currency(e['recoverable_total'])} available. "
                f"{e['worst_rate_segment']} has the worst rate but its customers "
                f"are worth "
                f"{theme.fmt_currency(segments.loc[e['worst_rate_segment'], 'avg_value'])} "
                "each, so chasing the worst percentage sends the team to the "
                "smallest prize."
            ),
            filename=config.NARRATIVE_CHARTS["opportunity"].name,
            chart_type="Horizontal bar chart",
            rationale=(
                "Ranking a single measure across four named categories, so bar "
                "length carries it. Horizontal because the labels are words."
            ),
            key="narr3",
        )

    st.divider()

    st.subheader("What we recommend")
    smb = segments.loc[e["leader"]]
    ent = segments.loc["Enterprise"]
    recommendations = [
        {
            "title": f"Put retention effort into {e['leader']}, not everywhere",
            "why": f"It is {e['leader_share']:.0%} of the recoverable money.",
            "impact": (
                f"Bringing {smb['churn_rate']:.1%} down to {e['target']:.0%} "
                f"returns {theme.fmt_currency(e['leader_recoverable'])} a year."
            ),
            "owner": "Head of Customer Success",
            "when": "Within two quarters",
        },
        {
            "title": "Protect Enterprise even though its rate looks healthy",
            "why": (
                f"One account is worth {theme.fmt_currency(ent['avg_value'])}, "
                "more than a year of Individual churn."
            ),
            "impact": (
                f"{theme.fmt_currency(ent['value_at_risk'])} of exposure covered "
                f"by named ownership across {int(ent['customers'])} accounts."
            ),
            "owner": "Head of Sales",
            "when": "This quarter",
        },
        {
            "title": (
                f"Concentrate on the first "
                f"{e['tenure']['newest_cutoff_months']:.0f} months"
            ),
            "why": (
                f"The newest quarter of customers churns at "
                f"{e['tenure']['newest_churn']:.1%} against "
                f"{e['tenure']['oldest_churn']:.1%} for the most established."
            ),
            "impact": "Closing half the gap moves roughly 60 customers a year.",
            "owner": "Head of Customer Success",
            "when": "Programme live next quarter",
        },
        {
            "title": "Stop treating ticket volume as a churn warning",
            "why": "The signal we assumed was there is not, and start recording response times.",
            "impact": (
                "Prevents a support-reduction campaign that would have "
                "suppressed contact from our most valuable accounts."
            ),
            "owner": "Head of Support",
            "when": "Logging in place within one quarter",
        },
    ]

    for index, item in enumerate(recommendations, start=1):
        with st.container(border=True):
            st.markdown(f"**{index}. {item['title']}**")
            left, right = st.columns([3, 1])
            left.markdown(
                theme.md_safe(f"{item['why']}  \n**Impact:** {item['impact']}")
            )
            right.markdown(
                f"**Owner**  \n{item['owner']}  \n\n**When**  \n{item['when']}"
            )

    st.divider()
    with st.expander("What we could not answer"):
        st.markdown(
            theme.md_safe(f"""
**No support response times.** No file in this project records when a ticket was
answered, only how many were raised. "Does answering faster keep customers?" is
a good question and we cannot currently answer it. That is why recording
response times is a recommendation rather than a finding.

**Churn has no history.** We hold one churn figure per customer, not a
month-by-month series, so segments can be compared against each other and
against target, but not this quarter against last.

**The figures come from generated data.** This runs on the project's synthetic
customer dataset. The method and the reasoning are real; the customers are not.

**A smaller file disagrees.** `data/raw/correlation_data.csv` holds
{e['small_sample_n']} rows and reports {e['small_sample_r']:+.2f} for tickets
against churn - the opposite sign. {e['small_sample_n']} rows cannot carry a
decision of this size.
            """)
        )
        if config.CHURN_NARRATIVE.exists():
            st.caption(f"Full written narrative: `docs/{config.CHURN_NARRATIVE.name}`")


render()
