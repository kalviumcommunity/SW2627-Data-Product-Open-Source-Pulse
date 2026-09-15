import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard.contributor_data import _ensure_wait_bucket, journey_with_risk


data, journey = journey_with_risk()
journey = _ensure_wait_bucket(journey)
if "first_pr_merged" not in journey.columns:
    journey["first_pr_merged"] = 0
journey["first_pr_merged"] = pd.to_numeric(journey["first_pr_merged"], errors="coerce").fillna(0).astype(int)
st.title("Pull Request Analysis")
st.caption("Review process behavior versus first-time contributor return.")

first, second, third, fourth, fifth = st.columns(5)
first.metric("First-time PRs", len(journey))
second.metric("Avg first review", f"{journey['first_review_wait_days'].mean():.1f}d")
third.metric("Avg iterations", f"{journey['review_iterations'].mean():.1f}")
fourth.metric("Merge rate", f"{journey['first_pr_merged'].mean():.0%}")
fifth.metric("Return rate", f"{journey['returned'].mean():.0%}")

st.subheader("Return rate by first-review experience")
if "wait_bucket" in journey.columns:
    chart_data = journey.groupby("wait_bucket")["returned"].mean().reset_index()
    chart_data.columns = ["wait_bucket", "returned"]
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("wait_bucket:N", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("returned:Q"),
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No wait bucket is available for this dataset.")
st.subheader("Review iterations and return")
chart_data = journey.groupby("review_iterations")["returned"].mean().reset_index()
chart_data.columns = ["review_iterations", "returned"]
chart = alt.Chart(chart_data).mark_bar().encode(
    x=alt.X("review_iterations:N", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("returned:Q"),
).properties(height=300)
st.altair_chart(chart, use_container_width=True)
st.dataframe(
    journey[["contributor_id", "first_review_wait_days", "review_iterations", "first_pr_state", "returned"]],
    use_container_width=True,
    hide_index=True,
)