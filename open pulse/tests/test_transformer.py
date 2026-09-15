"""Tests for data transforms (first-PR flags, wait times, buckets)."""

from io import StringIO

import pandas as pd

from src.dashboard.contributor_data import load_contributor_data


def test_load_contributor_data_derives_wait_bucket_for_uploaded_csv():
    csv = StringIO(
        "contributor_id,first_review_wait_days,review_iterations,returned\n"
        "1,3,2,1\n"
        "2,12,4,0\n"
        "3,NaN,1,0\n"
    )

    data = load_contributor_data(csv)
    journey = data["journey"]

    assert "wait_bucket" in journey.columns
    assert journey.loc[0, "wait_bucket"] == "medium_2_10d"
    assert journey.loc[1, "wait_bucket"] == "slow_gt_10d"
    assert journey.loc[2, "wait_bucket"] == "no_review"


def test_load_contributor_data_derives_missing_first_pr_merged_for_uploaded_csv():
    csv = StringIO(
        "contributor_id,first_review_wait_days,review_iterations,returned\n"
        "1,3,2,1\n"
        "2,12,4,0\n"
        "3,NaN,1,0\n"
    )

    data = load_contributor_data(csv)
    journey = data["journey"]

    assert "first_pr_merged" in journey.columns
    assert journey["first_pr_merged"].tolist() == [0, 0, 0]


def test_load_contributor_data_reads_persisted_csv_bytes():
    csv = {
        "name": "contributors.csv",
        "bytes": (
            b"contributor_id,first_review_wait_days,review_iterations,returned\n"
            b"1,3,2,1\n"
        ),
    }

    data = load_contributor_data(csv)

    assert data["journey"].loc[0, "contributor_id"] == 1
    assert data["journey"].loc[0, "wait_bucket"] == "medium_2_10d"
