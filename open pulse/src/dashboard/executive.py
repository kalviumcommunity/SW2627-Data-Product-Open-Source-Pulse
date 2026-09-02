"""The executive summary text, built from the analysis.

Kept separate from the build script so the Streamlit page and the exported
document render the same words. Every figure is substituted from the analysis;
none is typed by hand.
"""

from src.dashboard import narrative, theme


def money(value):
    """Whole dollars, no decimals. Used in the technical appendix."""
    return f"${value:,.0f}"


money_exec = theme.fmt_currency_exec


def summary_sections(evidence, executive):
    """Return the six executive-summary sections as an ordered mapping."""
    e, x = evidence, executive
    segments = e["segments"]
    leader = x["stretch_leader"]
    leader_row = segments.loc[leader]
    best_row = segments.loc[x["best_segment"]]
    risks = narrative.risk_register(e, x)

    return {
        "Situation": (
            f"We lose {money_exec(e['value_at_risk'])} a year to customer churn, "
            f"{x['blended_churn']:.1%} of a {money_exec(e['book_value'])} customer "
            f"book. That loss is not spread evenly, and over half of it is avoidable. "
            f"We examined all {e['total_customers']:,} customers to find where it "
            f"sits and what would stop it."
        ),
        "Key findings": [
            f"**{leader} is the leak.** It loses {leader_row['churn_rate']:.1%} of "
            f"its customers a year against {x['best_rate']:.1%} in "
            f"{x['best_segment']} - {money_exec(x['stretch_leader_value'])} a year, "
            f"{x['stretch_leader_share']:.0%} of everything recoverable.",

            f"**We already know how to fix it.** {x['best_segment']} runs at "
            f"{x['best_rate']:.1%} inside this same business. Bringing our three "
            f"weaker segments to that standard returns "
            f"{money_exec(x['stretch_total'])} a year.",

            f"**The cause we assumed was wrong.** Support contact does not drive "
            f"customers away. Length of relationship does: our newest customers "
            f"leave at {e['tenure']['newest_churn']:.1%}, our longest-standing at "
            f"{e['tenure']['oldest_churn']:.1%}.",
        ],
        "Business risks": [
            f"**{risk['name']}.** {risk['what']} {risk['matters']}"
            for risk in risks
        ],
        "Recommendations": [
            f"**Fund a retention programme for {leader}.** Worth "
            f"{money_exec(x['stretch_leader_value'])} a year, the single largest prize. "
            f"Owner: Head of Customer Success.",

            f"**Give every {x['best_segment']} account a named owner.** "
            f"{money_exec(best_row['value_at_risk'])} sits in "
            f"{int(best_row['customers'])} accounts worth "
            f"{money_exec(best_row['avg_value'])} each. Owner: Head of Sales.",

            f"**Rebuild the first {e['tenure']['newest_cutoff_months']:.0f} months "
            f"of the customer relationship,** where customers leave at "
            f"{e['tenure']['newest_churn']:.1%} against "
            f"{e['tenure']['oldest_churn']:.1%} later on. "
            f"Owner: Head of Customer Success.",
        ],
        "Decision needed": (
            f"Approve scoping of a retention programme for {leader} and confirm a "
            f"budget ceiling. Any programme costing less than "
            f"{money_exec(x['investment_ceiling'])} a year to run pays for itself, "
            f"because that is the full annual prize. We do not yet hold cost data; "
            f"Finance must price the options."
        ),
        "Next steps": [
            "Customer Success returns three costed options for the "
            f"{leader} programme - two weeks.",
            "Finance prices them against the ceiling above - three weeks.",
            f"Sales assigns owners to all {int(best_row['customers'])} "
            f"{x['best_segment']} accounts - this quarter.",
            "Support begins recording response times so the question we could "
            "not answer becomes answerable - this quarter.",
        ],
    }


def render_markdown(sections):
    """Render the sections as the body of the one-page summary."""
    parts = []
    for heading, content in sections.items():
        parts.append(f"### {heading}")
        if isinstance(content, list):
            parts.append("\n".join(f"- {item}" for item in content))
        else:
            parts.append(content)
    return "\n\n".join(parts)


