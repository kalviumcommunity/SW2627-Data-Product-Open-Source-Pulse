"""Pipeline orchestrator: GitHub exports -> contributor journey outputs."""

from pathlib import Path

import pandas as pd

from src.analytics.demo_data import build_demo_data
from src.analytics.review_timeline import issue_response_stats, review_iteration_count
from src.data_pipeline.loader import (
    load_commits,
    load_contributors,
    load_issues,
    load_pull_requests,
    load_reviews,
)
from src.data_pipeline.transformer import (
    build_contribution_history,
    compute_first_review_wait,
    compute_first_time_flags,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _journey_from_exports(contributors, pull_requests, issues, reviews, commits):
    pull_requests = compute_first_time_flags(pull_requests)
    wait = compute_first_review_wait(reviews, pull_requests)
    iterations = review_iteration_count(reviews, pd.DataFrame())
    first = pull_requests[pull_requests["is_first_pr"].eq(1)].copy()
    first = first.merge(wait, left_on="id", right_on="pr_id", how="left")
    first = first.merge(iterations[["pr_id", "review_iterations"]], left_on="id", right_on="pr_id", how="left")
    first["returned"] = 0
    history = build_contribution_history(pull_requests, commits, issues)
    for contributor_id, group in history.groupby("contributor_id"):
        first_time = first.loc[first["contributor_id"].eq(contributor_id), "created_at"]
        if first_time.empty:
            continue
        later = group[group["created_at"] > first_time.iloc[0]]
        first.loc[first["contributor_id"].eq(contributor_id), "returned"] = int(not later.empty)
    result = first.rename(columns={"created_at": "first_pr_created_at", "state": "first_pr_state", "is_merged": "first_pr_merged"})
    result["time_to_merge_days"] = (
        pd.to_datetime(result["merged_at"], errors="coerce", utc=True)
        - pd.to_datetime(result["first_pr_created_at"], errors="coerce", utc=True)
    ).dt.total_seconds() / 86400
    result["wait_bucket"] = pd.cut(
        result["first_review_wait_days"],
        bins=[-float("inf"), 2, 10, float("inf")],
        labels=["fast_le_2d", "medium_2_10d", "slow_gt_10d"],
    ).astype("object")
    result.loc[result["first_review_wait_days"].isna(), "wait_bucket"] = "no_review"
    result["unanswered_issue"] = 0
    issue_stats = issue_response_stats(issues, pd.DataFrame()) if not issues.empty else pd.DataFrame()
    if not issue_stats.empty:
        unanswered = issue_stats.groupby("contributor_id")["first_response_wait_days"].apply(lambda values: values.isna().any())
        result["unanswered_issue"] = result["contributor_id"].map(unanswered).fillna(False).astype(int)
    return result


def run_pipeline(raw_dir=None, output_dir=None):
    raw_path = Path(raw_dir) if raw_dir else PROJECT_ROOT / "data" / "raw"
    destination = Path(output_dir) if output_dir else PROJECT_ROOT / "output"
    contributors = load_contributors(raw_path / "contributors.csv")
    pull_requests = load_pull_requests(raw_path / "pull_requests.csv")
    issues = load_issues(raw_path / "issues.csv")
    reviews = load_reviews(raw_path / "reviews.csv")
    commits = load_commits(raw_path / "commits.csv")
    if pull_requests.empty or contributors.empty:
        demo = build_demo_data()
        journey = demo["journey"]
        contributors = demo["contributors"]
        pull_requests = demo["pull_requests"]
        issues = demo["issues"]
    else:
        journey = _journey_from_exports(contributors, pull_requests, issues, reviews, commits)
    destination.mkdir(parents=True, exist_ok=True)
    journey.to_csv(destination / "contributor_journey.csv", index=False)
    contributors.to_csv(destination / "contributors.csv", index=False)
    pull_requests.to_csv(destination / "pull_requests.csv", index=False)
    issues.to_csv(destination / "issues.csv", index=False)
    return journey
