import argparse
import sys

import pandas as pd


REQUIRED_COLUMNS = [
    "customer_id",
    "customer_type",
    "region",
    "product_tier",
    "lifetime_value",
    "churn",
    "support_tickets",
    "retention_days",
]
NUMERIC_COLUMNS = [
    "customer_id",
    "lifetime_value",
    "churn",
    "support_tickets",
    "retention_days",
]


def validate(path, min_rows=100):
    print(f"Validating: {path}")
    errors = []

    try:
        df = pd.read_csv(path)
    except (OSError, ValueError) as error:
        print(f"ERROR: Unable to read input: {error}")
        return 1

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
    else:
        print("PASS: Required columns present")

    type_errors = []
    for column in NUMERIC_COLUMNS:
        if column in df.columns and not pd.api.types.is_numeric_dtype(df[column]):
            type_errors.append(column)
    if type_errors:
        errors.append(f"Columns are not numeric: {type_errors}")
    else:
        print("PASS: Numeric columns have expected dtypes")

    if len(df) < min_rows:
        errors.append(f"Row count {len(df)} below minimum {min_rows}")
    else:
        print(f"PASS: Row count {len(df)} meets minimum {min_rows}")

    null_columns = [column for column in df.columns if df[column].isnull().all()]
    if null_columns:
        errors.append(f"Fully null columns: {null_columns}")
    else:
        print("PASS: No fully null columns")

    if errors:
        print("VALIDATION FAILED:")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("ALL CHECKS PASSED")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Validate an Open Pulse dataset")
    parser.add_argument("path")
    parser.add_argument("--min-rows", type=int, default=100)
    args = parser.parse_args()
    return validate(args.path, args.min_rows)


if __name__ == "__main__":
    sys.exit(main())