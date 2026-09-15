import streamlit as st

from src.dashboard.contributor_data import driver_summary, journey_with_risk


data, journey = journey_with_risk()
st.title("Recommendations")
st.caption("Prioritized actions based on observed onboarding friction.")

recommendations = [
    ("High", "Reduce first review time", "Set a maintainer response target under 48 hours and monitor the slow-review cohort."),
    ("Medium", "Create beginner-friendly issues", "Label starter issues with scope, expected skills, and a clear first step."),
    ("Medium", "Reduce review iteration friction", "Add contribution guidance and examples before the first PR reaches review."),
]
for priority, title, action in recommendations:
    with st.container(border=True):
        st.subheader(title)
        st.caption(f"Priority: {priority}")
        st.write(action)
        st.checkbox("Mark as actioned", key=title)

drivers = driver_summary(journey)
if not drivers.empty:
    st.subheader("Evidence")
    st.dataframe(drivers, use_container_width=True, hide_index=True)