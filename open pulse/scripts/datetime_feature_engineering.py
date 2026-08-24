"""Parse transaction timestamps for datetime feature engineering."""

from pathlib import Path

import pandas as pd


# The input data must use this unambiguous timestamp format.
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_transaction_dates(df, column="transaction_date"):
    """Convert timestamp strings to datetime using the explicit input format."""
    df_features = df.copy()
    df_features[column] = pd.to_datetime(
        df_features[column], format=TIMESTAMP_FORMAT
    )

    if not pd.api.types.is_datetime64_any_dtype(df_features[column]):
        raise TypeError(f"{column} is not a datetime column after conversion")

    print(f"{column} dtype: {df_features[column].dtype}")
    return df_features


def build_datetime_pipeline(input_path, output_path):
    """Load transactions, parse timestamps, verify them, and save the result."""
    df = pd.read_csv(input_path)
    df_features = parse_transaction_dates(df)

    print(f"Min date: {df_features['transaction_date'].min()}")
    print(f"Max date: {df_features['transaction_date'].max()}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_csv(output_path, index=False)
    print(f"Typed transaction data saved to {output_path}")
    return df_features


def main():
    """Run the datetime parsing pipeline for the sample transaction data."""
    project_root = Path(__file__).resolve().parents[1]
    build_datetime_pipeline(
        project_root / "data" / "raw" / "temporal_data.csv",
        project_root / "data" / "processed" / "datetime_features.csv",
    )


if __name__ == "__main__":
    main()