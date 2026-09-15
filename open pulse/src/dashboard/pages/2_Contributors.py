import streamlit as st

from src.dashboard.contributor_data import journey_with_risk


data, journey = journey_with_risk()
st.title("Affected Contributors")

risk_levels = sorted(journey["risk_level"].unique())
risk = st.multiselect("Risk level", risk_levels, default=risk_levels)
returned = st.selectbox("Return status", ["All", "Returned", "Did not return"])
filtered = journey[journey["risk_level"].isin(risk)].copy()
if returned == "Returned":
    filtered = filtered[filtered["returned"].eq(1)]
elif returned == "Did not return":
    filtered = filtered[filtered["returned"].eq(0)]

st.write(f"Showing {len(filtered)} contributors")
if filtered.empty:
    st.warning("No contributors match these filters. Clear a filter to continue.")
else:
    st.dataframe(
        filtered[["contributor_id", "first_pr_created_at", "first_review_wait_days", "review_iterations", "first_pr_state", "returned", "risk_level"]],
        use_container_width=True,
        hide_index=True,
    )
    selected = st.selectbox("Investigate contributor", filtered["contributor_id"].tolist())
    person = filtered[filtered["contributor_id"].eq(selected)].iloc[0]
    st.subheader(f"Contributor {selected} journey")
    first, second, third, fourth = st.columns(4)
    first.metric("First review", f"{person['first_review_wait_days']:.1f} days")
    second.metric("Iterations", int(person["review_iterations"]))
    third.metric("Outcome", person["first_pr_state"])
    fourth.metric("Returned", "Yes" if person["returned"] else "No")
    if person["risk_reasons"]:
        st.error("Potential retention risk: " + person["risk_reasons"])
    else:
        st.success("No elevated onboarding risk detected.")