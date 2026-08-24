"""Validate customer-to-order joins and preserve an auditable join decision."""

import json
from pathlib import Path

import pandas as pd


JOIN_KEY = "customer_id"


def merge_with_row_validation(df_customers, df_orders):
    """Perform the production left join and report its row-count change."""
    print(f"Left: {len(df_customers)}")
    print(f"Right: {len(df_orders)}")

    df_merged = pd.merge(
        df_customers,
        df_orders,
        on=JOIN_KEY,
        how="left",
        suffixes=("_customer", "_order"),
        validate="one_to_many",
    )
    print(f"Merged: {len(df_merged)}")
    print(f"Change: {len(df_merged) - len(df_customers)}")
    return df_merged


def detect_unmatched_keys(df_customers, df_orders, output_dir):
    """Find unmatched customers and orphaned orders and save both datasets."""
    unmatched_customers = df_customers[
        ~df_customers[JOIN_KEY].isin(df_orders[JOIN_KEY])
    ]
    unmatched_orders = df_orders[
        ~df_orders[JOIN_KEY].isin(df_customers[JOIN_KEY])
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    unmatched_customers.to_csv(output_dir / "unmatched_customers.csv", index=False)
    unmatched_orders.to_csv(output_dir / "unmatched_orders.csv", index=False)
    print(f"Customers without orders: {len(unmatched_customers)}")
    print(f"Orphaned orders: {len(unmatched_orders)}")
    return unmatched_customers, unmatched_orders


def compare_join_types(df_customers, df_orders):
    """Compare inner, left, and outer joins using the shared customer key."""
    inner = pd.merge(df_customers, df_orders, on=JOIN_KEY, how="inner")
    left = pd.merge(df_customers, df_orders, on=JOIN_KEY, how="left")
    outer = pd.merge(df_customers, df_orders, on=JOIN_KEY, how="outer")
    counts = {"inner": len(inner), "left": len(left), "outer": len(outer)}
    print(f"Inner: {counts['inner']}, Left: {counts['left']}, Outer: {counts['outer']}")
    return counts


def validate_join_duplication(df_merged, df_orders):
    """Check columns and quantify the highest order count for one customer."""
    print(f"Merged columns: {list(df_merged.columns)}")
    key_counts = df_merged[JOIN_KEY].value_counts(dropna=False)
    order_counts = df_orders[JOIN_KEY].value_counts(dropna=False)
    max_orders = int(order_counts.max()) if not order_counts.empty else 0
    print(f"Max orders per customer: {max_orders}")
    return {
        "merged_columns": list(df_merged.columns),
        "max_orders_per_customer": max_orders,
        "merged_key_counts": {str(key): int(value) for key, value in key_counts.items()},
    }


def document_join_decision(
    df_customers,
    df_orders,
    df_merged,
    unmatched_customers,
    unmatched_orders,
    output_path,
):
    """Save the selected join and its validation metrics as JSON."""
    join_report = {
        "join_type": "left",
        "left_table": "customers",
        "right_table": "orders",
        "join_key": JOIN_KEY,
        "left_rows": len(df_customers),
        "right_rows": len(df_orders),
        "result_rows": len(df_merged),
        "unmatched_left": len(unmatched_customers),
        "unmatched_right": len(unmatched_orders),
        "reasoning": "Left join preserves all customers; unmatched customers have no orders",
    }
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(join_report, file, indent=2)
    print(json.dumps(join_report, indent=2))
    return join_report


def main():
    """Run customer-order join validation and save the joined data."""
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "output"
    df_customers = pd.read_csv(project_root / "data" / "raw" / "customers.csv")
    df_orders = pd.read_csv(
        project_root / "data" / "processed" / "transactions_ingested.csv"
    )

    print("\n" + "=" * 70)
    print("STARTING CUSTOMER-ORDER JOIN VALIDATION")
    print("=" * 70)
    df_merged = merge_with_row_validation(df_customers, df_orders)
    unmatched_customers, unmatched_orders = detect_unmatched_keys(
        df_customers, df_orders, output_dir
    )
    join_counts = compare_join_types(df_customers, df_orders)
    duplication = validate_join_duplication(df_merged, df_orders)
    join_report = document_join_decision(
        df_customers,
        df_orders,
        df_merged,
        unmatched_customers,
        unmatched_orders,
        output_dir / "join_report.json",
    )

    df_merged.to_csv(output_dir / "customers_orders_left_join.csv", index=False)
    with (output_dir / "join_validation_summary.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            {"join_counts": join_counts, "duplication_validation": duplication},
            file,
            indent=2,
        )
    print(f"Joined data saved to {output_dir / 'customers_orders_left_join.csv'}")


if __name__ == "__main__":
    main()