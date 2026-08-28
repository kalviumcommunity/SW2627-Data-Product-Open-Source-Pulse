"""
Database init entrypoint.

Builds the shared analytics warehouse (analytics.db) that every team reads
from. Creates three tables whose column names match the shared SQL files in
queries/, so those .sql files stay the single source of truth for metrics:

    customers    - dimension: one row per customer (segment = customer_type)
    transactions - fact: one row per order line item (order_id groups items)
    users        - signup funnel: created_at / email_verified_at /
                   first_purchase_at

Data is deterministic (seed 42). The raw CRM exports in data/raw/ predate
the warehouse and lack the dates/segments required for monthly metrics, so
demo data is generated here; regenerating always produces the same rows.
Tables created by earlier tasks (e.g. customers_cleaned) are left untouched.

Run: python scripts/init_db.py
"""

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, inspect

DB_PATH = "analytics.db"
SEED = 42
N_CUSTOMERS = 60
N_USERS = 450
N_LINE_ITEMS = 1600  # target transaction rows (order line items)


def generate_customers(rng, n=N_CUSTOMERS):
    """Generate the customer dimension with Enterprise/SMB segments."""
    prefixes = ["Apex", "Bolt", "Cedar", "Delta", "Ember",
                "Flint", "Grove", "Harbor", "Ivory", "Juniper"]
    suffixes = {"Enterprise": "Systems", "SMB": "Studio"}

    customer_types = rng.choice(["Enterprise", "SMB"], size=n, p=[0.35, 0.65])

    names, emails = [], []
    for i, ctype in enumerate(customer_types):
        name = (f"{prefixes[i % len(prefixes)]} {suffixes[ctype]} "
                f"{i // len(prefixes) + 1:02d}")
        names.append(name)
        emails.append(f"billing@{name.lower().replace(' ', '')}.example.com")

    today = pd.Timestamp.now().normalize()
    signup_dates = today - pd.to_timedelta(rng.integers(30, 730, n), unit="D")

    return pd.DataFrame({
        "customer_id": np.arange(1, n + 1),
        "customer_name": names,
        "email": emails,
        "customer_type": customer_types,
        "signup_date": signup_dates.strftime("%Y-%m-%d"),
    })


def generate_transactions(rng, customers, target_lines=N_LINE_ITEMS):
    """Generate order line items spread over the last ~13 months.

    One order contains 1-3 line items (Accounting's 'sum line items' view),
    so order_count < line-item count in the shared revenue metric.
    """
    n_customers = len(customers)
    customer_ids = customers["customer_id"].to_numpy()
    types = customers["customer_type"].to_numpy()
    today = pd.Timestamp.now()

    rows = []
    order_id = 5000
    while len(rows) < target_lines:
        cust_idx = int(rng.integers(0, n_customers))
        ctype = str(types[cust_idx])
        size = int(rng.choice([1, 2, 3], p=[0.55, 0.30, 0.15]))

        day_offset = int(rng.integers(0, 400))
        ts = (today - pd.Timedelta(days=day_offset)).normalize()
        ts += pd.Timedelta(hours=int(rng.integers(8, 21)),
                           minutes=int(rng.integers(0, 60)),
                           seconds=int(rng.integers(0, 60)))

        status = str(rng.choice(["completed", "pending", "refunded"],
                                p=[0.85, 0.10, 0.05]))
        for _ in range(size):
            if ctype == "Enterprise":
                amount = round(float(np.clip(rng.normal(850, 200), 50, None)), 2)
            else:
                amount = round(float(np.clip(rng.normal(180, 60), 20, None)), 2)
            rows.append({
                "transaction_id": 10000 + len(rows),
                "order_id": order_id,
                "customer_id": int(customer_ids[cust_idx]),
                "transaction_date": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "status": status,
                "customer_type": ctype,  # denormalized for the MAU metric
            })
        order_id += 1

    return pd.DataFrame(rows)


def generate_users(rng, n=N_USERS):
    """Generate signup-funnel users over the last 90 days.

    Stages: signup (created_at) -> email verified (email_verified_at)
    -> first purchase (first_purchase_at). Later-stage timestamps are always
    ordered after earlier ones and never in the future.
    """
    now = pd.Timestamp.now()

    minutes_ago = rng.uniform(0, 90 * 24 * 60, n)
    created = pd.Series(now - pd.to_timedelta(minutes_ago, unit="m"))
    span_min = (now - created).dt.total_seconds() / 60

    # ~80% verify their email within minutes..3 days (capped at half lifetime)
    verified_flag = rng.random(n) < 0.80
    verify_offset = np.minimum(rng.uniform(30, 3 * 24 * 60, n), span_min * 0.5)
    verified_at = created + pd.to_timedelta(
        np.where(verified_flag, verify_offset, np.nan), unit="m"
    )

    # ~55% of verified users go on to purchase (after 60%..95% of lifetime)
    purchased_flag = verified_flag & (rng.random(n) < 0.55)
    purchase_offset = span_min * rng.uniform(0.60, 0.95, n)
    purchased_at = created + pd.to_timedelta(
        np.where(purchased_flag, purchase_offset, np.nan), unit="m"
    )

    users = pd.DataFrame({
        "user_id": np.arange(1, n + 1),
        "email": [f"user{i:04d}@example.com" for i in range(1, n + 1)],
        "created_at": created,
        "email_verified_at": verified_at,
        "first_purchase_at": purchased_at,
    })
    for col in ("created_at", "email_verified_at", "first_purchase_at"):
        users[col] = users[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    return users


def build_analytics_db(database_path=DB_PATH):
    """Create/rebuild the warehouse tables and return the engine."""
    rng = np.random.default_rng(SEED)

    customers = generate_customers(rng)
    transactions = generate_transactions(rng, customers)
    users = generate_users(rng)

    engine = create_engine(f"sqlite:///{database_path}")
    customers.to_sql("customers", engine, if_exists="replace", index=False)
    transactions.to_sql("transactions", engine, if_exists="replace", index=False)
    users.to_sql("users", engine, if_exists="replace", index=False)

    # Verify load (tables from earlier tasks, e.g. customers_cleaned, untouched)
    tables = inspect(engine).get_table_names()
    for table in ("customers", "transactions", "users"):
        assert table in tables, f"{table} was not created"

    print("Shared analytics warehouse ready:")
    print(f"  customers    {len(customers):>6} rows "
          f"({customers['customer_type'].value_counts().to_dict()})")
    print(f"  transactions {len(transactions):>6} rows "
          f"({transactions['order_id'].nunique()} orders)")
    print(f"  users        {len(users):>6} rows "
          f"({users['first_purchase_at'].notna().sum()} converted)")
    print(f"  database     {database_path}")
    return engine


if __name__ == "__main__":
    build_analytics_db()
