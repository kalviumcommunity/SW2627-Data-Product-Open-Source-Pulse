# KPI Lineage

Where every number on the executive summary comes from, how its comparison
period is chosen, and how it was checked.

Regenerate with `python scripts/build_kpis.py`. The build recomputes every KPI
in both SQL and pandas and fails if they disagree, so this document cannot
drift from the dashboard.

## Current values

| Metric | Key | Value | Change | Status | Direction |
|---|---|---|---|---|---|
| Revenue | `revenue` | $170.3K | +4.4% | ↑ on track | higher is better |
| Transactions | `transactions` | 8,421 | +10.9% | ↑ on track | higher is better |
| Avg order value | `avg_order_value` | $20.22 | -5.9% | ↓ off track | higher is better |
| New signups | `signups` | 1,683 | +16.6% | ↑ on track | higher is better |
| Churn rate | `churn_rate` | 12.4% | +24.3% vs target | ↑ off track | lower is better |

## Reporting window

| | |
|---|---|
| Current period | 2026-08 (03 Aug to 25 Aug 2026) |
| Prior period | 2026-07 (01 Jul to 23 Jul 2026) |
| Window length | 17 business days each |
| Prior month total | 23 business days |

### Why the prior month is truncated

The newest month in the data is partial, holding 17 of the
23 business days a full month carries here. Comparing it against a
complete prior month would compare 17 days of trading against
23, and every additive metric would appear to collapse.

Both windows are therefore cut to the same 17 days. The
difference this makes is not cosmetic:

| Comparison | Revenue change | Reads as |
|---|---|---|
| Matched windows, 17 days each | **+4.4%** | growing |
| Naive, 17 days against the full 23-day prior month | -35.7% | collapsing |

The naive form reports roughly a third of the revenue disappearing when trading
is in fact growing. It compares 17 days of takings against
23, and the gap is arithmetic, not business. Shipping that number turns a
KPI row into a false alarm, and it is the single most common way a KPI row
loses its credibility.

## Metric definitions

### Revenue

- **Business question:** Are we bringing in more money than last period?
- **Source:** `vw_kpi_summary -> vw_kpi_period_totals -> daily_metrics`
- **Comparison:** against the matched window of the prior month
- **Direction:** higher is better
- **Validation:** computed in SQL through the views and again in pandas; the
  build fails if the two differ by more than 1e-06 relative.

### Transactions

- **Business question:** Are customers buying more often?
- **Source:** `vw_kpi_summary -> vw_kpi_period_totals -> daily_metrics`
- **Comparison:** against the matched window of the prior month
- **Direction:** higher is better
- **Validation:** computed in SQL through the views and again in pandas; the
  build fails if the two differ by more than 1e-06 relative.

### Avg order value

- **Business question:** Is each purchase getting larger or smaller?
- **Source:** `vw_kpi_summary, revenue / transactions over the matched window`
- **Comparison:** against the matched window of the prior month
- **Direction:** higher is better
- **Validation:** computed in SQL through the views and again in pandas; the
  build fails if the two differ by more than 1e-06 relative.

### New signups

- **Business question:** Is the top of the funnel growing?
- **Source:** `vw_kpi_summary -> vw_kpi_period_totals -> daily_metrics`
- **Comparison:** against the matched window of the prior month
- **Direction:** higher is better
- **Validation:** computed in SQL through the views and again in pandas; the
  build fails if the two differ by more than 1e-06 relative.

### Churn rate

- **Business question:** Are we keeping the customers we win?
- **Source:** `vw_churn_kpi -> customer_segments`
- **Comparison:** against the retention target of 10%
- **Direction:** lower is better, so the colour is inverted
- **Validation:** computed in SQL through the views and again in pandas; the
  build fails if the two differ by more than 1e-06 relative.

## Notes on sourcing

**Views, not tables.** The dashboard reads `vw_kpi_summary` and `vw_churn_kpi`.
Changing a metric definition means editing `sql/analytics/kpi_views.sql` once;
no consumer changes.

**No hard-coded dates.** `vw_kpi_periods` derives the current month from
`MAX(month)` in the data and the prior month by SQL date arithmetic. A newer
extract moves the window forward on its own.

**No hard-coded values.** Every figure on the card comes from the views. The
only constants are the retention target (10%, the threshold
`analyze_segments.py` already uses to flag a segment) and the
2% band inside which a change reads as flat.

**Two synthetic sources.** The four period metrics come from
`daily_metrics.csv` and churn from `customer_segment_data.csv`. These are
separate generated datasets that do not describe the same customers. In
production all five would come from one warehouse; the join is safe here only
because each KPI is reported independently.

**Churn has no date column** anywhere in this project, so it cannot be compared
period over period. Rather than invent a history, it is compared against the
retention target, which the lesson's own KPI criteria allow: a KPI must be
comparable to "last period, last year, or a target".

**Customer satisfaction is absent.** No rating, score, or NPS column exists in
any raw or processed file. It is not on the card row, because a KPI with no
underlying measurement is a decoration.
