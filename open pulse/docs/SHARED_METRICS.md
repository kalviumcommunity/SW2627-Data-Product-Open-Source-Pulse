# Shared Metrics — One SQL, One Number

> **Problem:** Finance counts invoiced, Sales counts paid, Product counts
> transactions, Accounting sums line items — five teams, five different
> "Monthly Revenue" numbers.
> **Solution:** the metric is defined **once** as a versioned `.sql` file in
> `queries/`. Every team, notebook, dashboard and test loads *that file*.
> Nobody hand-writes metric SQL anymore.

## The contract

| Metric | File | Grain | Answers |
| --- | --- | --- | --- |
| Monthly Active Users | `queries/monthly_active_users.sql` | 1 row / month | Who transacted, split Enterprise vs SMB |
| Revenue by Segment | `queries/revenue_by_segment.sql` | 1 row / segment-month | The official "Monthly Revenue" plus order count, AOV, unique customers, revenue per customer |
| Conversion Funnel | `queries/conversion_funnel.sql` | 1 row / signup day | Signup → email verified → first purchase, % converted |

Column names in the result sets are a **contract**: downstream code
(`scripts/run_shared_queries.py`, `tests/test_shared_queries.py`,
dashboards) depends on them. Changing a column name requires updating the
contract everywhere in the same PR.

## Usage

```bash
python scripts/init_db.py            # build/rebuild analytics.db (seed 42, deterministic)
python scripts/run_shared_queries.py # load queries/*.sql -> DataFrames -> validate -> output/*.csv
python -m pytest tests/test_shared_queries.py -v
```

```python
from run_shared_queries import load_query, run_metric, get_engine
import pandas as pd

engine = get_engine()
mau = pd.read_sql(load_query("monthly_active_users"), engine)
```

## Validation gate (Task 5)

`validate_metrics(mau_df, revenue_df, funnel_df)` fails loudly when:

1. any metric table contains nulls;
2. revenue is not strictly positive, or conversion is outside `[0, 100]`;
3. the numbers are internally inconsistent (zero orders/revenue per
   segment-month, segment breakdown ≠ total MAU, funnel stage > signups).

Only after `✓ All metrics validated` may the numbers be quoted, and the
runner then exports `output/monthly_active_users.csv`,
`output/revenue_by_segment.csv`, `output/conversion_funnel.csv`.

## Dialect notes

The warehouse in this repo is SQLite (`analytics.db`). The `.sql` files use
SQLite syntax and document the PostgreSQL production equivalents in their
headers, e.g.:

| SQLite (this repo) | PostgreSQL (prod) |
| --- | --- |
| `DATE(x, 'start of month')` | `DATE_TRUNC('month', x)::DATE` |
| `DATE('now', 'start of month', '-12 months')` | `DATE_TRUNC('month', NOW()) - INTERVAL '12 months'` |
| `DATETIME('now', '-90 days')` | `NOW() - INTERVAL '90 days'` |

The conditional-aggregation `FILTER` clauses and all aliases are identical
in both dialects.
