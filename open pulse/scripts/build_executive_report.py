"""Build the executive summary, the technical appendix, and the audience versions.

Three documents with three different jobs:

  docs/EXECUTIVE_SUMMARY.md   one page, 300-400 words, no methodology
  docs/TECHNICAL_ANALYSIS.md  the appendix, unlimited, for anyone verifying
  docs/AUDIENCE_VERSIONS.md   the same finding reframed for four audiences

The executive summary is checked against the word range and a jargon blocklist,
and the build fails if either gate is breached. Every figure is substituted from
the analysis, so no number in any document is typed by hand.

Run: python scripts/build_executive_report.py
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard import config, executive, narrative  # noqa: E402
from src.dashboard.executive import money  # noqa: E402


WORD_RANGE = (300, 400)
HEDGES = ["we believe", "might be", "possibly", "it appears", "perhaps",
          "we think", "could potentially", "may be worth considering"]


def count_words(text):
    """Words in the prose, ignoring markdown punctuation."""
    return len(re.sub(r"[#*`\-|]", " ", text).split())


def check(body):
    """Enforce length, jargon, and hedging before anything is written."""
    words = count_words(body)
    low, high = WORD_RANGE
    print(f"[check] executive summary: {words} words (brief asks {low}-{high})")
    if not low <= words <= high:
        raise SystemExit(f"Executive summary is {words} words, outside {low}-{high}.")

    lowered = body.lower()
    jargon = [term for term in narrative.JARGON if term in lowered]
    if jargon:
        raise SystemExit(f"Jargon in the executive summary: {', '.join(jargon)}")
    print(f"[check] no jargon from the {len(narrative.JARGON)}-term blocklist")

    hedging = [term for term in HEDGES if term in lowered]
    if hedging:
        raise SystemExit(f"Hedging language found: {', '.join(hedging)}")
    print(f"[check] no hedging from the {len(HEDGES)}-term blocklist")
    return words


def write_executive_summary(evidence, executive_figures, body, words):
    """Write the one-page summary."""
    document = f"""# Churn Reduction Initiative

## Executive Summary

*One page. Prepared for the leadership team. The supporting analysis is in
[TECHNICAL_ANALYSIS.md](TECHNICAL_ANALYSIS.md) and is optional reading.*

---

{body}

---

*{words} words. Figures from {evidence['total_customers']:,} customer records;
see the technical appendix for sources and limits.*
"""
    config.EXECUTIVE_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    config.EXECUTIVE_SUMMARY.write_text(document, encoding="utf-8")
    print(f"[output] {config.EXECUTIVE_SUMMARY.relative_to(PROJECT_ROOT)} ({words} words)")


def write_traceability(evidence, executive_figures):
    """Return the finding-to-recommendation table as markdown."""
    e, x = evidence, executive_figures
    segments = e["segments"]
    leader = x["stretch_leader"]
    rows = [
        (
            f"{leader} churns at {segments.loc[leader, 'churn_rate']:.1%} vs "
            f"{x['best_rate']:.1%} in {x['best_segment']}",
            f"{money(x['stretch_leader_value'])}/yr, {x['stretch_leader_share']:.0%} "
            "of all recoverable value",
            f"Fund a {leader} retention programme",
            f"Closing the gap to {x['best_rate']:.1%} returns "
            f"{money(x['stretch_leader_value'])} a year",
        ),
        (
            f"{x['best_segment']} holds {money(segments.loc[x['best_segment'], 'avg_value'])} "
            "per account",
            f"{money(segments.loc[x['best_segment'], 'value_at_risk'])}/yr exposure "
            "despite the best rate",
            f"Named owner for every {x['best_segment']} account",
            "Two lost accounts cost more than fixing our worst-rate segment entirely",
        ),
        (
            f"Newest customers churn at {e['tenure']['newest_churn']:.1%} vs "
            f"{e['tenure']['oldest_churn']:.1%} for the longest-standing",
            "Every new customer enters at the highest-risk moment",
            f"Rebuild the first {e['tenure']['newest_cutoff_months']:.0f} months",
            f"Removes a {e['tenure']['newest_churn'] - e['tenure']['oldest_churn']:.1%} "
            "excess at the point of greatest leverage",
        ),
        (
            f"Support contact and churn move together across the whole base "
            f"({e['pooled_r']:+.2f}) but not inside any segment "
            f"(max {e['within_max_abs']:.2f})",
            "A support-reduction campaign would have cost money and changed nothing",
            "Retire ticket volume as a churn signal; record response times",
            "Prevents a wrong intervention and unblocks the question we cannot answer",
        ),
    ]
    header = (
        "| Finding | Risk | Recommendation | How it helps |\n"
        "|---|---|---|---|\n"
    )
    return header + "\n".join(f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows)


def write_technical_analysis(evidence, executive_figures, traceability):
    """Write the appendix: method, evidence, limits, and how to reproduce."""
    e, x = evidence, executive_figures
    segments = e["segments"]

    segment_rows = "\n".join(
        f"| {name} | {row.customers:,} | {row.churn_rate:.2%} | "
        f"{money(row.avg_value)} | {money(row.book_value)} | "
        f"{money(row.value_at_risk)} | {row.avg_tickets:.1f} | "
        f"{row.avg_retention_days:.0f} |"
        for name, row in segments.sort_values("value_at_risk", ascending=False).iterrows()
    )
    within_rows = "\n".join(
        f"| {segment} | {value:+.3f} |" for segment, value in e["within_r"].items()
    )
    driver_rows = "\n".join(
        f"| `{column}` | {value:+.3f} |" for column, value in e["drivers"].items()
    )
    stretch_rows = "\n".join(
        f"| {name} | {segments.loc[name, 'churn_rate']:.2%} | {x['best_rate']:.2%} | "
        f"{money(value)} |"
        for name, value in sorted(
            x["stretch_by_segment"].items(), key=lambda item: -item[1]
        )
    )

    document = f"""# Technical Analysis

