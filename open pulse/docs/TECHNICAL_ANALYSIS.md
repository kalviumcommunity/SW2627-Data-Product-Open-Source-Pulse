# Technical Analysis

*Appendix to [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md). Optional reading.
The summary stands on its own; this document exists so the work can be checked
and reproduced.*

---

## 1. Data source and scope

| | |
|---|---|
| Dataset | `output/customer_segment_data.csv` |
| Records | 1,000 customers, one row each |
| Fields used | segment, region, product tier, lifetime value, support ticket count, retention days, churn |
| Produced by | `src/analytics/segment_analysis.py` (`generate_customer_data`, seed 42) |
| Analysis code | `src/dashboard/narrative.py` |

**This is generated data.** The method and the reasoning are real; the customers
are not. Every figure reproduces exactly because the generator is seeded.

## 2. Segment economics

| Segment | Customers | Churn | Avg value | Book value | At risk / yr | Avg tickets | Avg tenure (days) |
|---|---|---|---|---|---|---|---|
| SMB | 397.0 | 13.12% | $8,140 | $3,231,650 | $423,906 | 6.2 | 403 |
| Enterprise | 53.0 | 2.96% | $144,800 | $7,674,387 | $227,292 | 11.6 | 929 |
| Startup | 353.0 | 10.02% | $3,102 | $1,095,119 | $109,780 | 3.0 | 255 |
| Individual | 197.0 | 17.91% | $474 | $93,423 | $16,732 | 2.9 | 121 |

Book value is customers x average lifetime value. Value at risk is book value x
churn rate, i.e. the annual expected loss at current rates.

- Total book value: **$12,094,579**
- Total value at risk: **$777,710**
- Blended churn rate: **6.43%**

## 3. Two benchmarks, and why the second is used

The published retention target is 10%. The blended rate is already
6.43%, below it, so a target-based benchmark measures only the
segments individually in breach and returns
**$108,399**. That understates the case.

The executive summary uses a best-in-class benchmark instead: what returns if the
weaker segments matched Enterprise, which achieves 2.96%
inside this same business.

| Segment | Current | Benchmark | Recoverable |
|---|---|---|---|
| SMB | 13.12% | 2.96% | $328,195 |
| Startup | 10.02% | 2.96% | $77,346 |
| Individual | 17.91% | 2.96% | $13,965 |

Total: **$419,505 per year**, of which
78% is SMB.

This is a benchmark, not a forecast. It states the size of the prize if a known
standard is met, and it is the basis for the investment ceiling quoted in the
summary. No cost data exists in this project, so the summary gives leadership a
ceiling rather than a price.

## 4. Association analysis

Association of each measure with churn across all 1,000
customers:

| Measure | Association with churn |
|---|---|
| `retention_days` | -0.478 |
| `lifetime_value` | -0.460 |
| `support_tickets` | -0.214 |

### The support-ticket reversal

Pooled across everyone, support tickets and churn move together at
**-0.214**, which reads as though contacting support protects
customers. Within each segment:

| Segment | Association with churn |
|---|---|
| SMB | +0.038 |
| Startup | +0.056 |
| Individual | +0.106 |
| Enterprise | -0.059 |

The strongest within-segment figure is 0.106. The pooled
result is produced entirely by segment membership: Enterprise customers
file 11.6 tickets on average and
churn at 3.0%, while Individual
customers file 2.9 and churn at
17.9%. Ticket volume is a proxy for
account size.

For contrast, `data/raw/correlation_data.csv` — the 20-row
file behind `scripts/analyze_correlations.py` — reports
**+0.81** for the same pair, the opposite sign. That file is
too small to support a decision.

## 5. Tenure

| Group | Churn | Average tenure |
|---|---|---|
| Newest quarter of customers | 15.62% | 119 days |
| Longest-standing quarter | 10.72% | 577 days |

Tenure is the strongest single association with churn in the dataset at
-0.478. The relationship is partly definitional —
a customer who churns early cannot accumulate tenure — so it is reported as the
highest-leverage moment to intervene, not as a lever in itself.

## 6. Traceability

| Finding | Risk | Recommendation | How it helps |
|---|---|---|---|
| SMB churns at 13.1% vs 3.0% in Enterprise | $328,195/yr, 78% of all recoverable value | Fund a SMB retention programme | Closing the gap to 3.0% returns $328,195 a year |
| Enterprise holds $144,800 per account | $227,292/yr exposure despite the best rate | Named owner for every Enterprise account | Two lost accounts cost more than fixing our worst-rate segment entirely |
| Newest customers churn at 15.6% vs 10.7% for the longest-standing | Every new customer enters at the highest-risk moment | Rebuild the first 6 months | Removes a 4.9% excess at the point of greatest leverage |
| Support contact and churn move together across the whole base (-0.21) but not inside any segment (max 0.11) | A support-reduction campaign would have cost money and changed nothing | Retire ticket volume as a churn signal; record response times | Prevents a wrong intervention and unblocks the question we cannot answer |

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
fails if the text drifts outside 300-400 words, contains
any of the 20 blocklisted technical terms, or hedges.
