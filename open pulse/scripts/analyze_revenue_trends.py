"""Analyze daily revenue trends with resampling and rolling windows."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def prepare_time_series(df):
    """Parse dates, sort records, and add rolling and cumulative measures."""
    df_ts = df.copy()
    df_ts["date"] = pd.to_datetime(df_ts["date"], format="%Y-%m-%d")
    df_ts = df_ts.sort_values("date").set_index("date")
    df_ts["revenue_ma7"] = df_ts["revenue"].rolling(window=7, min_periods=1).mean()
    df_ts["revenue_ma30"] = df_ts["revenue"].rolling(window=30, min_periods=1).mean()
    df_ts["cumulative_revenue"] = df_ts["revenue"].cumsum()
    return df_ts


def calculate_period_metrics(df_ts):
    """Return weekly and monthly revenue sum, order count, and average."""
    aggregations = {"revenue": ["sum", "count", "mean"]}
    weekly = df_ts.resample("W").agg(aggregations)
    monthly = df_ts.resample("MS").agg(aggregations)
    weekly.columns = ["revenue_sum", "order_count", "revenue_mean"]
    monthly.columns = ["revenue_sum", "order_count", "revenue_mean"]
    return weekly, monthly


def calculate_monthly_change(monthly):
    """Calculate percentage changes and split months into growth and decline."""
    monthly = monthly.copy()
    monthly["mom_change_pct"] = monthly["revenue_sum"].pct_change() * 100
    growth_months = monthly[monthly["mom_change_pct"] > 0]
    decline_months = monthly[monthly["mom_change_pct"] < 0]
    return monthly, growth_months, decline_months


def classify_trend(df_ts):
    """Classify the recent 30-day rolling-average direction and magnitude."""
    recent_ma30 = df_ts["revenue_ma30"].dropna().tail(30)
    start_value = recent_ma30.iloc[0]
    end_value = recent_ma30.iloc[-1]
    magnitude = (end_value - start_value) / start_value * 100 if start_value else 0
    if abs(magnitude) < 1:
        direction = "flat"
    else:
        direction = "up" if magnitude > 0 else "down"
    return direction, float(magnitude)


def save_plots(df_ts, output_dir):
    """Save rolling-average and cumulative-revenue visualizations."""
    figure, axis = plt.subplots(figsize=(12, 6))
    axis.plot(df_ts.index, df_ts["revenue"], label="Raw", alpha=0.3)
    axis.plot(df_ts.index, df_ts["revenue_ma7"], label="7-day MA")
    axis.plot(df_ts.index, df_ts["revenue_ma30"], label="30-day MA")
    axis.set_title("Revenue with 7-day and 30-day Rolling Averages")
    axis.set_xlabel("Date")
    axis.set_ylabel("Revenue")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "rolling_revenue_averages.png", dpi=150)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(12, 6))
    axis.plot(df_ts.index, df_ts["cumulative_revenue"])
    axis.set_title("Cumulative Revenue Over Time")
    axis.set_xlabel("Date")
    axis.set_ylabel("Cumulative revenue")
    figure.tight_layout()
    figure.savefig(output_dir / "cumulative_revenue.png", dpi=150)
    plt.close(figure)


def main():
    """Run the complete revenue trend analysis."""
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(project_root / "data" / "raw" / "daily_revenue.csv")
    df_ts = prepare_time_series(df)
    weekly, monthly = calculate_period_metrics(df_ts)
    monthly, growth_months, decline_months = calculate_monthly_change(monthly)
    trend_direction, trend_magnitude = classify_trend(df_ts)

    print("WEEKLY METRICS")
    print(weekly)
    print("\nMONTHLY METRICS AND MOM CHANGE")
    print(monthly)
    print("\nGrowth months:")
    print(growth_months[["revenue_sum", "mom_change_pct"]])
    print("\nDecline months:")
    print(decline_months[["revenue_sum", "mom_change_pct"]])
    print(f"\nHighest revenue week: {weekly['revenue_sum'].idxmax().date()}")
    print(f"Trend direction: {trend_direction.upper()}")
    print(f"Trend magnitude over recent 30 days: {trend_magnitude:.1f}%")
    print(f"Total revenue: ${df_ts['cumulative_revenue'].iloc[-1]:,.0f}")

    implication = (
        "Accelerating growth - maintain current strategy"
        if trend_direction == "up"
        else "Declining momentum - investigate causes"
        if trend_direction == "down"
        else "Stable revenue - maintain strategy and monitor leading indicators"
    )
    analysis = (
        f"TREND ANALYSIS:\n\nRolling Average Trend: {trend_direction.upper()}\n"
        f"Change over last 30 days: {trend_magnitude:.1f}%\n\n"
        f"Month-over-month growth: {monthly['mom_change_pct'].iloc[-1]:.1f}%\n\n"
        f"Business Implications:\n- {implication}\n"
        f"- Revenue volatility: ${df_ts['revenue'].std():.0f} (measure of noise)\n"
        f"Action: Use the smoothed trend to plan capacity and investigate daily anomalies."
    )
    print(f"\n{analysis}")

    df_ts.to_csv(output_dir / "revenue_trend_features.csv")
    weekly.to_csv(output_dir / "weekly_revenue_metrics.csv")
    monthly.to_csv(output_dir / "monthly_revenue_metrics.csv")
    save_plots(df_ts, output_dir)
    with (output_dir / "revenue_trend_analysis.json").open("w", encoding="utf-8") as file:
        json.dump(
            {
                "trend_direction": trend_direction,
                "trend_magnitude_pct": round(trend_magnitude, 2),
                "total_revenue": float(df_ts["cumulative_revenue"].iloc[-1]),
                "growth_months": [str(index.date()) for index in growth_months.index],
                "decline_months": [str(index.date()) for index in decline_months.index],
                "highest_revenue_week": str(weekly["revenue_sum"].idxmax().date()),
                "business_analysis": analysis,
            },
            file,
            indent=2,
        )


if __name__ == "__main__":
    main()