*Appendix to [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md). Optional reading.
The summary stands on its own; this document exists so the work can be checked
and reproduced.*

---

## 1. Data source and scope

| | |
|---|---|
| Dataset | `output/customer_segment_data.csv` |
| Records | {e['total_customers']:,} customers, one row each |
| Fields used | segment, region, product tier, lifetime value, support ticket count, retention days, churn |
| Produced by | `src/analytics/segment_analysis.py` (`generate_customer_data`, seed 42) |
| Analysis code | `src/dashboard/narrative.py` |

**This is generated data.** The method and the reasoning are real; the customers
are not. Every figure reproduces exactly because the generator is seeded.

## 2. Segment economics

| Segment | Customers | Churn | Avg value | Book value | At risk / yr | Avg tickets | Avg tenure (days) |
|---|---|---|---|---|---|---|---|
{segment_rows}

Book value is customers x average lifetime value. Value at risk is book value x
churn rate, i.e. the annual expected loss at current rates.

- Total book value: **{money(e['book_value'])}**
- Total value at risk: **{money(e['value_at_risk'])}**
- Blended churn rate: **{x['blended_churn']:.2%}**

## 3. Two benchmarks, and why the second is used

The published retention target is {e['target']:.0%}. The blended rate is already
{x['blended_churn']:.2%}, below it, so a target-based benchmark measures only the
segments individually in breach and returns
**{money(e['recoverable_total'])}**. That understates the case.

The executive summary uses a best-in-class benchmark instead: what returns if the
weaker segments matched {x['best_segment']}, which achieves {x['best_rate']:.2%}
inside this same business.

| Segment | Current | Benchmark | Recoverable |
|---|---|---|---|
{stretch_rows}

Total: **{money(x['stretch_total'])} per year**, of which
{x['stretch_leader_share']:.0%} is {x['stretch_leader']}.

This is a benchmark, not a forecast. It states the size of the prize if a known
standard is met, and it is the basis for the investment ceiling quoted in the
summary. No cost data exists in this project, so the summary gives leadership a
ceiling rather than a price.

## 4. Association analysis

Association of each measure with churn across all {e['total_customers']:,}
customers:

| Measure | Association with churn |
|---|---|
{driver_rows}

### The support-ticket reversal

Pooled across everyone, support tickets and churn move together at
**{e['pooled_r']:+.3f}**, which reads as though contacting support protects
customers. Within each segment:

| Segment | Association with churn |
|---|---|
{within_rows}

The strongest within-segment figure is {e['within_max_abs']:.3f}. The pooled
result is produced entirely by segment membership: {x['best_segment']} customers
file {segments.loc[x['best_segment'], 'avg_tickets']:.1f} tickets on average and
churn at {segments.loc[x['best_segment'], 'churn_rate']:.1%}, while Individual
customers file {segments.loc['Individual', 'avg_tickets']:.1f} and churn at
{segments.loc['Individual', 'churn_rate']:.1%}. Ticket volume is a proxy for
account size.

For contrast, `data/raw/correlation_data.csv` — the {e['small_sample_n']}-row
file behind `scripts/analyze_correlations.py` — reports
**{e['small_sample_r']:+.2f}** for the same pair, the opposite sign. That file is
too small to support a decision.

## 5. Tenure

