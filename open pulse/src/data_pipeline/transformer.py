"""Transform raw DataFrames into the analytics schema.

Uses pandas/numpy for cleaning, type coercion, date parsing,
and feature engineering (is_first_pr, wait times, buckets).
"""

def clean_datetime(df, columns):
    """Coerce columns to datetime."""
    ...

def compute_first_time_flags(pull_requests):
    """Mark each contributor's first-ever PR (is_first_pr)."""
    ...

def compute_first_review_wait(reviews, pull_requests):
    """Time from PR creation to first review, per PR."""
    ...

def build_contribution_history(pull_requests, commits, issues):
    """Chronological contribution log per contributor."""
    ...

def bucket_wait_times(journey, thresholds=None):
    """Bucket first-review wait into fast/medium/slow/no_review."""
    ...
