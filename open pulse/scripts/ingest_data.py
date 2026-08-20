"""Ingest CSV and JSON files with auditable loading summaries."""

from pathlib import Path

import pandas as pd


def ingest_csv(filepath, delimiter=',', encoding='utf-8', dtype_dict=None):
    """
    Load a CSV file with explicit parsing parameters.

    Args:
        filepath: Path to the CSV file.
        delimiter: Field delimiter, such as comma, semicolon, or tab.
        encoding: File encoding, normally UTF-8, latin-1, or cp1252.
        dtype_dict: Optional mapping of column names to pandas data types.

    Returns:
        A pandas DataFrame containing the loaded rows and columns.
    """
    try:
        df = pd.read_csv(
            filepath,
            delimiter=delimiter,
            encoding=encoding,
            dtype=dtype_dict,
        )
        print(f"CSV loaded: {filepath}")
        print(f"  Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        print(f"  Columns: {list(df.columns)}")
        return df
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        raise
    except UnicodeDecodeError:
        print(f"Encoding error: Could not decode with {encoding}")
        print("Try: latin-1, iso-8859-1, or cp1252")
        raise


def ingest_json(filepath, is_nested=False):
    """
    Load JSON data, optionally flattening nested objects into columns.

    Args:
        filepath: Path to a JSON file containing records.
        is_nested: Flatten nested objects using dot-separated column names.

    Returns:
        A pandas DataFrame with nested structures expanded when requested.
    """
    try:
        df = pd.read_json(filepath)
        if is_nested:
            df = pd.json_normalize(df.to_dict(orient='records'))
            print("Nested JSON flattened to tabular format")

        print(f"JSON loaded: {filepath}")
        print(f"  Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        return df
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        raise


def ingest_csv_with_fallback(filepath, delimiters=None, fallback_encodings=None):
    """Load a CSV by trying each delimiter and encoding combination."""
    if delimiters is None:
        delimiters = [',']
    if fallback_encodings is None:
        fallback_encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

    for delimiter in delimiters:
        for encoding in fallback_encodings:
            try:
                df = pd.read_csv(filepath, delimiter=delimiter, encoding=encoding)
                print(
                    f"Successfully loaded with delimiter={delimiter!r}, "
                    f"encoding={encoding!r}"
                )
                return df
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue

    raise ValueError(
        f"Could not load {filepath} with any encoding/delimiter combination"
    )


def document_ingestion(df, source_file):
    """Print a detailed ingestion report suitable for an audit trail."""
    print(f"\n{'=' * 60}")
    print(f"INGESTION REPORT: {source_file}")
    print(f"{'=' * 60}")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")
    print("\nColumn Names & Data Types:")
    print(df.dtypes)
    print("\nNull Values Per Column:")
    print(df.isnull().sum())
    print("\nFirst 3 Rows:")
    print(df.head(3).to_string())
    print(f"{'=' * 60}\n")
    return df


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    print("Starting multi-format ingestion...\n")

    csv_df = ingest_csv(
        raw_dir / "customers.csv",
        delimiter=',',
        encoding='utf-8',
        dtype_dict={'customer_id': 'int64', 'name': 'string', 'email': 'string'},
    )
    document_ingestion(csv_df, "customers.csv")

    json_df = ingest_json(raw_dir / "transactions.json", is_nested=True)
    document_ingestion(json_df, "transactions.json")

    csv_df.to_csv(processed_dir / "customers_ingested.csv", index=False)
    json_df.to_csv(processed_dir / "transactions_ingested.csv", index=False)
    print("All data ingested and saved to processed/")