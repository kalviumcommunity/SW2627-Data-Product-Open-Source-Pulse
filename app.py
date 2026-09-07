"""Streamlit app shell: sidebar navigation, columns, expanders, hierarchy.

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# Sidebar navigation
# --------------------------------------------------------------------------- #
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Overview", "Trends", "Data Explorer"],
)

# --------------------------------------------------------------------------- #
# Page: Overview
# --------------------------------------------------------------------------- #
if page == "Overview":
    st.title("Business Overview")

    # Level 1 - Status: KPI cards first (above the fold)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Revenue", "$5.2M", "+12.5%")
    with col2:
        st.metric("Users", "2,500", "+5.2%")
    with col3:
        st.metric("AOV", "$45", "+2.1%")
    with col4:
        st.metric("Churn", "5.2%", "-2.8%", delta_color="inverse")
    with col5:
        st.metric("NPS", "72", "+4")

    # Level 2 - Trend
    st.header("Revenue Trend")
    st.subheader("30-day view")
    st.write("Chart placeholder")
    st.divider()

    # Level 3 - Segments
    st.header("Segment Breakdown")
    st.subheader("Revenue by customer segment")
    st.write("Chart placeholder")
    st.divider()

    # Optional detail
    with st.expander("About These Metrics"):
        st.write(
            "Revenue is calculated as the sum of all order amounts for the "
            "current month. Churn is the percentage of customers who did not "
            "return within 30 days."
        )

# --------------------------------------------------------------------------- #
# Page: Trends
# --------------------------------------------------------------------------- #
elif page == "Trends":
    st.title("Trend Analysis")

    st.header("Time-Series Charts")
    st.subheader("Daily metrics (last 90 days)")
    c1, c2 = st.columns(2)
    with c1:
        st.write("Revenue trend chart placeholder")
    with c2:
        st.write("Customer growth chart placeholder")
    st.divider()

    st.header("Period Comparison")
    st.subheader("Current vs. prior period")
    c3, c4 = st.columns(2)
    with c3:
        st.write("Volume comparison placeholder")
    with c4:
        st.write("Value comparison placeholder")
    st.divider()

    with st.expander("Chart controls"):
        st.write(
            "Choose granularity, toggle smoothing, and switch metric sets. "
            "These controls affect every chart above."
        )

# --------------------------------------------------------------------------- #
# Page: Data Explorer
# --------------------------------------------------------------------------- #
elif page == "Data Explorer":
    st.title("Data Explorer")

    st.header("Filters")
    st.subheader("Narrow the data below")
    c1, c2 = st.columns(2)
    with c1:
        st.write("Segment selector placeholder")
    with c2:
        st.write("Date range picker placeholder")
    st.divider()

    st.header("Data Tables")
    st.subheader("Filtered results")
    st.write("Data table placeholder")
    st.divider()

    # Progressive disclosure - raw data lives behind an expander
    with st.expander("Raw data"):
        st.dataframe(pd.DataFrame({"col": []}), width="stretch")
        st.download_button("Download CSV", data="", file_name="data.csv")
