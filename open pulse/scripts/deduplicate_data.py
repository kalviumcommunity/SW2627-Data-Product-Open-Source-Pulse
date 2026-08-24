"""Detect, remove, and audit duplicate records."""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def detect_exact_duplicates(df):
    """Find rows where all values are identical."""
    exact_dups = int(df.duplicated().sum())
    dup_rows = df[df.duplicated(keep=False)].sort_values(by=df.columns.tolist())

    print("\nEXACT DUPLICATE DETECTION")
    print("=" * 60)
    print(f"Exact duplicates found: {exact_dups}")
    print(f"Total duplicate rows (including originals): {len(dup_rows)}")
    if len(dup_rows) > 0:
        print("\nSample duplicate rows:")
        print(dup_rows.head(10).to_string())
    return exact_dups, dup_rows


def detect_near_duplicates(df, key_columns):
    """Find records sharing key values, even when other fields differ."""
    duplicate_keys = df[df.duplicated(subset=key_columns, keep=False)]

    print("\nNEAR-DUPLICATE DETECTION")
    print("=" * 60)
    print(f"Records with duplicate keys: {len(duplicate_keys)}")
    print(
        "Unique key combinations with duplicates: "
        f"{duplicate_keys.groupby(key_columns, dropna=False).ngroups}"
    )
    if len(duplicate_keys) > 0:
        print("\nSample groups with duplicate keys:")
        for keys, group in list(
            duplicate_keys.groupby(key_columns, dropna=False, sort=False)
        )[:3]:
            print(f"\n  Key: {keys}")
            print(f"  Records in group: {len(group)}")
            print(group.to_string())
    return duplicate_keys


def remove_exact_duplicates(df, keep="first"):
    """Remove exact duplicates using the requested keep strategy."""
    if keep not in {"first", "last", False}:
        raise ValueError("keep must be 'first', 'last', or False")

    rows_before = len(df)
    df_dedup = df.drop_duplicates(keep=keep)
    rows_removed = rows_before - len(df_dedup)
    removal_pct = rows_removed / rows_before * 100 if rows_before else 0

    print("\nEXACT DUPLICATE REMOVAL")
    print("=" * 60)
    print(f"Keep strategy: {keep}")
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {len(df_dedup):,}")
    print(f"Rows removed: {rows_removed:,} ({removal_pct:.2f}%)")
    return df_dedup


def remove_near_duplicates(df, key_columns, keep_strategy="most_complete"):
    """Remove duplicate keys by retaining the best record in each group."""
    if keep_strategy not in {"most_complete", "first", "last"}:
        raise ValueError("keep_strategy must be 'most_complete', 'first', or 'last'")

    rows_before = len(df)
    if keep_strategy == "most_complete":
        completeness = df.isnull().sum(axis=1)
        df_dedup = (
            df.assign(_null_count=completeness)
            .sort_values("_null_count", kind="stable")
            .drop_duplicates(subset=key_columns, keep="first")
            .drop(columns="_null_count")
            .sort_index()
        )
    else:
        df_dedup = df.drop_duplicates(
            subset=key_columns, keep=keep_strategy
        )

    rows_removed = rows_before - len(df_dedup)
    removal_pct = rows_removed / rows_before * 100 if rows_before else 0
    print("\nNEAR-DUPLICATE REMOVAL")
    print("=" * 60)
    print(f"Keep strategy: {keep_strategy}")
    print(f"Key columns: {key_columns}")
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {len(df_dedup):,}")
    print(f"Rows removed: {rows_removed:,} ({removal_pct:.2f}%)")
    return df_dedup


def log_removed_duplicates(df_original, df_dedup, output_dir=None):
    """Save removed rows and an audit summary."""
    removed_mask = ~df_original.index.isin(df_dedup.index)
    removed_records = df_original[removed_mask]
    output_dir = Path(output_dir or Path(__file__).resolve().parents[1] / "output")
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_file = output_dir / "removed_duplicates_audit.csv"
    summary_file = output_dir / "dedup_audit_summary.json"

    print("\nAUDIT LOGGING")
    print("=" * 60)
    print(f"Total records removed: {len(removed_records)}")
    removed_records.to_csv(audit_file, index=False)
    print("- Removed records saved to audit file")

    audit_summary = {
        "removal_timestamp": datetime.now().isoformat(),
        "total_removed": int(len(removed_records)),
        "reason": "Duplicate detection and deduplication",
        "audit_file": "output/removed_duplicates_audit.csv",
        "audit_note": "All removed records logged for compliance and recovery if needed",
    }
    with summary_file.open("w", encoding="utf-8") as file:
        json.dump(audit_summary, file, indent=2, default=str)
    print("- Audit summary saved")
    print("=" * 60)
    return removed_records, audit_summary


def compare_before_after(df_original, df_dedup, output_path=None):
    """Create and save before/after deduplication metrics."""
    rows_removed = len(df_original) - len(df_dedup)
    comparison = {
        "rows_before": len(df_original),
        "rows_after": len(df_dedup),
        "rows_removed": rows_removed,
        "removal_percentage": round(
            rows_removed / len(df_original) * 100 if len(df_original) else 0, 2
        ),
        "columns": len(df_original.columns),
        "nulls_before": int(df_original.isnull().sum().sum()),
        "nulls_after": int(df_dedup.isnull().sum().sum()),
        "timestamp": datetime.now().isoformat(),
    }

    print("\n" + "=" * 70)
    print("DEDUPLICATION FINAL SUMMARY")
    print("=" * 70)
    print(f"Rows before: {comparison['rows_before']:,}")
    print(f"Rows after:  {comparison['rows_after']:,}")
    print(
        f"Removed:     {comparison['rows_removed']:,} "
        f"({comparison['removal_percentage']}%)"
    )
    print(f"\nNulls before: {comparison['nulls_before']:,}")
    print(f"Nulls after:  {comparison['nulls_after']:,}")
    print(f"Null change:  {comparison['nulls_before'] - comparison['nulls_after']:,}")
    print("=" * 70)

    if output_path is None:
        output_path = Path(__file__).resolve().parents[1] / "output" / "dedup_summary.json"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(comparison, file, indent=2, default=str)
    return comparison


def main():
    """Run the end-to-end deduplication workflow."""
    project_root = Path(__file__).resolve().parents[1]
    df_original = pd.read_csv(project_root / "data" / "raw" / "data_with_dupes.csv")

    print("\n" + "=" * 70)
    print("STARTING DEDUPLICATION WORKFLOW")
    print("=" * 70)
    print(f"Initial record count: {len(df_original):,}")

    print("\n[Step 1/4] Detecting exact duplicates...")
    detect_exact_duplicates(df_original)
    print("\n[Step 2/4] Detecting near-duplicates by key...")
    detect_near_duplicates(df_original, ["customer_id", "transaction_date"])
    print("\n[Step 3/4] Removing exact duplicates (keeping first)...")
    df_dedup = remove_exact_duplicates(df_original, keep="first")
    print("\n[Step 4/4] Removing near-duplicates (keeping most complete)...")
    df_dedup = remove_near_duplicates(
        df_dedup,
        ["customer_id", "transaction_date"],
        keep_strategy="most_complete",
    )

    log_removed_duplicates(df_original, df_dedup)
    compare_before_after(df_original, df_dedup)
    output_path = project_root / "data" / "processed" / "deduplicated_data.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_dedup.to_csv(output_path, index=False)
    print(f"\n- Deduplicated data saved to {output_path}")


if __name__ == "__main__":
    main()