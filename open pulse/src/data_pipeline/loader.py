"""Load raw GitHub export files (CSV/JSON) into DataFrames."""

from pathlib import Path

import pandas as pd


DEFAULT_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def _load(name, path=None):
    source = Path(path) if path else DEFAULT_RAW_DIR / name
    if not source.exists():
        return pd.DataFrame()
    if source.suffix.lower() == ".json":
        return pd.read_json(source)
    return pd.read_csv(source)


def load_contributors(path=None):
    return _load("contributors.csv", path)


def load_pull_requests(path=None):
    return _load("pull_requests.csv", path)


def load_issues(path=None):
    return _load("issues.csv", path)


def load_reviews(path=None):
    return _load("reviews.csv", path)


def load_commits(path=None):
    return _load("commits.csv", path)
