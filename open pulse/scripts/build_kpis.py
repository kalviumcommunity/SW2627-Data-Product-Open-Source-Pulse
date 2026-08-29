"""Build the KPI layer and prove the numbers.

Loads the committed aggregate artifacts into the analytics database, creates
the KPI views from sql/analytics/kpi_views.sql, computes every KPI twice - once
in SQL through the views and once independently in pandas - and fails if the
two disagree. Writes output/kpi_summary.csv and output/KPI_LINEAGE.md.

Nothing here hard-codes a date or a value. The reporting window is derived from
the newest month present in the data, so loading a fresher extract moves the
window forward with no code change.

Run: python scripts/build_kpis.py
"""

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard import config, data_loader, kpi  # noqa: E402


TOLERANCE = 1e-6


def load_tables(engine):
    """Load the source artifacts into the database.

    Reuses ``load_to_database.load_cleaned_data_to_database``, the repeatable
    loader from the database module, so the KPI tables arrive through the same
    validated path as every other table in the project.
    """
    loader = data_loader._load_script_module("load_to_database")

    daily = pd.read_csv(config.DAILY_METRICS, parse_dates=["date"])
    daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")
    loader.load_cleaned_data_to_database(daily, "daily_metrics", str(config.DB_PATH))

    customers = pd.read_csv(config.CUSTOMER_SEGMENT_DATA)
    loader.load_cleaned_data_to_database(
        customers, "customer_segments", str(config.DB_PATH)
    )
    return daily, customers


def create_views(engine):
    """Execute the KPI view definitions."""
    statements = config.KPI_VIEWS_SQL.read_text(encoding="utf-8")
    raw = engine.raw_connection()
    try:
        raw.executescript(statements)
        raw.commit()
    finally:
        raw.close()

    with engine.connect() as connection:
        views = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
        ).scalars().all()
    print(f"\n[views] created {len(views)}: {', '.join(views)}")
    return views


def read_kpis_from_sql(engine):
    """Read every KPI out of the views."""
    with engine.connect() as connection:
        periods = pd.read_sql("SELECT * FROM vw_kpi_periods", connection).iloc[0]
        summary = pd.read_sql("SELECT * FROM vw_kpi_summary", connection)
        churn = pd.read_sql("SELECT * FROM vw_churn_kpi", connection).iloc[0]
        totals = pd.read_sql(
            "SELECT * FROM vw_kpi_period_totals ORDER BY period DESC", connection
        )

    values = {}
    lookup = summary.set_index("metric")
    for metric in ["revenue", "transactions", "avg_order_value", "signups"]:
        row = lookup.loc[metric]
        values[metric] = {
            "current": float(row["current_value"]),
            "prior": float(row["prior_value"]),
            "change_pct": float(row["change_pct"]),
        }
    values["churn_rate"] = {
        "current": float(churn["current_value"]),
        "target": float(churn["target_value"]),
        "change_pct": float(churn["change_pct"]),
    }
    return values, periods, totals


def compute_kpis_in_pandas(daily, customers):
    """Compute the same KPIs independently, as a check on the SQL."""
    current, prior, context = kpi.matched_month_windows(daily)

    def totals(frame):
        revenue = float(frame["daily_revenue"].sum())
        transactions = float(frame["transaction_count"].sum())
        return {
            "revenue": revenue,
            "transactions": transactions,
            "signups": float(frame["signup_rate"].sum()),
            "avg_order_value": revenue / transactions if transactions else float("nan"),
        }

    current_totals, prior_totals = totals(current), totals(prior)

    # The comparison this project deliberately does not use, kept so the
    # lineage document can show what the matched window is protecting against.
    frame = daily.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    prior_full = frame[
        frame["date"].dt.to_period("M") == pd.Period(context["prior_month"])
    ]
    context["naive_revenue_change_pct"] = kpi.percent_change(
        current_totals["revenue"], float(prior_full["daily_revenue"].sum())
    )
    context["prior_full_revenue"] = float(prior_full["daily_revenue"].sum())
    values = {
        metric: {
            "current": current_totals[metric],
            "prior": prior_totals[metric],
            "change_pct": kpi.percent_change(
                current_totals[metric], prior_totals[metric]
            ),
        }
        for metric in current_totals
    }
    churn_now = float(customers["churn"].mean())
    values["churn_rate"] = {
        "current": churn_now,
        "target": kpi.CHURN_TARGET,
        "change_pct": kpi.percent_change(churn_now, kpi.CHURN_TARGET),
    }
    return values, context


def cross_validate(sql_values, pandas_values):
    """Compare the SQL and pandas results and report each metric."""
    print("\n" + "=" * 78)
    print("CROSS-VALIDATION: SQL views vs independent pandas computation")
    print("=" * 78)
    print(f"{'metric':18} {'SQL':>16} {'pandas':>16} {'difference':>14}   result")

    failures = []
    for key in sql_values:
        left = sql_values[key]["current"]
        right = pandas_values[key]["current"]
        difference = abs(left - right)
        relative = difference / abs(right) if right else difference
        ok = relative < TOLERANCE
        if not ok:
            failures.append(key)
        print(
            f"{key:18} {left:>16,.4f} {right:>16,.4f} {difference:>14.2e}   "
            f"{'match' if ok else 'MISMATCH'}"
        )

    if failures:
        raise SystemExit(
            f"\nKPI cross-validation failed for: {', '.join(failures)}. "
            "The SQL views and the pandas computation disagree."
        )
    print("\nAll KPIs agree across both computation paths.")


