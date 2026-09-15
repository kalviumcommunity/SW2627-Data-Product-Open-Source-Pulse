import streamlit as st

from src.dashboard.contributor_data import journey_with_risk


data, journey = journey_with_risk()
st.title("Pull Request Analysis")
st.caption("Review process behavior versus first-time contributor return.")

first, second, third, fourth, fifth = st.columns(5)
first.metric("First-time PRs", len(journey))
second.metric("Avg first review", f"{journey['first_review_wait_days'].mean():.1f}d")
third.metric("Avg iterations", f"{journey['review_iterations'].mean():.1f}")
fourth.metric("Merge rate", f"{journey['first_pr_merged'].mean():.0%}")
fifth.metric("Return rate", f"{journey['returned'].mean():.0%}")

st.subheader("Return rate by first-review experience")
st.bar_chart(journey.groupby("wait_bucket")["returned"].mean())
st.subheader("Review iterations and return")
st.bar_chart(journey.groupby("review_iterations")["returned"].mean())
st.dataframe(
    journey[["contributor_id", "first_review_wait_days", "review_iterations", "first_pr_state", "returned"]],
    use_container_width=True,
    hide_index=True,
)