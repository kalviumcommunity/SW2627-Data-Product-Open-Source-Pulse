"""Transform raw DataFrames into the analytics schema."""

import pandas as pd


def clean_datetime(df, columns):
    result = df.copy()
    for column in columns:
        if column in result:
            result[column] = pd.to_datetime(result[column], errors="coerce", utc=True)
    return result


def compute_first_time_flags(pull_requests):
    result = clean_datetime(pull_requests, ["created_at"])
    if result.empty:
        result["is_first_pr"] = pd.Series(dtype="int64")
        return result
    result = result.sort_values(["contributor_id", "created_at", "id"])
    result["is_first_pr"] = (~result.duplicated("contributor_id")).astype(int)
    return result.sort_index()


def compute_first_review_wait(reviews, pull_requests):
    prs = clean_datetime(pull_requests, ["created_at"])[["id", "created_at"]].rename(
        columns={"id": "pr_id", "created_at": "pr_created_at"}
    )
    first_reviews = clean_datetime(reviews, ["created_at"]).groupby("pr_id", as_index=False).agg(
        first_review_at=("created_at", "min"),
        review_count=("id", "count"),
    )
    result = prs.merge(first_reviews, on="pr_id", how="left")
    result["first_review_wait_days"] = (
        result["first_review_at"] - result["pr_created_at"]
    ).dt.total_seconds() / 86400
    return result


def build_contribution_history(pull_requests, commits, issues):
    frames = []
    if not pull_requests.empty:
        frames.append(pd.DataFrame({
            "contributor_id": pull_requests["contributor_id"],
            "pr_id": pull_requests["id"],
            "created_at": pull_requests["created_at"],
            "contribution_type": "pull_request",
        }))
    if not commits.empty:
        frames.append(pd.DataFrame({
            "contributor_id": commits["contributor_id"],
            "pr_id": commits.get("pr_id"),
            "created_at": commits["committed_at"],
            "contribution_type": "commit",
        }))
    if not issues.empty and "contributor_id" in issues:
        frames.append(pd.DataFrame({
            "contributor_id": issues["contributor_id"],
            "pr_id": None,
            "created_at": issues["created_at"],
            "contribution_type": "issue",
        }))
    if not frames:
        return pd.DataFrame(columns=["contributor_id", "pr_id", "created_at", "contribution_type"])
    result = pd.concat(frames, ignore_index=True)
    result["created_at"] = pd.to_datetime(result["created_at"], errors="coerce", utc=True)
    return result.sort_values(["contributor_id", "created_at"]).reset_index(drop=True)


def bucket_wait_times(journey, thresholds=None):
    limits = thresholds or {"fast": 2, "slow": 10}
    result = journey.copy()
    wait = result["first_review_wait_days"]
    result["wait_bucket"] = pd.cut(
        wait,
        bins=[-float("inf"), limits["fast"], limits["slow"], float("inf")],
        labels=["fast_le_2d", "medium_2_10d", "slow_gt_10d"],
    ).astype("object")
    result.loc[wait.isna(), "wait_bucket"] = "no_review"
    return result
