"""Enforce explicit data types and record conversion results."""

from pathlib import Path

import numpy as np
import pandas as pd


def cast_columns_to_types(df, type_mapping):
    """Cast mapped columns and return the typed frame with a conversion log."""
    df_typed = df.copy()
    conversion_log = {}

    for col, target_dtype in type_mapping.items():
        if col not in df.columns:
            print(f"Warning: Column {col} not found in DataFrame")
            continue

        original_dtype = df[col].dtype
        try:
            df_typed[col] = df_typed[col].astype(target_dtype)
            conversion_log[col] = {
                "from": str(original_dtype),
                "to": str(target_dtype),
                "status": "success",
            }
            print(f"- {col}: {original_dtype} -> {target_dtype}")
        except Exception as error:
            conversion_log[col] = {
                "from": str(original_dtype),
                "to": str(target_dtype),
                "status": "failed",
                "error": str(error),
            }
            print(f"x {col}: Conversion failed - {error}")
            raise

    return df_typed, conversion_log


def convert_string_dates_to_datetime(df, date_columns, date_format=None):
    """Convert date columns to datetime, using an explicit format when supplied."""
    df_typed = df.copy()

    for col in date_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue
        try:
            if date_format:
                df_typed[col] = pd.to_datetime(df_typed[col], format=date_format)
            else:
                df_typed[col] = pd.to_datetime(df_typed[col])
            print(f"- {col}: Converted to datetime")
        except Exception as error:
            print(f"x {col}: Conversion failed - {error}")
            print(f"  Sample values: {df[col].head(3).tolist()}")
            print(f"  Expected format: {date_format}")
            raise

    return df_typed


def convert_currency_to_float(df, currency_columns):
    """Strip common currency symbols and convert columns to float values."""
    df_typed = df.copy()

    for col in currency_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue
        try:
            cleaned = (
                df_typed[col]
                .astype("string")
                .str.replace(r"[$,]", "", regex=True)
                .str.strip()
            )
            df_typed[col] = pd.to_numeric(cleaned, errors="coerce").astype("float64")

            failed_conversions = (
                df_typed[col].isnull().sum() - df[col].isnull().sum()
            )
            if failed_conversions > 0:
                print(
                    f"Warning: {col}: {failed_conversions} values could not be converted"
                )
            print(f"- {col}: Stripped symbols, converted to float")
        except Exception as error:
            print(f"x {col}: Conversion failed - {error}")
            raise

    return df_typed


def convert_integers_to_boolean(df, boolean_columns):
    """Convert binary integer or common text representations to boolean values."""
    df_typed = df.copy()

    for col in boolean_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue
        try:
            unique_vals = df[col].unique()
            print(f"  {col} unique values: {unique_vals}")
            if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(
                df[col]
            ):
                mapping = {
                    "yes": True,
                    "no": False,
                    "y": True,
                    "n": False,
                    "true": True,
                    "false": False,
                    "1": True,
                    "0": False,
                    1: True,
                    0: False,
                    True: True,
                    False: False,
                }
                normalized = df_typed[col].map(
                    lambda value: value.strip().lower()
                    if isinstance(value, str)
                    else value
                )
                df_typed[col] = normalized.map(mapping).astype("boolean")
            else:
                df_typed[col] = df_typed[col].astype(bool)
            print(f"- {col}: Converted to boolean")
        except Exception as error:
            print(f"x {col}: Conversion failed - {error}")
            raise

    return df_typed


def compare_dtypes(df_original, df_typed, output_path=None):
    """Compare dtypes before and after conversion and save the summary."""
    comparison = pd.DataFrame(
        {
            "column": df_original.columns,
            "dtype_before": df_original.dtypes.values,
            "dtype_after": df_typed.dtypes.values,
            "changed": (df_original.dtypes != df_typed.dtypes).values,
        }
    )

    print("\n" + "=" * 70)
    print("DTYPE CONVERSION SUMMARY")
    print("=" * 70)
    print(comparison.to_string(index=False))

    if output_path is None:
        output_path = Path(__file__).resolve().parents[1] / "output" / "dtype_conversion_report.csv"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(output_path, index=False)
    print(f"\nReport saved to {output_path}")
    print("=" * 70)
    return comparison


def main():
    """Run the end-to-end type enforcement workflow."""
    project_root = Path(__file__).resolve().parents[1]
    raw_path = project_root / "data" / "raw" / "untyped_data.csv"
    processed_path = project_root / "data" / "processed" / "typed_data.csv"

    df = pd.read_csv(raw_path)
    print("=" * 70)
    print("BEFORE TYPE CONVERSION")
    print("=" * 70)
    print(df.dtypes)
    print("\nSample data:")
    print(df.head(3))

    print("\n1. Converting date columns...")
    df_typed = convert_string_dates_to_datetime(
        df, ["transaction_date", "signup_date"], date_format="%Y-%m-%d"
    )

    print("\n2. Converting currency columns...")
    df_typed = convert_currency_to_float(df_typed, ["amount", "revenue"])

    print("\n3. Converting boolean columns...")
    df_typed = convert_integers_to_boolean(df_typed, ["is_active", "is_premium"])
    df_typed, _ = cast_columns_to_types(df_typed, {"amount": "float64"})

    print("\n4. Comparing before/after types...")
    print("=" * 70)
    print("AFTER TYPE CONVERSION")
    print("=" * 70)
    print(df_typed.dtypes)
    print("\nSample data:")
    print(df_typed.head(3))

    compare_dtypes(df, df_typed)
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    df_typed.to_csv(processed_path, index=False)
    print(f"\n- Typed data saved to {processed_path}")


if __name__ == "__main__":
    main()