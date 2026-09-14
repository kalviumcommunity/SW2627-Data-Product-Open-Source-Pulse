import argparse
import logging
from pathlib import Path

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def _first_column(df, names, required=True):
    for name in names:
        if name in df.columns:
            return name
    if required:
        raise ValueError(f"Missing required column. Expected one of: {', '.join(names)}")
    return None


def ingest(path):
    logger.info("Ingesting: %s", path)
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    df = pd.read_csv(source)
    logger.info("Rows ingested: %s", len(df))
    return df


def clean(df):
    logger.info("Cleaning data")
    initial = len(df)
    customer_column = _first_column(df, ["customer_id", "id"])
    amount_column = _first_column(df, ["amount", "transaction_amount", "revenue"])
    segment_column = _first_column(df, ["segment", "customer_type"], required=False)

    cleaned = df.dropna(subset=[customer_column]).copy()
    cleaned["amount"] = pd.to_numeric(cleaned[amount_column], errors="coerce")
    cleaned = cleaned.dropna(subset=["amount"])
    cleaned = cleaned[cleaned["amount"] > 0].copy()
    if segment_column:
        cleaned["segment"] = cleaned[segment_column].fillna("Unknown").astype(str)
    else:
        cleaned["segment"] = "All"
    logger.info("Cleaned rows: %s -> %s", initial, len(cleaned))
    return cleaned


def aggregate(df):
    logger.info("Aggregating data")
    order_column = _first_column(
        df,
        ["order_id", "transaction_id", "id", "customer_id"],
    )
    aggregated = (
        df.groupby("segment", dropna=False)
        .agg(
            revenue=("amount", "sum"),
            orders=(order_column, "count"),
        )
        .reset_index()
    )
    logger.info("Segments aggregated: %s", len(aggregated))
    return aggregated


def output(cleaned, aggregated, output_dir):
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(destination / "cleaned.csv", index=False)
    aggregated.to_csv(destination / "aggregated.csv", index=False)
    logger.info("Pipeline complete. Output written to: %s", destination)


def main():
    parser = argparse.ArgumentParser(description="Run the Open Pulse data pipeline")
    parser.add_argument("--input", default="data/raw/segment_data.csv")
    parser.add_argument("--output", default="output")
    args = parser.parse_args()

    raw = ingest(args.input)
    cleaned = clean(raw)
    aggregated = aggregate(cleaned)
    output(cleaned, aggregated, args.output)


if __name__ == "__main__":
    main()