import streamlit as st

from src.dashboard.contributor_data import journey_with_risk


data, journey = journey_with_risk()
st.title("Issue Analysis")
st.caption("Issue participation and maintainer response versus contributor return.")

issues = data["issues"].copy()
if issues.empty:
    st.warning("No issue participation records are available.")
else:
    first, second, third, fourth, fifth = st.columns(5)
    first.metric("Issues", len(issues))
    second.metric("Avg first response", f"{issues['first_response_wait_days'].mean():.1f}d")
    third.metric("Avg maintainer replies", f"{issues['maintainer_replies'].mean():.1f}")
    fourth.metric("Resolved", f"{issues['state'].eq('closed').mean():.0%}")
    fifth.metric("Return rate", f"{issues['returned'].mean():.0%}")
    st.subheader("Return rate by maintainer response")
    st.bar_chart(issues.groupby(issues["maintainer_replies"].eq(0))["returned"].mean())
    st.dataframe(issues, use_container_width=True, hide_index=True)