def audience_versions(evidence, executive):
    """The same finding, reframed for four audiences.

    The data does not change and neither does the recommendation. What changes
    is which consequence leads: money for the board, sequencing for operations,
    workload for the support team, and system design for engineering.
    """
    e, x = evidence, executive
    segments = e["segments"]
    leader = x["stretch_leader"]
    leader_row = segments.loc[leader]
    best_row = segments.loc[x["best_segment"]]

    return {
        "Board of Directors": {
            "cares_about": "Shareholder value and strategic risk.",
            "length": "One paragraph. Money only.",
            "text": (
                f"Churn costs {money(e['value_at_risk'])} a year against a "
                f"{money(e['book_value'])} customer book, and "
                f"{money(x['stretch_total'])} of that is recoverable at standards "
                f"we already meet elsewhere in the business. {x['stretch_leader_share']:.0%} "
                f"of the opportunity sits in one segment. Over three years the "
                f"untouched loss is {money(x['three_year_loss'])}. We are asking "
                f"to scope a retention programme against a "
                f"{money(x['investment_ceiling'])} annual ceiling, and to report "
                "back with costed options next quarter."
            ),
        },
        "VP of Engineering": {
            "cares_about": "Feasibility, systems, and what must be built.",
            "length": "Two paragraphs. Implementation detail.",
            "text": (
                f"Three things need building. First, response-time logging in the "
                f"support system: we currently record ticket volume but not when "
                f"anyone replied, which is why we cannot answer whether faster "
                f"replies retain customers. Second, a tenure field on the customer "
                f"record exposed to reporting, so the first "
                f"{e['tenure']['newest_cutoff_months']:.0f} months can be tracked "
                f"as a cohort rather than reconstructed each time. Third, account "
                f"ownership on the {x['best_segment']} records, so the "
                f"{int(best_row['customers'])} highest-value accounts have a named "
                "owner in the system rather than in a spreadsheet.\n\n"
                "None of this is a model or a scoring engine. It is instrumentation. "
                "The analysis we could not complete failed for want of a timestamp, "
                "not for want of technique. Priority order is response-time logging "
                "first, because it unblocks the next analysis; ownership second, "
                "because it is a field and a form; tenure reporting third."
            ),
        },
        "Operations": {
            "cares_about": "Sequencing, owners, and what changes on Monday.",
            "length": "Two paragraphs. Process detail.",
            "text": (
                f"The work concentrates on {leader}, which holds "
                f"{int(leader_row['customers'])} customers churning at "
                f"{leader_row['churn_rate']:.1%}. The programme needs three costed "
                f"options back within two weeks, priced by Finance within three, "
                f"and a decision before the quarter closes. Separately, every one "
                f"of the {int(best_row['customers'])} {x['best_segment']} accounts "
                "needs a named owner recorded this quarter; that is an assignment "
                "exercise, not a project.\n\n"
                f"One process change starts immediately regardless of the funding "
                f"decision: stop treating a rise in support tickets as a churn "
                f"warning. It is not one. Customers who contact us more are, if "
                f"anything, the ones who stay. Escalation rules built on ticket "
                "volume should be retired, and Support should begin logging "
                "response times so the real question can be answered next quarter."
            ),
        },
        "Support team": {
            "cares_about": "Workload, tools, and whether this lands on them.",
            "length": "Two paragraphs. Plain and direct.",
            "text": (
                "The headline first: the analysis cleared you. A theory was going "
                "around that customers leave because they contact support too "
                "often, which would have made your ticket count look like a "
                "problem to be suppressed. Across all "
                f"{e['total_customers']:,} customers that is simply not true. The "
                "customers who talk to you most are among the ones who stay "
                "longest. Nobody is going to ask you to reduce contact.\n\n"
                "What we are asking for is one new habit: record when a ticket was "
                "answered, not just that it arrived. We could not answer whether "
                "replying faster keeps customers, because that timestamp does not "
                "exist anywhere. Once it does, we can find out - and if it turns "
                f"out that speed matters, the case for more hands on the team gets "
                "made with evidence rather than assertion."
            ),
        },
    }
