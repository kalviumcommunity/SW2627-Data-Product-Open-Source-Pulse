# JOIN Strategy Documentation

Every join in this project is documented here with its purpose, row count
impact, unmatched key handling, and business rationale.

## Table Inventory

| Table | Rows | PK | FK | Purpose |
|-------|------|----|----|---------|
| `customers` | 60 | `customer_id` | — | Dimension: one row per customer |
| `transactions` | ~1600 | `transaction_id` | `customer_id`, `order_id` | Fact: one row per order line item |
| `customer_segments` | 1000 | `customer_id` | — | Dimension: segment metadata (region, tier, churn) |
| `users` | 450 | `user_id` | — | Funnel: signup -> verify -> first purchase |

## Join Types: When to Use Each

| Join | Use When | Result Size |
|------|----------|-------------|
| `INNER JOIN` | You only want records that match on both sides | <= both tables |
| `LEFT JOIN` | You want all rows from the left table, matched or not | >= left table |
| `FULL JOIN` | You want all records from both tables | >= both tables |

SQLite has no `FULL OUTER JOIN`. Simulate it with `UNION`:

```sql
SELECT a.*, b.* FROM a LEFT JOIN b ON a.id = b.id
UNION
SELECT a.*, b.* FROM b LEFT JOIN a ON a.id = b.id WHERE a.id IS NULL;
```

## Decision 1: customers LEFT JOIN transactions

```
File: queries/enterprise_annual_spending.sql
File: docs/join_validation/task1_left_join_validation.sql
```

| | |
|---|---|
| **Purpose** | Get all customers with their transaction history |
| **Join type** | LEFT JOIN (keep all customers) |
| **Row change** | 60 customers -> 60 grouped rows (1 per customer) |
| **Unmatched** | Customers with zero transactions (retained via LEFT) |
| **Business use** | Customer lifetime value, spend-based segmentation |

Why LEFT not INNER: A customer with no transactions is not an error.
They signed up but never purchased. Dropping them would hide the
signup-to-purchase conversion gap.

## Decision 2: customers LEFT JOIN customer_segments

```
File: docs/join_validation/task4_multi_table_join.sql
```

| | |
|---|---|
| **Purpose** | Enrich customers with segment metadata (region, tier, churn) |
| **Join type** | LEFT JOIN (dimension-to-dimension) |
| **Row change** | 60 -> 60 (1:1 match on customer_id) |
| **Unmatched** | customer_segments has 1000 rows, customers has 60 |
| **Business use** | Region-based reporting, churn analysis |

Why this works: Both tables are keyed on `customer_id`. The
`customer_segments` table has 1000 rows (generated independently),
so only 60 of those match the `customers` table. The LEFT JOIN keeps
all 60 customers and adds segment data where available.

## Decision 3: Multi-table join (3 tables)

```
File: docs/join_validation/task4_multi_table_join.sql
```

| | |
|---|---|
| **Purpose** | Complete customer view: transactions + segment metadata |
| **Join chain** | customers -> transactions (1:N) -> customer_segments (N:1) |
| **Row change** | 60 customers -> ~1600 rows (one per transaction) |
| **Unmatched** | Customers without segment data get NULLs for region/tier |
| **Business use** | Full customer 360 view, executive segment reports |

**Row multiplication risk**: The `customers -> transactions` join is
one-to-many. Each customer appears once per transaction. This is
expected behavior, not duplication. The `transactions -> customer_segments`
join is many-to-one (each transaction maps to one customer's segment),
so it does not multiply rows further.

**Validation**: Revenue totals are checked before and after the join.
If the join multiplied rows unexpectedly, aggregate sums would differ.

## Decision 4: Detecting Unmatched Keys

```
File: docs/join_validation/task2_detect_unmatched_keys.sql
```

Two types of unmatched records:

**A) Customers with no transactions** (LEFT JOIN WHERE ... IS NULL)
- Not an error. These are signups who never purchased.
- Count them to measure conversion rate.
- Business action: target with onboarding campaigns.

**B) Transactions with no matching customer** (orphaned records)
- This IS a data integrity problem.
- The FK `customer_id` in `transactions` references a non-existent customer.
- Root cause: data pipeline bug, stale export, or ID mismatch.
- Business action: quarantine and investigate before reporting.

## Decision 5: Compare Join Types

```
File: docs/join_validation/task3_compare_join_types.sql
```

| Join Type | Rows | What It Contains |
|-----------|------|-----------------|
| INNER | ~1600 | Only customers who have transactions |
| LEFT | ~1600 | All 60 customers + their transactions (NULLs for zero-spend) |
| FULL | ~1600 | All customers + all transactions (orphaned ones included) |

Why run all three: Confirm that INNER does not silently drop customers
you expected to see, and that LEFT does not drop transactions you
expected to keep.

## Validation Checklist

Before shipping any query with a JOIN:

1. **Row count**: Does the result size match your expectation?
2. **Unmatched keys**: Run the IS NULL check. Are unmatched rows
   expected (new customers) or unexpected (data bugs)?
3. **Aggregate check**: Sum a numeric column before and after the join.
   If the sums differ, the join multiplied rows.
4. **Join type**: Did you use LEFT when you needed all left-table rows?
   Did you use INNER when you only wanted matches?

## Files

| File | Task |
|------|------|
| `task1_left_join_validation.sql` | LEFT JOIN with row count validation |
| `task2_detect_unmatched_keys.sql` | Detect unmatched keys (IS NULL) |
| `task3_compare_join_types.sql` | INNER vs LEFT vs FULL comparison |
| `task4_multi_table_join.sql` | 3-table join with duplication check |
| `task4b_validate_no_duplication.sql` | Revenue totals before/after join |
| `validate_joins.py` | Python script: runs all queries, validates results |
| `JOIN_STRATEGY.md` | This file |
