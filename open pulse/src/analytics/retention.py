"""Return/retention behavior analysis."""

import pandas as pd


def returned_flag(journey_df):
    result = journey_df.copy()
    result["returned"] = result["returned"].fillna(0).astype(int) if "returned" in result else 0
    return result


def retention_by_first_experience(journey_df):
    factors = ["wait_bucket", "first_pr_state", "first_pr_merged", "review_iterations", "unanswered_issue"]
    available = [factor for factor in factors if factor in journey_df]
    pieces = []
    for factor in available:
        summary = journey_df.groupby(factor, dropna=False).agg(
            contributors=("contributor_id", "nunique"),
            returned=("returned", "sum"),
        ).reset_index()
        summary["return_rate"] = summary["returned"] / summary["contributors"]
        summary["factor"] = factor
        summary = summary.rename(columns={factor: "value"})
        pieces.append(summary[["factor", "value", "contributors", "returned", "return_rate"]])
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def churn_risk_flags(journey_df, thresholds=None):
    limits = thresholds or {"slow_review_days": 10, "high_iterations": 3}
    result = journey_df.copy()
    wait = pd.Series(pd.to_numeric(result.get("first_review_wait_days"), errors="coerce"), index=result.index)
    iterations = pd.Series(pd.to_numeric(result.get("review_iterations", 0), errors="coerce"), index=result.index).fillna(0)
    result["risk_reasons"] = ""
    slow_mask = wait.gt(limits["slow_review_days"])
    iteration_mask = iterations.ge(limits["high_iterations"])
    result.loc[slow_mask, "risk_reasons"] = result.loc[slow_mask, "risk_reasons"] + "long_first_review;"
    result.loc[iteration_mask, "risk_reasons"] = result.loc[iteration_mask, "risk_reasons"] + "high_review_iterations;"
    if "unanswered_issue" in result:
        issue_mask = result["unanswered_issue"].fillna(0).astype(bool)
        result.loc[issue_mask, "risk_reasons"] = result.loc[issue_mask, "risk_reasons"] + "unanswered_issue;"
    result["risk_level"] = "low"
    result.loc[result["risk_reasons"].str.count(";") == 1, "risk_level"] = "medium"
    result.loc[result["risk_reasons"].str.count(";") >= 2, "risk_level"] = "high"
    return result
