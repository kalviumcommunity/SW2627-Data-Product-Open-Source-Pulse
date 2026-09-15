import pandas as pd
import streamlit as st

from src.dashboard.contributor_data import _ensure_wait_bucket, factor_breakdown, journey_with_risk


data, journey = journey_with_risk()
journey = _ensure_wait_bucket(journey)
st.title("Onboarding Insights")
st.caption("Compare onboarding experiences by affected contributors and return rate.")

breakdown = factor_breakdown(journey)
if breakdown.empty:
    st.warning("No onboarding factor data is available.")
else:
    st.dataframe(breakdown, use_container_width=True, hide_index=True)

st.subheader("What to investigate")
cards = [
    ("Long first review time", journey.get("wait_bucket", pd.Series(False, index=journey.index)).eq("slow_gt_10d")),
    ("No maintainer response", journey.get("unanswered_issue", pd.Series(0, index=journey.index)).eq(1)),
    ("High review iterations", journey.get("review_iterations", pd.Series(0, index=journey.index)).ge(3)),
]
for label, mask in cards:
    affected = journey[mask]
    rate = affected["returned"].mean() if len(affected) else 0
    st.write(f"**{label}**: {len(affected)} affected, {rate:.0%} returned")