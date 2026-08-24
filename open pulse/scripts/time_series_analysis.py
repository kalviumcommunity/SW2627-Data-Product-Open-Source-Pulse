"""Create temporal features and time-indexed transaction summaries."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_timestamps(df, date_column="transaction_date"):
    """Parse timestamps using the documented, unambiguous input format."""
    df_features = df.copy()
    df_features[date_column] = pd.to_datetime(
        df_features[date_column], format=TIMESTAMP_FORMAT
    )
    if not pd.api.types.is_datetime64_any_dtype(df_features[date_column]):
        raise TypeError(f"{date_column} was not converted to datetime")
    print(f"{date_column} dtype: {df_features[date_column].dtype}")
    return df_features


def add_temporal_features(df, date_column="transaction_date"):
    """Add day, hour, ISO week, and customer purchase-recency features."""
    df_features = df.copy()
    timestamp = df_features[date_column]
    df_features["day_of_week"] = timestamp.dt.day_name()
    df_features["hour"] = timestamp.dt.hour
    df_features["week_num"] = timestamp.dt.isocalendar().week.astype("int64")

    customer_last_purchase = df_features.groupby("customer_id")[date_column].transform(
        "max"
    )
    today = pd.Timestamp.now()
    df_features["days_since_last_purchase"] = (
        today - customer_last_purchase
    ).dt.days
    return df_features


def create_weekly_metrics(df, date_column="transaction_date"):
    """Resample amount into weekly sum, count, and mean metrics."""
    time_indexed = df.set_index(date_column).sort_index()
    weekly_metrics = time_indexed["amount"].resample("W").agg(
        revenue_sum="sum", transaction_count="count", average_amount="mean"
    )
    return weekly_metrics


def create_time_indexed_aggregations(df):
    """Create day/hour aggregations and an hour by weekday revenue pivot."""
    hourly_daily = df.groupby(["day_of_week", "hour"], sort=False)["amount"].agg(
        ["sum", "count", "mean"]
    )
    pivot_table = pd.pivot_table(
        df,
        values="amount",
        index="hour",
        columns="day_of_week",
        aggfunc="sum",
    )
    return hourly_daily, pivot_table


def identify_peak_windows(hourly_daily, top_n=3):
    """Return the busiest day/hour windows by transaction count and amount."""
    peak_windows = hourly_daily.sort_values(
        ["count", "sum"], ascending=False
    ).head(top_n)
    return peak_windows.reset_index()


def save_outputs(df, weekly_metrics, hourly_daily, pivot_table, peak_windows, output_dir):
    """Save feature data and analysis artifacts for review."""
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_dir / "temporal_features.csv", index=False)
    weekly_metrics.to_csv(output_dir / "weekly_metrics.csv")
    hourly_daily.to_csv(output_dir / "hourly_daily_aggregations.csv")
    pivot_table.to_csv(output_dir / "hour_day_revenue_pivot.csv")
    peak_windows.to_csv(output_dir / "peak_activity_windows.csv", index=False)

    recency = df["days_since_last_purchase"].describe().to_dict()
    with (output_dir / "temporal_analysis_summary.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            {
                "timestamp_format": TIMESTAMP_FORMAT,
                "min_date": str(df["transaction_date"].min()),
                "max_date": str(df["transaction_date"].max()),
                "days_in_dataset": int(
                    (df["transaction_date"].max() - df["transaction_date"].min()).days
                ),
                "hours_with_data": sorted(df["hour"].unique().tolist()),
                "weeks_in_dataset": int(df["week_num"].nunique()),
                "recency_distribution": recency,
                "customers_without_recent_activity": int(
                    (df["days_since_last_purchase"] > 30).sum()
                ),
            },
            file,
            indent=2,
            default=str,
        )


def plot_hour_distribution(df, output_path):
    """Save a histogram of transaction volume by hour of day."""
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.hist(df["hour"], bins=np.arange(-0.5, 24.5, 1), edgecolor="white")
    axis.set_title("Transaction Volume by Hour")
    axis.set_xlabel("Hour of day")
    axis.set_ylabel("Transactions")
    axis.set_xticks(range(24))
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def main():
    """Run temporal feature extraction and save analysis outputs."""
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "output"
    df = pd.read_csv(project_root / "data" / "raw" / "temporal_data.csv")

    print("=" * 70)
    print(f"PARSING TRANSACTION TIMESTAMPS WITH FORMAT: {TIMESTAMP_FORMAT}")
    print("=" * 70)
    df = parse_timestamps(df)
    df = add_temporal_features(df)

    print("\nTEMPORAL VALIDATION")
    print(f"Min date: {df['transaction_date'].min()}")
    print(f"Max date: {df['transaction_date'].max()}")
    print(
        f"Days in dataset: "
        f"{(df['transaction_date'].max() - df['transaction_date'].min()).days}"
    )
    print(f"Hours with data: {sorted(df['hour'].unique().tolist())}")
    print(f"Weeks in dataset: {df['week_num'].nunique()}")
    print("\nHourly volume:")
    print(df.groupby("hour").size())
    print("\nRecency distribution:")
    print(df["days_since_last_purchase"].describe())
    print(
        "Customers without recent activity (>30 days): "
        f"{(df['days_since_last_purchase'] > 30).sum()}"
    )

    weekly_metrics = create_weekly_metrics(df)
    hourly_daily, pivot_table = create_time_indexed_aggregations(df)
    peak_windows = identify_peak_windows(hourly_daily)
    print("\nWeekly metrics:")
    print(weekly_metrics)
    print("\nHour x day-of-week revenue pivot:")
    print(pivot_table)
    print("\nPeak activity windows:")
    print(peak_windows.to_string(index=False))

    save_outputs(
        df, weekly_metrics, hourly_daily, pivot_table, peak_windows, output_dir
    )
    plot_hour_distribution(df, output_dir / "hour_distribution.png")
    print(f"\nAnalysis outputs saved to {output_dir}")


if __name__ == "__main__":
    main()