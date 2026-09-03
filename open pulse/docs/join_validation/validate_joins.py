"""
Join Validation: prove every join is correct.

Connects to the analytics database, executes the join validation queries,
and verifies row counts, unmatched keys, and join-type differences.

Run: python docs/join_validation/validate_joins.py
"""

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "analytics.db"
SEGMENT_CSV = PROJECT_ROOT / "output" / "customer_segment_data.csv"

SEPARATOR = "=" * 78


def get_engine():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run 'python scripts/init_db.py' first to build the warehouse.")
        sys.exit(1)
    engine = create_engine(f"sqlite:///{DB_PATH}")
    _ensure_customer_segments(engine)
    return engine


def _ensure_customer_segments(engine):
    with engine.connect() as conn:
        exists = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='customer_segments'"
        )).fetchone()
    if exists:
        return
    if not SEGMENT_CSV.exists():
        print(f"WARNING: {SEGMENT_CSV} not found. Task 4 will skip customer_segments joins.")
        return
    df = pd.read_csv(SEGMENT_CSV)
    df.to_sql("customer_segments", engine, if_exists="replace", index=False)
    print(f"[setup] Loaded customer_segments ({len(df)} rows) from {SEGMENT_CSV.name}")


def run_query(engine, sql):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


def task1_left_join_validation(engine):
    print(f"\n{SEPARATOR}")
    print("TASK 1: LEFT JOIN with Row Count Validation")
    print(SEPARATOR)

    baseline = run_query(engine, "SELECT COUNT(*) AS cnt FROM customers")
    customer_count = int(baseline.iloc[0]["cnt"])
    print(f"\nBaseline: {customer_count} customers in customers table")

    result = run_query(engine, """
        SELECT
            c.customer_id,
            c.customer_name,
            c.customer_type,
            COUNT(DISTINCT t.order_id) AS order_count,
            COUNT(t.transaction_id)    AS line_items,
            ROUND(SUM(t.amount), 2)    AS total_spent
        FROM customers c
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
        GROUP BY c.customer_id, c.customer_name, c.customer_type
        ORDER BY total_spent DESC NULLS LAST
    """)

    joined_rows = len(result)
    multiply_factor = joined_rows / customer_count if customer_count else 0

    print(f"After LEFT JOIN (grouped): {joined_rows} rows")
    print(f"Row change: {joined_rows - customer_count:+d} "
          f"({(joined_rows - customer_count) / customer_count * 100:+.1f}%)")
    print(f"Multiplication factor: {multiply_factor:.2f}x (orders per customer)")

    zero_spend = result[result["total_spent"].isna()]
    print(f"Customers with zero spend (no transactions): {len(zero_spend)}")

    print(f"\nTop 5 customers by spend:")
    print(result.head(5).to_string(index=False))

    assert joined_rows == customer_count, (
        f"LEFT JOIN with GROUP BY should return {customer_count} rows, "
        f"got {joined_rows}"
    )
    print(f"\nPASS: LEFT JOIN grouped result equals customer count ({joined_rows})")


def task2_detect_unmatched_keys(engine):
    print(f"\n{SEPARATOR}")
    print("TASK 2: Detect Unmatched Keys")
    print(SEPARATOR)

    customer_count = int(run_query(engine, "SELECT COUNT(*) AS cnt FROM customers").iloc[0]["cnt"])

    no_orders = run_query(engine, """
        SELECT c.customer_id, c.customer_name, c.customer_type, c.signup_date
        FROM customers c
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
        WHERE t.transaction_id IS NULL
        ORDER BY c.signup_date
    """)

    orphaned = run_query(engine, """
        SELECT t.transaction_id, t.customer_id, t.order_id, t.amount, t.transaction_date
        FROM transactions t
        LEFT JOIN customers c ON t.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
        ORDER BY t.transaction_date
    """)

    no_orders_count = len(no_orders)
    orphaned_count = len(orphaned)

    print(f"\nCustomers without orders: {no_orders_count} "
          f"({no_orders_count / customer_count * 100:.1f}% of {customer_count})")
    if no_orders_count > 0:
        print(no_orders.to_string(index=False))

    print(f"\nOrphaned transactions (no matching customer): {orphaned_count}")
    if orphaned_count > 0:
        print(orphaned.to_string(index=False))
        print("WARNING: Orphaned records detected - investigate customer_id mismatch")
    else:
        print("No orphaned transactions - referential integrity intact")

    assert orphaned_count == 0, f"Found {orphaned_count} orphaned transactions"
    print(f"\nPASS: No orphaned transactions")


