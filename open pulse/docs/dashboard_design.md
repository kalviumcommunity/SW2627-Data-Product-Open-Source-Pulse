# Dashboard Design Documentation

The dashboard layout follows a four-level information hierarchy. This document
records why each level exists, which design principles it applies, and where
the data comes from. The working implementation lives in
`src/dashboard/pages/6_Dashboard_Layout.py`.

## Information Hierarchy Applied

### Level 1 - Status: five KPI cards

Each card shows a metric name, the current value, a period-over-period change,
and a trend arrow. Answering *"are we on track?"* at a glance before any chart
loads.

| Metric | What question it answers | Direction |
|--------|--------------------------|-----------|
| Revenue | Are we bringing in more money than last period? | higher is better |
| Transactions | Are customers buying more often? | higher is better |
| Avg order value | Is each purchase getting larger or smaller? | higher is better |
| New signups | Is the top of the funnel growing? | higher is better |
| Churn rate | Are we keeping the customers we win? | lower is better |

Why these five: they are the smallest set that separates *volume* growth
(transactions, signups) from *value* growth (average order value), with revenue
as the headline and retention guarding the back door. A rising churn rate
renders red precisely because its direction is declared as *lower is better*,
so a "good" number can never accidentally carry a success colour.

### Level 2 - Trends: what is behind the numbers

Two time-series charts sit below the cards:

1. **Daily Revenue Trend** - a line chart with a period-average reference line
   and a peak-day annotation.
2. **Daily Transactions** - bars under a 7-day rolling average, with a mean
   reference line.

Why two: revenue alone cannot say whether growth is price-led or volume-led.
Placing transactions beside revenue lets a reader see the divergence directly.
Each chart has a labelled title, units on both axes, and a reference line so a
number is never read in isolation.

### Level 3 - Segments: where revenue and risk sit

Two comparison charts and a table:

1. **Lifetime Value by Customer Segment** - a horizontal bar chart with value
   labels on every bar.
2. **Churn Rate by Segment vs Retention Target** - bars with a danger-coloured
   target line.

Why a bar chart: segments are discrete categories, and the eye judges
bar length far more accurately than angle or area. The churn chart answers
*which segments are revenue at risk* by making the 10% target a visible line
rather than a footnote.

### Level 4 - Detail: drill-down and export

Filters (segment, product tier, minimum retention) narrow a customer table,
which offers a CSV export. This is the progressive-disclosure step: the
summary answers the question at a glance, and only a deliberate filter
interaction reveals the individual rows underneath a status.

## Design Principles Applied

1. **Progressive Disclosure** - the summary is visible immediately; detail is
   reached through an explicit filter rather than dumped on first load.
2. **Spatial Organisation** - the most important question (status) sits first,
   top-left, before any chart; detail is last.
3. **Consistent Metaphor** - green means on track, red means off track, amber
   means flat, across every element. Colour is never the only carrier of the
   message - every indicator also carries an arrow and a written word, so the
   meaning survives greyscale and colour-vision deficiency.
4. **Context Over Numbers** - every metric compares against a prior period or
   a target rather than standing alone.

## Colour Palette

Defined once in `src/dashboard/theme.py` and shared by every chart on every
page, so a colour means the same thing no matter where the reader is.

| Role | Hex | Usage |
|------|-----|-------|
| Primary | `#1f77b4` | Default single-series fill |
| Secondary | `#ff7f0e` | Second accent series |
| Success | `#2ca02c` | Targets and healthy thresholds |
| Danger | `#d62728` | Alerts, annotation arrows, churn target |
| Neutral | `#7f7f7f` | Reference lines and source notes |

KPI status ramp (separate so a judgement is never reachable by the series
colour cycle): on track `#10b981`, off track `#ef4444`, flat `#f59e0b`.

Customer segments use distinct hues from the Okabe-Ito colour-blind-safe set
with a marker shape per segment: Enterprise `#E69F00`, SMB `#009E73`, Startup
`#CC79A7`, Individual `#D55E00`.

## Target Audience

| Audience | Cadence | What they read |
|----------|---------|----------------|
| Executives / CEO | Weekly glance | Level 1 KPI cards only |
| VP of Sales | Daily | Level 1 + Level 2 trends |
| Analysts | Ad hoc | Level 3 segments + Level 4 filters and export |

The hierarchy serves all three: the glance needs only the top row, the daily
reader adds the trends, and the analyst drills to the detail.

## Data Sources

| Content | Source |
|---------|--------|
| KPI values | `vw_kpi_summary` and `vw_churn_kpi` SQL views over `daily_metrics` and `customer_segments` (or the cross-validated pandas fallback when the database is not built) |
| Trend data | `output/daily_metrics.csv` - `daily_revenue`, `transaction_count` |
| Segment data | `output/customer_segment_data.csv` - `customer_type`, `lifetime_value`, `churn`, `product_tier`, `region`, `retention_days` |

Every number is built from a committed artifact in `output/` or the views
derived from them; no value is hard-coded in the page. Loading a fresher
extract moves the reporting window and every derived figure forward with no
code change.

## Files

| Path | Purpose |
|------|---------|
| `src/dashboard/pages/6_Dashboard_Layout.py` | Page implementing the four levels |
| `src/dashboard/layout_charts.py` | Pure Plotly chart builders for the page |
| `docs/dashboard_design.md` | This document |
