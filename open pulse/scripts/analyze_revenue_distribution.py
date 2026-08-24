"""Analyze revenue distributions and translate statistics into business actions."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


def analyze_revenue(df, revenue_column="revenue"):
    """Calculate distribution statistics and high/low value segments."""
    revenue = df[revenue_column].dropna()
    skewness = float(stats.skew(revenue))
    kurtosis = float(stats.kurtosis(revenue))
    percentiles = revenue.quantile([0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
    high_value = df[df[revenue_column] > percentiles.loc[0.75]]
    low_value = df[df[revenue_column] < percentiles.loc[0.25]]

    statistics = {
        "count": int(revenue.count()),
        "mean": float(revenue.mean()),
        "median": float(revenue.median()),
        "min": float(revenue.min()),
        "max": float(revenue.max()),
        "skewness": skewness,
        "kurtosis": kurtosis,
        "percentiles": {str(key): float(value) for key, value in percentiles.items()},
        "high_value_count": int(len(high_value)),
        "low_value_count": int(len(low_value)),
        "high_value_mean": float(high_value[revenue_column].mean()),
        "high_value_median": float(high_value[revenue_column].median()),
        "low_value_mean": float(low_value[revenue_column].mean()),
        "low_value_median": float(low_value[revenue_column].median()),
    }
    return statistics, high_value, low_value


def plot_distributions(df, high_value, low_value, output_dir, revenue_column="revenue"):
    """Save overall and high/low segment distribution plots."""
    figure, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].hist(df[revenue_column].dropna(), bins=12, edgecolor="black")
    axes[0].set_title("Revenue Distribution (Histogram)")
    axes[0].set_xlabel("Revenue")
    axes[0].set_ylabel("Customers")
    df[revenue_column].plot(kind="density", ax=axes[1])
    axes[1].set_title("Revenue Distribution (KDE)")
    axes[1].set_xlabel("Revenue")
    figure.tight_layout()
    figure.savefig(output_dir / "revenue_distribution.png", dpi=150)
    plt.close(figure)

    segment_figure, segment_axes = plt.subplots(1, 2, figsize=(14, 5))
    segment_axes[0].hist(
        high_value[revenue_column], bins=8, alpha=0.7, label="High-Value"
    )
    segment_axes[0].hist(
        low_value[revenue_column], bins=8, alpha=0.7, label="Low-Value"
    )
    segment_axes[0].legend()
    segment_axes[0].set_title("Revenue: High vs Low Value Customers")
    segment_axes[0].set_xlabel("Revenue")
    segment_axes[0].set_ylabel("Customers")
    segment_axes[1].boxplot(
        [low_value[revenue_column], high_value[revenue_column]],
        tick_labels=["Low-Value", "High-Value"],
    )
    segment_axes[1].set_title("Segment Revenue Comparison")
    segment_axes[1].set_ylabel("Revenue")
    segment_figure.tight_layout()
    segment_figure.savefig(output_dir / "revenue_segment_distribution.png", dpi=150)
    plt.close(segment_figure)


def build_interpretation(statistics):
    """Return a business interpretation based on distribution shape."""
    skewness = statistics["skewness"]
    kurtosis = statistics["kurtosis"]
    skew_label = "Highly right-skewed" if skewness > 1 else "Moderate"
    shape = (
        "Most customers are small; few are huge enterprise accounts"
        if skewness > 1
        else "Balanced distribution"
    )
    tail_label = "Fat tails (outliers)" if kurtosis > 3 else "Normal"
    action = (
        "Segment into small/enterprise for different strategies"
        if skewness > 1
        else "Uniform strategy"
    )
    return (
        "Revenue Distribution Analysis:\n\n"
        f"Skewness: {skewness:.2f} -> {skew_label}\n"
        f"Mean: ${statistics['mean']:.0f}\n"
        f"Median: ${statistics['median']:.0f}\n"
        f"Interpretation: {shape}\n\n"
        f"Kurtosis: {kurtosis:.2f} -> {tail_label}\n"
        f"Max: ${statistics['max']:.0f}\n"
        f"Top 1%: ${statistics['percentiles']['0.99']:.0f}\n\n"
        f"Business Action: {action}"
    )


def main():
    """Run revenue distribution analysis and save all outputs."""
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(project_root / "data" / "raw" / "revenue_data.csv")
    statistics, high_value, low_value = analyze_revenue(df)

    print("REVENUE DISTRIBUTION ANALYSIS")
    print("=" * 60)
    print(f"Skewness: {statistics['skewness']:.2f}")
    print(f"Kurtosis: {statistics['kurtosis']:.2f}")
    if abs(statistics["skewness"]) > 1:
        print("Highly skewed - use median not mean")
    if statistics["kurtosis"] > 3:
        print("Heavy tails - expect outliers")
    print("\nRevenue description:")
    print(df["revenue"].describe())
    print("\nPercentiles:")
    print(pd.Series(statistics["percentiles"]))
    print(
        f"\nHigh-value: mean={statistics['high_value_mean']:.0f}, "
        f"median={statistics['high_value_median']:.0f}"
    )
    print(
        f"Low-value: mean={statistics['low_value_mean']:.0f}, "
        f"median={statistics['low_value_median']:.0f}"
    )
    interpretation = build_interpretation(statistics)
    print(f"\n{interpretation}")

    plot_distributions(df, high_value, low_value, output_dir)
    with (output_dir / "revenue_distribution_analysis.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            {"statistics": statistics, "interpretation": interpretation},
            file,
            indent=2,
        )
    print(f"\nAnalysis outputs saved to {output_dir}")


if __name__ == "__main__":
    main()