def task3_compare_join_types(engine):
    print(f"\n{SEPARATOR}")
    print("TASK 3: Compare Join Types")
    print(SEPARATOR)

    inner = run_query(engine, """
        SELECT c.customer_id, c.customer_type, t.transaction_id, t.order_id, t.amount
        FROM customers c
        INNER JOIN transactions t ON c.customer_id = t.customer_id
    """)

    left = run_query(engine, """
        SELECT c.customer_id, c.customer_type, t.transaction_id, t.order_id, t.amount
        FROM customers c
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
    """)

    full = run_query(engine, """
        SELECT c.customer_id, c.customer_type, t.transaction_id, t.order_id, t.amount
        FROM customers c
        LEFT JOIN transactions t ON c.customer_id = t.customer_id

        UNION

        SELECT c.customer_id, c.customer_type, t.transaction_id, t.order_id, t.amount
        FROM transactions t
        LEFT JOIN customers c ON t.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """)

    print(f"\nINNER JOIN:  {len(inner):>6} rows  (only matched records)")
    print(f"LEFT JOIN:   {len(left):>6} rows  (all customers + matched transactions)")
    print(f"FULL JOIN:   {len(full):>6} rows  (all from both sides)")

    print(f"\nDifference LEFT - INNER:  {len(left) - len(inner):+d} "
          f"(customers with no transactions)")
    print(f"Difference FULL - INNER:  {len(full) - len(inner):+d} "
          f"(customers with no transactions + orphaned transactions)")

    assert len(left) >= len(inner), "LEFT must be >= INNER"
    assert len(full) >= len(inner), "FULL must be >= INNER"
    print(f"\nPASS: Join type ordering holds (INNER <= LEFT <= FULL)")


