"""Analyze and treat missing values with auditable decisions."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def analyze_missing_values(df):
    """Compute null counts and percentages before treatment."""
    missing_analysis = pd.DataFrame(
        {
            "column": df.columns,
            "null_count": df.isnull().sum().values,
            "null_percentage": (df.isnull().sum() / len(df) * 100).round(2).values,
            "data_type": df.dtypes.values,
            "null_meaning": "",
        }
    )

    print("=" * 70)
    print("BEFORE IMPUTATION - Missing Value Analysis")
    print("=" * 70)
    print(missing_analysis.to_string(index=False))
    print(f"\nTotal rows: {len(df)}")
    print(f"Total cells: {len(df) * len(df.columns)}")
    print(f"Missing cells: {df.isnull().sum().sum()}")
    print("=" * 70)

    return missing_analysis


def impute_mean_median(df, numerical_cols, strategy="median"):
    """Fill numerical nulls with the mean or median."""
    if strategy not in {"mean", "median"}:
        raise ValueError("strategy must be 'mean' or 'median'")

    df_imputed = df.copy()
    for col in numerical_cols:
        if col not in df_imputed or df_imputed[col].isnull().sum() == 0:
            continue
        fill_value = (
            df_imputed[col].median()
            if strategy == "median"
            else df_imputed[col].mean()
        )
        if pd.isna(fill_value):
            continue
        null_count = df_imputed[col].isnull().sum()
        df_imputed[col] = df_imputed[col].fillna(fill_value)
        print(f"  - {col}: filled {null_count} nulls with {strategy} ({fill_value:.2f})")
    return df_imputed


def impute_mode(df, categorical_cols):
    """Fill categorical nulls with the most common value."""
    df_imputed = df.copy()
    for col in categorical_cols:
        if col not in df_imputed or df_imputed[col].isnull().sum() == 0:
            continue
        modes = df_imputed[col].mode(dropna=True)
        if modes.empty:
            continue
        mode_val = modes.iloc[0]
        null_count = df_imputed[col].isnull().sum()
        df_imputed[col] = df_imputed[col].fillna(mode_val)
        print(f"  - {col}: filled {null_count} nulls with mode '{mode_val}'")
    return df_imputed


def impute_forward_fill(df, time_series_cols):
    """Fill time-series nulls with the previous known value."""
    df_imputed = df.copy()
    for col in time_series_cols:
        if col not in df_imputed or df_imputed[col].isnull().sum() == 0:
            continue
        null_count = df_imputed[col].isnull().sum()
        df_imputed[col] = df_imputed[col].ffill()
        print(f"  - {col}: forward-filled {null_count} nulls")
    return df_imputed


def drop_rows_with_nulls(df, critical_cols):
    """Drop rows where critical columns are null."""
    available_cols = [col for col in critical_cols if col in df.columns]
    if not available_cols:
        return df.copy()

    rows_before = len(df)
    df_imputed = df.dropna(subset=available_cols)
    rows_dropped = rows_before - len(df_imputed)
    print(f"  - Dropped {rows_dropped} rows with null in: {available_cols}")
    return df_imputed


def document_imputation_decisions(df_original, df_imputed, output_path=None):
    """Document imputation decisions with business justification."""
    decisions = {
        "amount": {
            "column_type": "numerical",
            "null_count_before": (
                df_original["amount"].isnull().sum()
                if "amount" in df_original
                else 0
            ),
            "strategy": "median_imputation",
            "value_used": (
                df_original["amount"].median() if "amount" in df_original else None
            ),
            "business_reasoning": (
                "Median purchase amount is representative of typical transaction. "
                "Mean would be skewed by high-value outliers. Maintains distribution integrity."
            ),
            "risk_assessment": "Low - median is stable metric resistant to outliers",
        },
        "email": {
            "column_type": "categorical_identifier",
            "null_count_before": (
                df_original["email"].isnull().sum() if "email" in df_original else 0
            ),
            "strategy": "drop_rows",
            "rows_affected": (
                df_original["email"].isnull().sum() if "email" in df_original else 0
            ),
            "business_reasoning": (
                "Email is critical for customer contact and marketing campaigns. "
                "Rows without email cannot be used for outreach. Data is incomplete."
            ),
            "risk_assessment": "Low - only affects small percentage of data",
        },
        "status_date": {
            "column_type": "datetime_series",
            "null_count_before": (
                df_original["status_date"].isnull().sum()
                if "status_date" in df_original
                else 0
            ),
            "strategy": "forward_fill",
            "interpretation": "Assumes last known status date is still valid until changed",
            "business_reasoning": (
                "For time-series analysis, forward fill preserves temporal continuity. "
                "Status typically does not change frequently."
            ),
            "risk_assessment": "Medium - assumes no change between observations",
        },
    }

    if output_path is None:
        output_path = Path(__file__).resolve().parents[1] / "output" / "imputation_decisions.json"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(decisions, file, indent=2, default=str)
    return decisions


def validate_imputation(df_original, df_imputed):
    """Compare missing-value metrics before and after imputation."""
    print("\n" + "=" * 70)
    print("AFTER IMPUTATION - Validation Report")
    print("=" * 70)
    print(f"Total rows before: {len(df_original)}")
    print(f"Total rows after:  {len(df_imputed)}")
    print(f"Rows removed: {len(df_original) - len(df_imputed)}")
    print(f"\nTotal nulls before: {df_original.isnull().sum().sum()}")
    print(f"Total nulls after:  {df_imputed.isnull().sum().sum()}")

    missing_after = pd.DataFrame(
        {
            "column": df_imputed.columns,
            "null_count_after": df_imputed.isnull().sum().values,
            "null_percentage_after": (
                df_imputed.isnull().sum() / len(df_imputed) * 100
            ).round(2).values,
        }
    )
    print("\nNull values by column after imputation:")
    print(missing_after.to_string(index=False))
    print("=" * 70)
    return missing_after


def main():
    """Run the end-to-end missing-value workflow."""
    project_root = Path(__file__).resolve().parents[1]
    raw_path = project_root / "data" / "raw" / "missing_data.csv"
    processed_path = project_root / "data" / "processed" / "cleaned_data.csv"

    df_original = pd.read_csv(raw_path)
    analyze_missing_values(df_original)

    print("\nStep 2: Applying imputation strategies...")
    df_imputed = drop_rows_with_nulls(df_original, ["customer_id", "email"])
    df_imputed = impute_mean_median(df_imputed, ["amount", "quantity"], strategy="median")
    df_imputed = impute_mode(df_imputed, ["category", "region"])
    df_imputed = impute_forward_fill(df_imputed, ["last_updated", "status_date"])

    print("\nStep 3: Documenting imputation decisions...")
    document_imputation_decisions(df_original, df_imputed)

    print("\nStep 4: Validating imputation...")
    validate_imputation(df_original, df_imputed)

    processed_path.parent.mkdir(parents=True, exist_ok=True)
    df_imputed.to_csv(processed_path, index=False)
    print(f"\n- Cleaned data saved to {processed_path}")


if __name__ == "__main__":
    main()