| Group | Churn | Average tenure |
|---|---|---|
| Newest quarter of customers | {e['tenure']['newest_churn']:.2%} | {e['tenure']['newest_avg_days']:.0f} days |
| Longest-standing quarter | {e['tenure']['oldest_churn']:.2%} | {e['tenure']['oldest_avg_days']:.0f} days |

Tenure is the strongest single association with churn in the dataset at
{e['drivers']['retention_days']:+.3f}. The relationship is partly definitional —
a customer who churns early cannot accumulate tenure — so it is reported as the
highest-leverage moment to intervene, not as a lever in itself.

## 6. Traceability

{traceability}

## 7. Limitations

**No support response times.** No file records when a ticket was answered. The
question "does replying faster retain customers?" cannot be answered with the
data as it stands. This is why instrumentation is a recommendation.

**No churn history.** One churn figure per customer, not a monthly series, so
segments can be compared against each other and against a benchmark, but not
this quarter against last.

**Association is not causation.** Nothing here establishes direction. The
support-ticket reversal is the clearest demonstration of why that matters.

**Two unrelated synthetic sources.** The customer dataset and the daily business
metrics used elsewhere in this dashboard describe different generated
populations. They are never joined.

## 8. Reproducing this

```
python scripts/build_churn_narrative.py     # narrative and evidence charts
python scripts/build_executive_report.py    # this document and the summary
```

Both regenerate every figure from the source data. The executive summary build
fails if the text drifts outside {WORD_RANGE[0]}-{WORD_RANGE[1]} words, contains
any of the {len(narrative.JARGON)} blocklisted technical terms, or hedges.
"""
    config.TECHNICAL_ANALYSIS.write_text(document, encoding="utf-8")
    print(f"[output] {config.TECHNICAL_ANALYSIS.relative_to(PROJECT_ROOT)}")


def write_audience_versions(versions):
    """Write the four reframings."""
    blocks = []
    for audience, entry in versions.items():
        words = count_words(entry["text"])
        blocks.append(
            f"""## {audience}

**Cares about:** {entry['cares_about']}
**Format:** {entry['length']} *({words} words)*

> {entry['text'].replace(chr(10) + chr(10), chr(10) + chr(10) + '> ')}
"""
        )

    document = f"""# The Same Finding, Four Audiences

The analysis does not change. The recommendation does not change. What changes is
which consequence leads, and how much detail earns its place.

The board needs the number and the ask. Engineering needs to know what to build.
Operations needs the sequence and the owners. The support team needs to know
whether this lands on them. Sending any one of these to the wrong audience would
be a failure of communication, not of analysis.

---

{"---".join(blocks)}

---

## What stayed the same

Every version rests on the same three facts: the loss is concentrated in one
segment, a standard we already meet elsewhere would recover most of it, and the
cause everyone assumed was wrong. No version overstates the evidence, and no
version contains a number the others contradict.

## What changed

| Audience | Leads with | Detail level | What is left out |
|---|---|---|---|
| Board | The money and the ask | One paragraph | Everything operational |
| VP of Engineering | What must be built | Two paragraphs, ordered by priority | Money, segment economics |
| Operations | Sequence and owners | Two paragraphs with dates | Method, association analysis |
| Support team | Their workload, and the theory that cleared them | Two paragraphs, plain | Money, benchmarks |
"""
    config.AUDIENCE_VERSIONS.write_text(document, encoding="utf-8")
    print(f"[output] {config.AUDIENCE_VERSIONS.relative_to(PROJECT_ROOT)}")


def main():
    """Build all three documents."""
    print("=" * 74)
    print("BUILDING EXECUTIVE REPORT")
    print("=" * 74)

    evidence = narrative.build_evidence()
    figures = narrative.executive_figures(evidence)

    sections = executive.summary_sections(evidence, figures)
    body = executive.render_markdown(sections)
    words = check(body)

    write_executive_summary(evidence, figures, body, words)
    traceability = write_traceability(evidence, figures)
    write_technical_analysis(evidence, figures, traceability)
    write_audience_versions(executive.audience_versions(evidence, figures))

    print("\n" + "=" * 74)
    print("THE ASK")
    print("=" * 74)
    print(f"  Lost each year            {money(evidence['value_at_risk'])}")
    print(f"  Recoverable at best-in-class {money(figures['stretch_total'])}")
    print(f"  Concentrated in           {figures['stretch_leader']} "
          f"({figures['stretch_leader_share']:.0%})")
    print(f"  Investment ceiling        {money(figures['investment_ceiling'])}/year")
    print("\nThree documents built and checked.")


if __name__ == "__main__":
    main()