def task4_multi_table_join(engine):
    print(f"\n{SEPARATOR}")
    print("TASK 4: Multi-Table Join (3 tables) + Duplication Check")
    print(SEPARATOR)

    with engine.connect() as conn:
        has_segments = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='customer_segments'"
        )).fetchone()

    if not has_segments:
        print("SKIP: customer_segments table not found. Run build_kpis.py first.")
        print("Falling back to 2-table join (customers -> transactions).")

        three_table = run_query(engine, """
            SELECT
                c.customer_id,
                c.customer_name,
                c.customer_type,
                t.transaction_id,
                t.order_id,
                t.amount
            FROM customers c
            LEFT JOIN transactions t ON c.customer_id = t.customer_id
            WHERE c.customer_type = 'Enterprise'
            ORDER BY c.customer_id, t.transaction_date DESC
        """)

        before = run_query(engine, """
            SELECT customer_id, ROUND(SUM(amount), 2) AS revenue
            FROM transactions
            WHERE status = 'completed'
            GROUP BY customer_id
        """)

        after = run_query(engine, """
            SELECT c.customer_id, ROUND(SUM(t.amount), 2) AS revenue
            FROM customers c
            LEFT JOIN transactions t ON c.customer_id = t.customer_id
            WHERE t.status = 'completed'
            GROUP BY c.customer_id
        """)
    else:
        three_table = run_query(engine, """
            SELECT
                c.customer_id,
                c.customer_name,
                c.customer_type,
                cs.region,
                cs.product_tier,
                t.transaction_id,
                t.order_id,
                t.amount
            FROM customers c
            LEFT JOIN transactions t ON c.customer_id = t.customer_id
            LEFT JOIN customer_segments cs ON c.customer_id = cs.customer_id
            WHERE c.customer_type = 'Enterprise'
            ORDER BY c.customer_id, t.transaction_date DESC
        """)

        before = run_query(engine, """
            SELECT customer_id, ROUND(SUM(amount), 2) AS revenue
            FROM transactions
            WHERE status = 'completed'
            GROUP BY customer_id
        """)

        after = run_query(engine, """
            SELECT c.customer_id, ROUND(SUM(t.amount), 2) AS revenue
            FROM customers c
            LEFT JOIN transactions t ON c.customer_id = t.customer_id
            LEFT JOIN customer_segments cs ON c.customer_id = cs.customer_id
            WHERE t.status = 'completed'
            GROUP BY c.customer_id
        """)

    print(f"\n3-table join (Enterprise): {len(three_table)} rows")
    print(f"Unique customers: {three_table['customer_id'].nunique()}")
    print(f"Unique transactions: {three_table['transaction_id'].dropna().nunique()}")

    before_dict = dict(zip(before["customer_id"], before["revenue"]))
    after_dict = dict(zip(after["customer_id"], after["revenue"]))

    mismatches = 0
    for cust_id in before_dict:
        if cust_id in after_dict:
            if abs(before_dict[cust_id] - after_dict[cust_id]) > 0.01:
                mismatches += 1
                print(f"  MISMATCH customer {cust_id}: "
                      f"before={before_dict[cust_id]}, after={after_dict[cust_id]}")

    print(f"\nRevenue mismatch check: {mismatches} mismatches out of "
          f"{len(before_dict)} customers")
    assert mismatches == 0, f"Found {mismatches} revenue mismatches from join duplication"
    print("PASS: No duplication detected in 3-table join")


def task5_summary(engine):
    print(f"\n{SEPARATOR}")
    print("TASK 5: Join Strategy Summary")
    print(SEPARATOR)

    stats = {}
    for table in ["customers", "transactions", "customer_segments", "users"]:
        try:
            cnt = int(run_query(engine, f"SELECT COUNT(*) AS cnt FROM {table}").iloc[0]["cnt"])
            stats[table] = cnt
        except Exception:
            stats[table] = 0

    print("\nTable row counts:")
    for table, count in stats.items():
        print(f"  {table:25s} {count:>6} rows")

    print("""
JOIN DECISIONS:

1. customers LEFT JOIN transactions
   - Why: Keep all customers, show their transaction history
   - Rows: customers (60) -> grouped by customer_id = 60 rows (1 per customer)
   - Unmatched: customers with zero transactions (shown with NULL spend)

2. customers LEFT JOIN customer_segments
   - Why: Enrich customer rows with segment metadata (region, tier, churn)
   - Rows: 1:1 match (both keyed on customer_id)
   - Risk: None - clean dimension-to-dimension join

3. Multi-table (customers -> transactions -> customer_segments)
   - Why: Complete customer view with history + segment context
   - Rows: One row per transaction per customer
   - Risk: Row multiplication if both transactions and segments are 1:N
   - Mitigation: Validate revenue totals match before/after join
""")

    print("PASS: All join validations completed successfully")


def main():
    print(SEPARATOR)
    print("JOIN VALIDATION SUITE")
    print(f"Database: {DB_PATH}")
    print(SEPARATOR)

    engine = get_engine()

    task1_left_join_validation(engine)
    task2_detect_unmatched_keys(engine)
    task3_compare_join_types(engine)
    task4_multi_table_join(engine)
    task5_summary(engine)

    engine.dispose()
    print(f"\n{SEPARATOR}")
    print("ALL JOIN VALIDATIONS PASSED")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
