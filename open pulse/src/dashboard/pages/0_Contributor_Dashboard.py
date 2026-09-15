import pandas as pd
import streamlit as st

from src.analytics.retention import churn_risk_flags
from src.dashboard.contributor_data import driver_summary, journey_with_risk, load_contributor_data


st.title("Contributor Retention Dashboard")
uploaded_file = st.file_uploader("Upload contributor journey CSV", type=["csv"])
try:
    if uploaded_file is not None:
        data = load_contributor_data(uploaded_file)
        journey = churn_risk_flags(data["journey"])
    else:
        data, journey = journey_with_risk()
except ValueError as error:
    st.error(str(error))
    st.stop()
if data["demo"]:
    st.info("Showing deterministic demo contributor data. Add GitHub exports to open pulse/data/raw/ to use repository data.")

total = len(journey)
returned = int(journey["returned"].sum())
return_rate = returned / total if total else 0
slow = journey["wait_bucket"].eq("slow_gt_10d")
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
}).set_index("stage")
st.bar_chart(funnel)