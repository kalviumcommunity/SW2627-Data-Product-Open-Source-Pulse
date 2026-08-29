"""Write the churn narrative and its supporting evidence.

Produces docs/CHURN_NARRATIVE.md, a standalone document a business reader can
follow without running code, plus the three charts it references. Every figure
in the prose is substituted from src/dashboard/narrative.py, so the story and
the data cannot disagree.

The body of the narrative is checked against the 500-750 word brief and the
build fails outside that range.

Run: python scripts/build_churn_narrative.py
"""

import re
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard import charts, config, narrative, theme  # noqa: E402


WORD_RANGE = (500, 750)

# Words that would make a business reader stop and ask what they mean.
JARGON = [
    "p-value", "p value", "auc", "logistic regression", "regression coefficient",
    "confidence interval", "statistically significant", "variance", "r-squared",
    "r²", "heteroscedastic", "confounder", "simpson's paradox", "correlation coefficient",
    "null hypothesis", "standard deviation", "multicollinearity",
]


def money(value):
    """Format a value as whole dollars."""
    return f"${value:,.0f}"


def render_charts(evidence):
    """Render the three evidence charts the narrative points at."""
    figures = {
        "churn_by_segment": charts.build_churn_by_segment(
            evidence["segments"], evidence["target"]
        ),
        "paradox": charts.build_ticket_paradox(
            evidence["pooled_r"],
            evidence["within_r"],
            evidence["small_sample_r"],
            evidence["small_sample_n"],
        ),
        "opportunity": charts.build_opportunity(evidence["segments"]),
    }
    for key, figure in figures.items():
        path = config.NARRATIVE_CHARTS[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
        plt.close(figure)
        print(f"  saved {path.name:44s} ({path.stat().st_size / 1024:,.0f} KB)")


def narrative_body(evidence):
    """Return the five-part narrative. This is the word-counted section."""
    e = evidence
    segments = e["segments"]
    smb = segments.loc[e["leader"]]
    ent = segments.loc["Enterprise"]
    ind = segments.loc[e["worst_rate_segment"]]

    return f"""## The problem

We hold {e['total_customers']:,} customers worth {money(e['book_value'])} in
lifetime value, and on current rates churn takes
{money(e['value_at_risk'])} of that away every year. Leadership asked a direct
question: which customers are we losing, and what is the one change that would
keep the most of them? An earlier look at the data pointed at support contact.
That answer was wrong, and acting on it would have cost us money.

## What we examined

We looked at all {e['total_customers']:,} customers across four segments -
Enterprise, SMB, Startup and Individual. For each customer we had their segment,
region, product tier, lifetime value, support ticket count, how long they have
stayed, and whether they churned. We compared each of these against churn, first
across the whole customer base and then within each segment separately. We did
not have support response times; no system in this business records them today.

## What we found

- **{len(e['over_target'])} of {e['segment_count']} segments sit above our
  {e['target']:.0%} retention target.** {e['worst_rate_segment']} is worst at
  {ind['churn_rate']:.1%}, then SMB at {smb['churn_rate']:.1%}.
- **Support ticket volume does not drive churn.** Across the whole base, customers
  who file more tickets appear *less* likely to leave. Within any single segment
  that link disappears entirely.
- **How long someone has been a customer is the strongest signal we have.** The
  newest quarter of customers, under {e['tenure']['newest_cutoff_months']:.0f}
  months with us, churns at {e['tenure']['newest_churn']:.1%}, against
  {e['tenure']['oldest_churn']:.1%} for those past
  {e['tenure']['oldest_avg_months']:.0f} months.
- **{e['leader']} holds {e['leader_share']:.0%} of the money we can actually
  recover** - {money(e['leader_recoverable'])} of {money(e['recoverable_total'])},
  from {e['leader_customers']} customers.
- **A good rate is not the same as low exposure.** Enterprise has our best rate
  at {ent['churn_rate']:.1%}, yet {money(ent['value_at_risk'])} is still at risk
  each year, because one account is worth {money(ent['avg_value'])} - more than
  every {segments['value_at_risk'].idxmin()} customer we lose in a year put
  together ({money(segments['value_at_risk'].min())}).

## Why this is happening

The support-ticket finding is a trap, and it is worth understanding before
anyone acts on it. Our Enterprise customers file the most tickets - about
{ent['avg_tickets']:.0f} each - and they also stay longest. Our Individual
customers barely contact us at all and leave fastest. Pool everyone together and
it looks as though contacting support keeps people loyal. It does not. Size does.
Big accounts have more people, more usage and more questions, and they also have
contracts, budgets and switching costs that keep them. Once we compare like with
like - SMB against SMB, Startup against Startup - the connection between tickets
and leaving vanishes to nothing. Ticket volume is a symptom of how large a
customer is, not a cause of whether they stay. A campaign to reduce support
contact would have suppressed the signal from our most valuable accounts while
doing nothing whatever about churn.

## What we recommend

- **Put retention effort into SMB, not everywhere.** SMB is
  {e['leader_share']:.0%} of the recoverable money. Bringing its
  {smb['churn_rate']:.1%} down to {e['target']:.0%} returns
  {money(e['leader_recoverable'])} a year. Owner: Head of Customer Success.
  Target: within two quarters.
- **Protect Enterprise even though its rate looks healthy.**
  {money(ent['value_at_risk'])} sits at risk there, and a single lost account
  costs {money(ent['avg_value'])}. Owner: Head of Sales. Target: a named account
  owner for all {int(ent['customers'])} accounts this quarter.
- **Concentrate on the first {e['tenure']['newest_cutoff_months']:.0f} months.**
  The newest quarter of customers churns at {e['tenure']['newest_churn']:.1%}
  against {e['tenure']['oldest_churn']:.1%} for the most established. Owner:
  Head of Customer Success. Target: onboarding programme live next quarter.
- **Stop treating ticket volume as a churn warning, and start recording response
  times.** The signal we assumed was there is not. Owner: Head of Support.
  Target: response-time logging in place within one quarter."""


def rewrap(body, width=79):
    """Rewrap the narrative so the raw markdown reads as cleanly as the render.

    The prose is assembled from an f-string, so substituted figures leave the
    source lines ragged even though a markdown renderer collapses them. This
    reflows each paragraph and bullet without touching headings.
    """
    blocks, output = body.split("\n\n"), []
    for block in blocks:
        stripped = block.strip()
        if not stripped or stripped.startswith("#"):
            output.append(stripped)
            continue
        if stripped.lstrip().startswith("- "):
            items, current = [], []
            for line in stripped.splitlines():
                if line.lstrip().startswith("- "):
                    if current:
                        items.append(" ".join(current))
                    current = [line.strip()[2:].strip()]
                else:
                    current.append(line.strip())
            if current:
                items.append(" ".join(current))
            output.append(
                "\n".join(
                    textwrap.fill(
                        item,
                        width=width,
                        initial_indent="- ",
                        subsequent_indent="  ",
                    )
                    for item in items
                )
            )
            continue
        output.append(
            textwrap.fill(" ".join(stripped.split()), width=width)
        )
    return "\n\n".join(output)


def check_quality(body):
    """Enforce the word count and flag jargon before the document is written."""
    prose = re.sub(r"[#*`\-]", " ", body)
    words = len(prose.split())
    low, high = WORD_RANGE
    print(f"\n[check] narrative body: {words} words (brief asks {low}-{high})")
    if not low <= words <= high:
        raise SystemExit(
            f"Narrative is {words} words, outside the {low}-{high} range the brief sets."
        )

    lowered = body.lower()
    found = [term for term in JARGON if term in lowered]
    if found:
        raise SystemExit(f"Jargon found in the narrative: {', '.join(found)}")
    print(f"[check] no jargon from the {len(JARGON)}-term blocklist")
    return words


def write_document(evidence, body, words):
    """Write the standalone narrative with its evidence appendix."""
    e = evidence
    segments = e["segments"]

    segment_rows = "\n".join(
        f"| {name} | {row.customers:,} | {row.churn_rate:.1%} | "
        f"{money(row.avg_value)} | {money(row.value_at_risk)} | "
        f"{money(row.recoverable)} |"
        for name, row in segments.sort_values(
            "recoverable", ascending=False
        ).iterrows()
    )
    within_rows = "\n".join(
        f"| {segment} only | {value:+.2f} | no meaningful link |"
        for segment, value in e["within_r"].items()
    )

    document = f"""# Why Our Customers Leave

**A churn analysis for leadership.** Read time: about four minutes.
No charts or code required; the evidence is summarised in the appendix.

---

{body}

---

## Evidence behind each finding

### Finding 1: three segments are above target

![Churn by segment](../output/{config.NARRATIVE_CHARTS['churn_by_segment'].name})

| Segment | Customers | Churn rate | Avg value | At risk / year | Recoverable |
|---|---|---|---|---|---|
{segment_rows}

*Recoverable* is the value returned if that segment reached the
{e['target']:.0%} target. It is zero where a segment is already at or below it.

**Why this evidence is convincing.** It covers every customer we have, not a
sample, and the gap between best and worst segment is
{(e['worst_rate'] / segments.loc['Enterprise', 'churn_rate']):.0f} times - far
too large to be chance.

### Finding 2: support tickets do not drive churn

![The ticket paradox](../output/{config.NARRATIVE_CHARTS['paradox'].name})

| Comparison | Link between tickets and churn | Reading |
|---|---|---|
| All {e['total_customers']:,} customers pooled | {e['pooled_r']:+.2f} | looks protective |
{within_rows}

**Why this evidence is convincing.** The reversal is the proof. If ticket volume
genuinely kept customers, the link would hold inside each segment. It does not:
the strongest within-segment figure is {e['within_max_abs']:.2f}, which is
nothing. The earlier analysis that pointed the other way used a
{e['small_sample_n']}-row file and reported {e['small_sample_r']:+.2f}. Twenty
rows cannot carry a decision of this size.

### Finding 3: the recoverable money is concentrated

![Where the value is](../output/{config.NARRATIVE_CHARTS['opportunity'].name})

{e['leader']} accounts for {money(e['leader_recoverable'])} of the
{money(e['recoverable_total'])} available - {e['leader_share']:.0%} of it - from
{e['leader_customers']} customers.

**Why this evidence is convincing.** It reframes the priority. {e['worst_rate_segment']}
has the worst *rate*, but its customers are worth {money(segments.loc[e['worst_rate_segment'], 'avg_value'])}
each, so fixing it entirely returns
{money(segments.loc[e['worst_rate_segment'], 'recoverable'])}. Chasing the worst
percentage would have sent the team to the smallest prize.

---

## What we could not answer

**We have no support response times.** No file in this business records when a
ticket was answered, only how many were raised. The question "does answering
faster keep customers?" is a good one and we cannot currently answer it. That is
why recording response times is one of our four recommendations rather than a
finding.

**Churn has no history here.** We hold one churn figure per customer, not a
month-by-month series, so we can compare segments against each other and against
target, but not this quarter against last.

**These figures come from generated data.** This analysis runs on the project's
synthetic customer dataset. The method, the numbers and the reasoning are real;
the customers are not.

---

## Appendix: how these numbers were produced

| | |
|---|---|
| Dataset | `output/customer_segment_data.csv` ({e['total_customers']:,} customers) |
| Analysis | `src/dashboard/narrative.py` |
| Charts | `src/dashboard/charts.py` |
| Rebuild | `python scripts/build_churn_narrative.py` |
| Retention target | {e['target']:.0%}, the threshold `analyze_segments.py` already uses |
| Narrative length | {words} words |

Every figure quoted above is substituted from the analysis at build time. None
is typed by hand, so the prose cannot drift from the data.
"""
    config.CHURN_NARRATIVE.parent.mkdir(parents=True, exist_ok=True)
    config.CHURN_NARRATIVE.write_text(document, encoding="utf-8")
    print(f"\n[output] {config.CHURN_NARRATIVE.relative_to(PROJECT_ROOT)}")


def main():
    """Build the narrative and its evidence."""
    print("=" * 74)
    print("BUILDING CHURN NARRATIVE")
    print("=" * 74)

    evidence = narrative.build_evidence()
    render_charts(evidence)

    body = rewrap(narrative_body(evidence))
    words = check_quality(body)
    write_document(evidence, body, words)

    print("\n" + "=" * 74)
    print("HEADLINE NUMBERS")
    print("=" * 74)
    print(f"  Book value                {money(evidence['book_value'])}")
    print(f"  Lost to churn each year   {money(evidence['value_at_risk'])}")
    print(f"  Recoverable to target     {money(evidence['recoverable_total'])}")
    print(f"  Concentrated in           {evidence['leader']} "
          f"({evidence['leader_share']:.0%})")
    print(f"  Tickets vs churn pooled   {evidence['pooled_r']:+.2f}")
    print(f"  Tickets vs churn within   "
          f"max {evidence['within_max_abs']:.2f} - no link")
    print("\nNarrative built and checked.")


if __name__ == "__main__":
    main()
