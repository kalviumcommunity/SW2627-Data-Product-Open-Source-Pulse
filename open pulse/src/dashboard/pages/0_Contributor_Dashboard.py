import altair as alt
import pandas as pd
import streamlit as st

from src.analytics.retention import churn_risk_flags
from src.dashboard.contributor_data import _ensure_wait_bucket, driver_summary, journey_with_risk, load_contributor_data


st.title("Contributor Retention Dashboard")
state_key = "persisted_contributor_csv"
version_key = "contributor_uploader_version"
st.session_state.setdefault(version_key, 0)
widget_key = f"contributor_csv_uploader_{st.session_state[version_key]}"
uploaded_file = st.file_uploader("Upload contributor journey CSV", type=["csv"], key=widget_key)
if uploaded_file is not None:
    st.session_state[state_key] = {
        "name": uploaded_file.name,
        "bytes": uploaded_file.getvalue(),
    }

if state_key in st.session_state:
    if st.button("Remove uploaded CSV", key="remove_contributor_csv"):
        del st.session_state[state_key]
        st.session_state[version_key] += 1
        st.rerun()

try:
    if uploaded_file is not None:
        data = load_contributor_data(uploaded_file)
        journey = churn_risk_flags(data["journey"])
    elif state_key in st.session_state:
        data = load_contributor_data(st.session_state[state_key])
        journey = churn_risk_flags(data["journey"])
    else:
        data, journey = journey_with_risk()
except ValueError as error:
    st.error(str(error))
    st.stop()
if data["demo"]:
    st.info("Showing deterministic demo contributor data. Add GitHub exports to open pulse/data/raw/ to use repository data.")

journey = _ensure_wait_bucket(journey)
if "first_pr_merged" not in journey.columns:
    journey["first_pr_merged"] = 0
journey["first_pr_merged"] = pd.to_numeric(journey["first_pr_merged"], errors="coerce").fillna(0).astype(int)

total = len(journey)
returned = int(journey["returned"].sum())
return_rate = returned / total if total else 0
slow = journey.get("wait_bucket", pd.Series([False] * len(journey), index=journey.index)).eq("slow_gt_10d")
drivers = driver_summary(journey)
top_driver = drivers.iloc[0]["driver"] if not drivers.empty else "No driver detected"

first, second, third, fourth = st.columns(4)
first.metric("First-time contributors", total)
second.metric("Return rate", f"{return_rate:.0%}")
third.metric("Slow first reviews", int(slow.sum()))
fourth.metric("Top friction", top_driver)

st.subheader("Top onboarding drivers")
if drivers.empty:
    st.warning("No onboarding drivers are available for this dataset.")
else:
    st.dataframe(drivers, use_container_width=True, hide_index=True)

st.subheader("First-time contributor journey")
funnel = pd.DataFrame({
    "stage": ["First contribution", "Reviewed", "Merged", "Returned"],
    "contributors": [
        total,
        int(journey["first_review_wait_days"].notna().sum()),
        int(journey["first_pr_merged"].sum()),
        returned,
    ],
})
chart = alt.Chart(funnel).mark_bar().encode(
    x=alt.X("stage:N", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("contributors:Q"),
).properties(height=300)
st.altair_chart(chart, use_container_width=True)
