"""Data access and derived views for contributor-retention screens."""

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.analytics.demo_data import build_demo_data
from src.analytics.first_time_contributors import return_rate_by_factor
from src.analytics.retention import churn_risk_flags


OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"


def _ensure_wait_bucket(journey):
    if "wait_bucket" in journey.columns:
        return journey
    if "first_review_wait_days" not in journey.columns:
        return journey
    wait = pd.to_numeric(journey["first_review_wait_days"], errors="coerce")
    result = journey.copy()
    result["wait_bucket"] = pd.cut(
        wait,
        bins=[-float("inf"), 2, 10, float("inf")],
        labels=["fast_le_2d", "medium_2_10d", "slow_gt_10d"],
        include_lowest=True,
    ).astype("object")
    result.loc[wait.isna(), "wait_bucket"] = "no_review"
    return result


def _ensure_first_pr_merged(journey):
    if "first_pr_merged" in journey.columns:
        return journey
    result = journey.copy()
    if "first_pr_state" in result.columns:
        states = result["first_pr_state"].astype(str).str.lower()
        result["first_pr_merged"] = states.eq("merged").astype(int)
    else:
        result["first_pr_merged"] = 0
    return result


def load_contributor_data(uploaded_file=None):
    persisted_key = "persisted_contributor_csv"
    if uploaded_file is None:
        uploaded_file = st.session_state.get(persisted_key)
    if uploaded_file is not None:
        if isinstance(uploaded_file, dict) and "bytes" in uploaded_file:
            uploaded_file = BytesIO(uploaded_file["bytes"])
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        journey = pd.read_csv(uploaded_file)
        required = {"contributor_id", "first_review_wait_days", "review_iterations", "returned"}
        missing = required.difference(journey.columns)
        if missing:
            raise ValueError(f"Uploaded journey CSV is missing columns: {sorted(missing)}")
        journey = _ensure_wait_bucket(journey)
        journey = _ensure_first_pr_merged(journey)
        if "risk_level" not in journey:
            journey = churn_risk_flags(journey)
        return {"journey": journey, "pull_requests": journey, "issues": pd.DataFrame(), "demo": False}
    journey_path = OUTPUT_DIR / "contributor_journey.csv"
    if journey_path.exists():
        journey = pd.read_csv(journey_path)
        return {
            "journey": journey,
            "pull_requests": pd.read_csv(OUTPUT_DIR / "pull_requests.csv") if (OUTPUT_DIR / "pull_requests.csv").exists() else journey,
            "issues": pd.read_csv(OUTPUT_DIR / "issues.csv") if (OUTPUT_DIR / "issues.csv").exists() else pd.DataFrame(),
            "demo": False,
        }
    data = build_demo_data()
    data["demo"] = True
    return data


def journey_with_risk():
    data = load_contributor_data()
    return data, churn_risk_flags(data["journey"])


def driver_summary(journey):
    rows = []
    for factor, label in [
        ("wait_bucket", "Long first review time"),
        ("unanswered_issue", "No maintainer response"),
        ("review_iterations", "High review iterations"),
    ]:
        if factor not in journey:
            continue
        if factor == "wait_bucket":
            affected = journey[factor].eq("slow_gt_10d")
        elif factor == "review_iterations":
            affected = pd.to_numeric(journey[factor], errors="coerce").ge(3)
        else:
            affected = journey[factor].fillna(0).astype(bool)
        group = journey.loc[affected]
        return_rate = group["returned"].mean() if len(group) else 0
        rows.append({
            "driver": label,
            "affected_contributors": int(group["contributor_id"].nunique()),
            "return_rate": float(return_rate),
            "impact": int(len(group) * (1 - return_rate)),
        })
    return pd.DataFrame(rows).sort_values("impact", ascending=False) if rows else pd.DataFrame()


def factor_breakdown(journey):
    frames = []
    for factor in ["wait_bucket", "unanswered_issue", "review_iterations", "first_pr_merged"]:
        if factor in journey:
            summary = return_rate_by_factor(journey, factor).rename(columns={factor: "value"})
            summary["factor"] = factor
            frames.append(summary)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()