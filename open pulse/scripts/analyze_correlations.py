"""Analyze feature correlations and document modeling decisions."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def compute_correlations(df):
    """Return Pearson, Spearman, and churn-correlation comparison matrices."""
    numeric_df = df.select_dtypes(include="number").drop(
        columns=["customer_id"], errors="ignore"
    )
    pearson_corr = numeric_df.corr(method="pearson")
    spearman_corr = numeric_df.corr(method="spearman")
    comparison = pd.DataFrame(
        {
            "pearson": pearson_corr["churn"],
            "spearman": spearman_corr["churn"],
        }
    )
    return pearson_corr, spearman_corr, comparison


def find_strong_pairs(correlation_matrix, threshold=0.7, limit=10):
    """Find unique non-self feature pairs above the absolute threshold."""
    pairs = []
    columns = correlation_matrix.columns
    for left_index, left_column in enumerate(columns):
        for right_column in columns[left_index + 1 :]:
            value = float(correlation_matrix.loc[left_column, right_column])
            if abs(value) > threshold:
                pairs.append(
                    {"feature_1": left_column, "feature_2": right_column, "correlation": value}
                )
    return pd.DataFrame(pairs).sort_values(
        "correlation", key=lambda values: values.abs(), ascending=False
    ).head(limit)


def build_business_analysis(strong_pairs):
    """Explain correlation risks and actions without claiming causation."""
    analysis = {
        "support_tickets <-> churn": {
            "correlation": None,
            "possible_directions": [
                "support_tickets -> churn (customer gives up after contacting support)",
                "churn -> support_tickets (unhappy customers contact support before leaving)",
                "customer_pain -> both (underlying issue causes both)",
            ],
            "data_indicates": "Correlation alone cannot establish direction; customer pain may confound both measures",
            "action": "Focus on reducing customer pain and test the relationship with time-ordered experiments",
        }
    }
    ticket_pair = strong_pairs[
        (strong_pairs["feature_1"] == "support_tickets")
        & (strong_pairs["feature_2"] == "churn")
        | (strong_pairs["feature_1"] == "churn")
        & (strong_pairs["feature_2"] == "support_tickets")
    ]
    if not ticket_pair.empty:
        analysis["support_tickets <-> churn"]["correlation"] = float(
            ticket_pair.iloc[0]["correlation"]
        )
    return analysis


def main():
    """Run correlation analysis and save reports and visualizations."""
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(project_root / "data" / "raw" / "correlation_data.csv")

    pearson_corr, spearman_corr, comparison = compute_correlations(df)
    print("PEARSON CORRELATION WITH CHURN")
    print(comparison)
    strong_pairs = find_strong_pairs(pearson_corr)
    print("\nSTRONGLY CORRELATED PAIRS")
    print(strong_pairs.to_string(index=False))

    figure, axis = plt.subplots(figsize=(12, 10))
    sns.heatmap(pearson_corr, annot=True, cmap="coolwarm", center=0, ax=axis)
    axis.set_title("Feature Correlation Matrix")
    figure.tight_layout()
    figure.savefig(output_dir / "correlation_heatmap.png", dpi=150)
    plt.close(figure)

    selected_columns = [
        column
        for column in [
            "transactions_per_month",
            "support_tickets",
            "churn",
        ]
        if column in df.columns
    ]
    selected_features = df[selected_columns]
    print("\nSELECTED FEATURES")
    print(selected_features.corr())

    business_analysis = build_business_analysis(strong_pairs)
    print("\nBUSINESS INTERPRETATION")
    print(json.dumps(business_analysis, indent=2))
    pearson_corr.to_csv(output_dir / "pearson_correlations.csv")
    spearman_corr.to_csv(output_dir / "spearman_correlations.csv")
    comparison.to_csv(output_dir / "churn_correlation_comparison.csv")
    strong_pairs.to_csv(output_dir / "strong_correlation_pairs.csv", index=False)
    selected_features.to_csv(output_dir / "selected_correlation_features.csv", index=False)
    with (output_dir / "correlation_business_analysis.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(business_analysis, file, indent=2)


if __name__ == "__main__":
    main()