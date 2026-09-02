"""Page: the one-page brief, its risks, and the same finding for four audiences.

Renders the same text as docs/EXECUTIVE_SUMMARY.md, from the same builder, so
the page and the document cannot disagree.

Reached through ``src/dashboard/app.py``, which puts the project root on
sys.path before this module is imported.
"""

import streamlit as st

from src.dashboard import components, config, data_loader, executive, narrative, theme


def render():
    """Draw the whole page."""
    components.page_header(
        "Decision Brief",
        "One page for leadership, plus the same finding rewritten for four audiences.",
        question="What are we approving, and what does it return?",
    )

    try:
        evidence = narrative.build_evidence()
    except data_loader.MissingArtifactError as error:
        components.missing_artifact_warning(error)
        return

    figures = narrative.executive_figures(evidence)
    sections = executive.summary_sections(evidence, figures)
    money = theme.fmt_currency_exec

    components.kpi_row(
        [
            {
                "label": "Lost each year",
                "value": money(evidence["value_at_risk"]),
                "caption": f"{figures['blended_churn']:.1%} of the book",
            },
            {
                "label": "Recoverable",
                "value": money(figures["stretch_total"]),
                "caption": f"at {figures['best_segment']}'s {figures['best_rate']:.1%}",
            },
            {
                "label": "Concentrated in",
                "value": figures["stretch_leader"],
                "caption": f"{figures['stretch_leader_share']:.0%} of the prize",
            },
            {
                "label": "Spend ceiling",
                "value": f"{money(figures['investment_ceiling'])}/yr",
                "caption": "above this, it stops paying",
            },
        ]
    )

    st.divider()

    summary_tab, risk_tab, trace_tab, audience_tab = st.tabs(
        [
            "The one-pager",
            "Risks",
            "Why each recommendation",
            "For a different audience",
        ]
    )

    with summary_tab:
        for heading, content in sections.items():
            st.markdown(f"##### {heading}")
            if isinstance(content, list):
                st.markdown(
                    theme.md_safe("\n".join(f"- {item}" for item in content))
                )
            else:
                st.markdown(theme.md_safe(content))
            st.write("")

        body = executive.render_markdown(sections)
        left, right = st.columns([3, 1])
        left.caption(
            f"{len(body.split())} words. No methodology, no technical terms. "
            "The workings are in the technical appendix."
        )
        right.download_button(
            "Download summary",
            data=config.EXECUTIVE_SUMMARY.read_text(encoding="utf-8")
            if config.EXECUTIVE_SUMMARY.exists()
            else body,
            file_name="EXECUTIVE_SUMMARY.md",
            mime="text/markdown",
            width="stretch",
            key="download_exec",
        )

    with risk_tab:
        st.markdown("Each risk carries a number, because a risk without one is a worry.")
        for risk in narrative.risk_register(evidence, figures):
            with st.container(border=True):
                st.markdown(f"**{risk['name']}**")
                columns = st.columns([2, 2, 2])
                columns[0].markdown(
                    theme.md_safe(f"**What**  \n{risk['what']}")
                )
                columns[1].markdown(
                    theme.md_safe(f"**Why it matters**  \n{risk['matters']}")
                )
                columns[2].markdown(
                    theme.md_safe(f"**Action**  \n{risk['action']}")
                )

    with trace_tab:
        st.markdown(
            "Every recommendation traces back to a finding and forward to a "
            "number. A recommendation that cannot do both is an opinion."
        )
        segments = evidence["segments"]
        leader = figures["stretch_leader"]
        best = figures["best_segment"]
        rows = [
            {
                "Finding": f"{leader} churns at {segments.loc[leader, 'churn_rate']:.1%} "
                           f"vs {figures['best_rate']:.1%} in {best}",
                "Risk": f"{money(figures['stretch_leader_value'])}/yr, "
                        f"{figures['stretch_leader_share']:.0%} of all recoverable value",
                "Recommendation": f"Fund a retention programme for {leader}",
                "How it helps": f"Closing the gap returns "
                                f"{money(figures['stretch_leader_value'])} a year",
            },
            {
                "Finding": f"{best} accounts are worth "
                           f"{money(segments.loc[best, 'avg_value'])} each",
                "Risk": f"{money(segments.loc[best, 'value_at_risk'])}/yr exposure "
                        "despite the best rate",
                "Recommendation": f"Named owner for every {best} account",
                "How it helps": "Two lost accounts cost more than fixing our "
                                "worst-rate segment entirely",
            },
            {
                "Finding": f"Newest customers churn at "
                           f"{evidence['tenure']['newest_churn']:.1%} vs "
                           f"{evidence['tenure']['oldest_churn']:.1%}",
                "Risk": "Every new customer enters at the highest-risk moment",
                "Recommendation": f"Rebuild the first "
                                  f"{evidence['tenure']['newest_cutoff_months']:.0f} months",
                "How it helps": "Acts at the point of greatest leverage",
            },
            {
                "Finding": f"Tickets track churn across the base "
                           f"({evidence['pooled_r']:+.2f}) but not inside any segment "
                           f"(max {evidence['within_max_abs']:.2f})",
                "Risk": "A support-reduction campaign would cost money and change nothing",
                "Recommendation": "Retire ticket volume as a churn signal",
                "How it helps": "Prevents a wrong intervention",
            },
        ]
        st.dataframe(rows, width="stretch", hide_index=True)

    with audience_tab:
        versions = executive.audience_versions(evidence, figures)
        st.markdown(
            "The analysis does not change and neither does the recommendation. "
            "What changes is which consequence leads, and how much detail earns "
            "its place."
        )
        choice = st.radio(
            "Audience",
            list(versions),
            horizontal=True,
            label_visibility="collapsed",
        )
        entry = versions[choice]
        left, right = st.columns([3, 1])
        left.info(theme.md_safe(entry["text"]), icon=":material/record_voice_over:")
        right.markdown(
            theme.md_safe(
                f"**Cares about**  \n{entry['cares_about']}\n\n"
                f"**Format**  \n{entry['length']}\n\n"
                f"**Length**  \n{len(entry['text'].split())} words"
            )
        )

    st.divider()
    with st.expander("Where the numbers come from"):
        st.markdown(
            theme.md_safe(
                f"""
The published retention target is {evidence['target']:.0%}, but our blended rate
is already {figures['blended_churn']:.1%}, below it. Measuring against the target
therefore counts only the segments individually in breach and returns
{money(evidence['recoverable_total'])}, which understates the case.

The brief measures against {figures['best_segment']} instead, which runs at
{figures['best_rate']:.1%} inside this same business. That is a standard the
company has already proven it can reach, and it values the opportunity at
{money(figures['stretch_total'])} a year.

**No cost data exists in this project.** No file records salaries, headcount, or
budget. Rather than invent a price, the brief gives leadership the ceiling: any
programme costing less than {money(figures['investment_ceiling'])} a year is
value-positive, and Finance prices the options against it.
                """
            )
        )
        if config.TECHNICAL_ANALYSIS.exists():
            st.caption(
                f"Full method and limits: `docs/{config.TECHNICAL_ANALYSIS.name}`"
            )


render()
