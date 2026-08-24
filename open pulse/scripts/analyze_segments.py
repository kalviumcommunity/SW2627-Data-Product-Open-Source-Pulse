"""Aggregate customer segments and surface actionable performance insights."""

import json
from pathlib import Path

import pandas as pd


def compute_segment_metrics(df):
    """Compute churn, revenue, customer count, and support metrics by segment."""
    segment_metrics = df.groupby("customer_type").agg(
        churn_rate=("churn", "mean"),
        total_revenue=("revenue", "sum"),
        customer_count=("customer_id", "count"),
        avg_support_tickets=("support_tickets", "mean"),
    )
    segment_metrics["churn_rank"] = segment_metrics["churn_rate"].rank(
        ascending=False, method="min"
    )
    segment_metrics["revenue_contribution"] = (
        segment_metrics["total_revenue"]
        / segment_metrics["total_revenue"].sum()
        * 100
    )
    return segment_metrics


def compute_product_segment_metrics(df):
    """Compute revenue and customer counts by customer type and product."""
    product_segment = df.groupby(["customer_type", "product"]).agg(
        total_revenue=("revenue", "sum"),
        customer_count=("customer_id", "count"),
    )
    return product_segment, product_segment.unstack(fill_value=0)


def create_revenue_pivot(df):
    """Create a customer-type by product revenue pivot table."""
    return pd.pivot_table(
        df,
        values="revenue",
        index="customer_type",
        columns="product",
        aggfunc="sum",
        fill_value=0,
    )


def create_segment_insights(segment_metrics):
    """Translate segment metrics into threshold-based business actions."""
    insights = []
    for segment, row in segment_metrics.iterrows():
        if row["churn_rate"] > 0.10:
            action = "HIGH PRIORITY: Churn above 10%. Investigate pain points."
        elif row["churn_rate"] < 0.02:
            action = "Healthy. Maintain current service level."
        else:
            action = "Monitor. No immediate action needed."
        insights.append(
            {
                "segment": segment,
                "customer_count": int(row["customer_count"]),
                "churn_rate": f"{row['churn_rate']:.1%}",
                "total_revenue": f"${row['total_revenue']:.0f}",
                "revenue_contribution": f"{row['revenue_contribution']:.1f}%",
                "action": action,
            }
        )
    return pd.DataFrame(insights)


def main():
    """Run segment aggregation and save analysis outputs."""
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(project_root / "data" / "raw" / "segment_data.csv")

    segment_metrics = compute_segment_metrics(df)
    product_segment, product_segment_pivot = compute_product_segment_metrics(df)
    revenue_pivot = create_revenue_pivot(df)
    worst_first = segment_metrics.sort_values("churn_rate", ascending=False)
    insights_df = create_segment_insights(segment_metrics)

    print("SEGMENT METRICS")
    print("=" * 70)
    print(segment_metrics)
    print("\nPRODUCT SEGMENT METRICS")
    print(product_segment)
    print("\nPRODUCT SEGMENT PIVOT")
    print(product_segment_pivot)
    print("\nREVENUE PIVOT")
    print(revenue_pivot)
    print("\nWORST SEGMENTS FIRST")
    print(worst_first)
    print("\nACTIONABLE SEGMENT INSIGHTS")
    print(insights_df.to_string(index=False))

    segment_metrics.to_csv(output_dir / "segment_metrics.csv")
    product_segment.to_csv(output_dir / "product_segment_metrics.csv")
    product_segment_pivot.to_csv(output_dir / "product_segment_pivot.csv")
    revenue_pivot.to_csv(output_dir / "segment_product_revenue_pivot.csv")
    insights_df.to_csv(output_dir / "segment_insights.csv", index=False)
    with (output_dir / "segment_analysis_summary.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            {
                "worst_segment": str(worst_first.index[0]),
                "best_revenue_segment": str(
                    segment_metrics["total_revenue"].idxmax()
                ),
                "segment_count": len(segment_metrics),
                "actions": insights_df.to_dict(orient="records"),
            },
            file,
            indent=2,
        )


if __name__ == "__main__":
    main()