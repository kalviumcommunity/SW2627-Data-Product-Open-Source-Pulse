"""Deterministic contributor-retention data for local development."""

import pandas as pd


def build_demo_data(count=30):
    contributors = []
    pull_requests = []
    issues = []
    for index in range(1, count + 1):
        created = pd.Timestamp("2026-01-01") + pd.Timedelta(days=index)
        wait_days = [1, 3, 5, 12, 18][index % 5]
        iterations = [1, 1, 2, 4, 5][index % 5]
        merged = int(index % 6 not in (0, 1))
        returned = int(wait_days <= 5 and iterations <= 2 and merged == 1)
        contributor_id = index
        pr_id = 1000 + index
        first_review = created + pd.Timedelta(days=wait_days)
        contributors.append({"id": contributor_id, "github_username": f"contributor{index:02d}", "is_first_time": 1})
        pull_requests.append({
            "id": pr_id,
            "contributor_id": contributor_id,
            "number": index,
            "created_at": created,
            "merged_at": created + pd.Timedelta(days=wait_days + 2) if merged else pd.NaT,
            "closed_at": created + pd.Timedelta(days=wait_days + 3),
            "state": "merged" if merged else "closed",
            "additions": 10 + index * 2,
            "deletions": index % 7,
            "changed_files": 1 + index % 5,
            "is_first_pr": 1,
            "is_merged": merged,
            "first_review_at": first_review,
            "first_review_wait_days": float(wait_days),
            "review_iterations": iterations,
            "returned": returned,
            "first_pr_created_at": created,
            "first_pr_state": "merged" if merged else "closed",
            "first_pr_merged": merged,
            "time_to_merge_days": float(wait_days + 2) if merged else float("nan"),
            "wait_bucket": "fast_le_2d" if wait_days <= 2 else "medium_2_10d" if wait_days <= 10 else "slow_gt_10d",
            "unanswered_issue": int(index % 4 == 0),
        })
        issues.append({
            "id": 2000 + index,
            "contributor_id": contributor_id,
            "created_at": created,
            "first_response_wait_days": float(wait_days if index % 4 else 0),
            "maintainer_replies": int(0 if index % 4 == 0 else 1 + index % 3),
            "resolution_days": float(wait_days + 4),
            "state": "closed" if merged else "open",
            "returned": returned,
        })
    journey = pd.DataFrame(pull_requests).drop(columns=["first_review_at"])
    return {
        "contributors": pd.DataFrame(contributors),
        "pull_requests": pd.DataFrame(pull_requests),
        "issues": pd.DataFrame(issues),
        "journey": journey,
    }