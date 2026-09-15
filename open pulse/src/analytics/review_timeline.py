"""Review-timeline and issue-participation metrics."""

import pandas as pd


def review_wait_stats(journey_df):
    waits = pd.to_numeric(journey_df["first_review_wait_days"], errors="coerce").dropna()
    if waits.empty:
        return {"count": 0, "mean_days": None, "median_days": None, "p90_days": None}
    return {
        "count": int(waits.size),
        "mean_days": float(waits.mean()),
        "median_days": float(waits.median()),
        "p90_days": float(waits.quantile(0.9)),
    }


def review_iteration_count(reviews, review_comments):
    counts = reviews.groupby("pr_id").size().rename("review_iterations").reset_index()
    if review_comments.empty:
        counts["review_comments"] = 0
        return counts
    comments = review_comments.groupby("pr_id").size().rename("review_comments").reset_index()
    return counts.merge(comments, on="pr_id", how="outer").fillna(0)


def issue_response_stats(issues, issue_comments):
    result = issues.copy()
    result["created_at"] = pd.to_datetime(result["created_at"], errors="coerce", utc=True)
    if "first_response_at" in result:
        response = pd.to_datetime(result["first_response_at"], errors="coerce", utc=True)
    else:
        response = pd.Series(pd.NaT, index=result.index, dtype="datetime64[ns, UTC]")
    result["first_response_wait_days"] = (response - result["created_at"]).dt.total_seconds() / 86400
    if issue_comments.empty:
        result["maintainer_replies"] = 0
    else:
        result["maintainer_replies"] = issue_comments.groupby("issue_id").size().reindex(result["id"]).fillna(0).to_numpy()
    result["resolution_days"] = (
        pd.to_datetime(result.get("closed_at"), errors="coerce", utc=True) - result["created_at"]
    ).dt.total_seconds() / 86400
    return result
