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

    uploaded_file = st.file_uploader("Upload your dataset", type=["csv", "json"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(".json"):
                df = pd.read_json(uploaded_file)
            else:
                st.error("Unsupported file type.")
                st.stop()

            if len(df) == 0:
                st.warning("Uploaded file is empty.")
                st.stop()
        except Exception:
            st.error("Could not read this file. Check the format and try again.")
            st.stop()

        st.success(
            "Loaded: "
            + uploaded_file.name
            + " ("
            + str(len(df))
            + " rows, "
            + str(len(df.columns))
            + " columns)"
        )

        # --- Task 2: automatic preview ---------------------------------
        st.header("Dataset Preview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", f"{len(df):,}")
        with col2:
            st.metric("Columns", str(len(df.columns)))
        with col3:
            total_nulls = df.isnull().sum().sum()
            total_cells = df.shape[0] * df.shape[1]
            null_pct = (total_nulls / total_cells) * 100
            st.metric("Null %", f"{null_pct:.1f}%")
        st.divider()

        st.subheader("First 10 Rows")
        st.dataframe(df.head(10), use_container_width=True)

        st.subheader("Column Summary")
        summary = pd.DataFrame(
            {
                "Column": df.columns,
                "Type": df.dtypes.astype(str).values,
                "Non-Null": df.notnull().sum().values,
                "Null Count": df.isnull().sum().values,
                "Null %": (df.isnull().sum() / len(df) * 100).round(1).values,
            }
        )
        st.dataframe(summary, use_container_width=True)

        # --- Task 3: descriptive statistics ----------------------------
        st.subheader("Descriptive Statistics")
        st.dataframe(df.describe(), use_container_width=True)

        # --- Task 5: downstream exploration ----------------------------
        st.subheader("Quick Exploration")
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            selected_col = st.selectbox("Select a column to visualise", numeric_cols)
            st.bar_chart(df[selected_col].value_counts().head(20))
        else:
            st.info("No numeric columns to chart.")

        # Progressive disclosure - raw data behind an expander
        with st.expander("Raw data"):
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="data.csv",
                mime="text/csv",
            )

    else:
        st.info("Upload a CSV or JSON file to begin.")
