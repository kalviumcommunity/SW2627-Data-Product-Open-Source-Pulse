"""
Data Workflow Pipeline

Complete data pipeline from ingestion to output with separated concerns.
Run: python scripts/data_workflow.py
"""

import pandas as pd
import os


def ingest_data(filepath):
    """
    Load data from a CSV file and return a Pandas DataFrame.

    Input: File path to a CSV file
    Output: Pandas DataFrame containing the raw data
    Assumptions: File exists and is valid CSV format
    """
    df = pd.read_csv(filepath)
    print(f">> Ingested {len(df)} rows from {filepath}")
    return df


def process_data(df):
    """
    Transform raw data into analysis-ready format.

    Input: Pandas DataFrame with raw data
    Output: Pandas DataFrame with nulls filled, duplicates removed
    Assumptions: Input DataFrame has expected columns
    """
    initial_rows = len(df)
    df = df.drop_duplicates()
    duplicates_removed = initial_rows - len(df)
    if duplicates_removed > 0:
        print(f">> Removed {duplicates_removed} duplicate rows")

    for col in df.select_dtypes(include=['number']).columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            print(f">> Filled {null_count} nulls in '{col}' with median ({median_val})")

    return df


def output_results(df, output_path):
    """
    Save processed data to a CSV file and print confirmation.

    Input: Pandas DataFrame to save, output file path
    Output: CSV file written to disk
    Assumptions: Output directory exists
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f">> Data successfully processed")
    print(f">> Rows processed: {len(df)}")
    print(f">> Output saved to {output_path}")


if __name__ == "__main__":
    data = ingest_data("data/raw/sample.csv")
    processed = process_data(data)
    output_results(processed, "output/processed.csv")
