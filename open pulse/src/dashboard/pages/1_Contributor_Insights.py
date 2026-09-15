import streamlit as st

from src.dashboard.contributor_data import factor_breakdown, journey_with_risk


data, journey = journey_with_risk()
st.title("Onboarding Insights")
st.caption("Compare onboarding experiences by affected contributors and return rate.")

breakdown = factor_breakdown(journey)
if breakdown.empty:
    st.warning("No onboarding factor data is available.")
else:
    st.dataframe(breakdown, use_container_width=True, hide_index=True)

st.subheader("What to investigate")
cards = [
    ("Long first review time", journey["wait_bucket"].eq("slow_gt_10d")),
    ("No maintainer response", journey["unanswered_issue"].eq(1)),
    ("High review iterations", journey["review_iterations"].ge(3)),
]
for label, mask in cards:
    affected = journey[mask]
    rate = affected["returned"].mean() if len(affected) else 0
    st.write(f"**{label}**: {len(affected)} affected, {rate:.0%} returned")