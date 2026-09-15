"""First-time contributor journey metrics."""

import pandas as pd


def cohort_builder(journey_df):
    result = journey_df.copy()
    if result.empty:
        return result
    result["first_pr_created_at"] = pd.to_datetime(result["first_pr_created_at"], errors="coerce", utc=True)
    result["first_review_wait_days"] = pd.to_numeric(result["first_review_wait_days"], errors="coerce")
    result["time_to_merge_days"] = pd.to_numeric(result["time_to_merge_days"], errors="coerce")
    result["returned"] = result["returned"].fillna(0).astype(int)
    return result.drop_duplicates("contributor_id").reset_index(drop=True)


def return_rate_by_bucket(df, bucket_col="wait_bucket"):
    return return_rate_by_factor(df, bucket_col)


def return_rate_by_factor(df, factor):
    if factor not in df:
        raise KeyError(factor)
    return (
        df.groupby(factor, dropna=False)
        .agg(contributors=("contributor_id", "nunique"), returned=("returned", "sum"))
        .assign(return_rate=lambda value: value["returned"] / value["contributors"])
        .reset_index()
    )