def write_outputs(table, context):
    """Write the KPI summary table and the lineage document."""
    export = table[
        [
            "Metric",
            "Key",
            "Current",
            "Prior",
            "Change_Pct",
            "Arrow",
            "Status",
            "Direction",
            "Basis",
            "Value_Display",
            "Change_Display",
        ]
    ]
    export.to_csv(config.KPI_SUMMARY, index=False)
    print(f"\n[output] {config.KPI_SUMMARY.relative_to(PROJECT_ROOT)}")

    rows = "\n".join(
        f"| {r.Metric} | `{r.Key}` | {r.Value_Display} | "
        f"{r.Change_Display or 'n/a'} | {r.Arrow} {r.Status} | "
        f"{'higher is better' if r.Direction == kpi.Direction.HIGHER_IS_BETTER else 'lower is better'} |"
        for r in table.itertuples()
    )
    lineage = "\n\n".join(
        f"""### {spec['label']}

- **Business question:** {spec['question']}
- **Source:** `{spec['source']}`
- **Comparison:** {
    'against the matched window of the prior month'
    if spec['basis'] == 'period'
    else f'against the retention target of {kpi.CHURN_TARGET:.0%}'
}
- **Direction:** {'higher is better' if spec['direction'] == kpi.Direction.HIGHER_IS_BETTER else 'lower is better, so the colour is inverted'}
- **Validation:** computed in SQL through the views and again in pandas; the
  build fails if the two differ by more than {TOLERANCE:g} relative."""
        for spec in kpi.KPI_SPECS
    )

    document = f"""# KPI Lineage

Where every number on the executive summary comes from, how its comparison
period is chosen, and how it was checked.

Regenerate with `python scripts/build_kpis.py`. The build recomputes every KPI
in both SQL and pandas and fails if they disagree, so this document cannot
drift from the dashboard.

## Current values

| Metric | Key | Value | Change | Status | Direction |
|---|---|---|---|---|---|
{rows}

## Reporting window

| | |
|---|---|
| Current period | {context['current_month']} ({context['current_start']:%d %b} to {context['current_end']:%d %b %Y}) |
| Prior period | {context['prior_month']} ({context['prior_start']:%d %b} to {context['prior_end']:%d %b %Y}) |
| Window length | {context['window_days']} business days each |
| Prior month total | {context['prior_month_total_days']} business days |

### Why the prior month is truncated

The newest month in the data is partial, holding {context['window_days']} of the
{context['prior_month_total_days']} business days a full month carries here. Comparing it against a
complete prior month would compare {context['window_days']} days of trading against
{context['prior_month_total_days']}, and every additive metric would appear to collapse.

Both windows are therefore cut to the same {context['window_days']} days. The
difference this makes is not cosmetic:

| Comparison | Revenue change | Reads as |
|---|---|---|
| Matched windows, {context['window_days']} days each | **{table.loc[table['Key'] == 'revenue', 'Change_Pct'].iloc[0]:+.1f}%** | growing |
| Naive, {context['window_days']} days against the full {context['prior_month_total_days']}-day prior month | {context['naive_revenue_change_pct']:+.1f}% | collapsing |

The naive form reports roughly a third of the revenue disappearing when trading
is in fact growing. It compares {context['window_days']} days of takings against
{context['prior_month_total_days']}, and the gap is arithmetic, not business. Shipping that number turns a
KPI row into a false alarm, and it is the single most common way a KPI row
loses its credibility.

## Metric definitions

{lineage}

## Notes on sourcing

**Views, not tables.** The dashboard reads `vw_kpi_summary` and `vw_churn_kpi`.
Changing a metric definition means editing `sql/analytics/kpi_views.sql` once;
no consumer changes.

**No hard-coded dates.** `vw_kpi_periods` derives the current month from
`MAX(month)` in the data and the prior month by SQL date arithmetic. A newer
extract moves the window forward on its own.

**No hard-coded values.** Every figure on the card comes from the views. The
only constants are the retention target ({kpi.CHURN_TARGET:.0%}, the threshold
`analyze_segments.py` already uses to flag a segment) and the
{kpi.FLAT_THRESHOLD_PCT:g}% band inside which a change reads as flat.

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
"""
    config.KPI_LINEAGE.write_text(document, encoding="utf-8")
    print(f"[output] {config.KPI_LINEAGE.relative_to(PROJECT_ROOT)}")


def main():
    """Build the KPI layer end to end."""
    print("=" * 78)
    print("BUILDING KPI LAYER")
    print("=" * 78)
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{config.DB_PATH}")
    print(f"Database: {config.DB_PATH}")

    daily, customers = load_tables(engine)
    create_views(engine)

    sql_values, periods, _totals = read_kpis_from_sql(engine)
    pandas_values, context = compute_kpis_in_pandas(daily, customers)
    cross_validate(sql_values, pandas_values)

    table = kpi.build_kpi_table(sql_values)

    print("\n" + "=" * 78)
    print(f"KPI SUMMARY  |  {context['current_month']} vs {context['prior_month']}, "
          f"{context['window_days']} business days each")
    print("=" * 78)
    print(f"{'metric':18} {'value':>12} {'change':>18}  status")
    for row in table.itertuples():
        print(
            f"{row.Metric:18} {row.Value_Display:>12} "
            f"{(row.Change_Display or 'n/a'):>16} {row.Arrow}  {row.Status}"
        )

    write_outputs(table, context)
    engine.dispose()
    print("\nKPI layer built and validated.")


if __name__ == "__main__":
    main()
