"""Streamlit analytics dashboard: upload, filter, KPI dashboard, and workflow.

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import io

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------- #
# Cached data loader - loads file bytes into a DataFrame, cached by content hash
# --------------------------------------------------------------------------- #
@st.cache_data
def _load_data(file_bytes, file_name):
    """Load uploaded file bytes into a DataFrame, cached by content hash."""
    if file_name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    if file_name.endswith(".json"):
        return pd.read_json(io.BytesIO(file_bytes))
    return None

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

    uploaded_file = st.file_uploader(
        "Upload your dataset", type=["csv", "json"], key="trends_uploader"
    )

    if uploaded_file is not None:
        try:
            trends_bytes = uploaded_file.getvalue()
            trends_df = _load_data(trends_bytes, uploaded_file.name)
            if trends_df is None:
                st.error("Unsupported file type.")
                st.stop()
            trends_df = trends_df.copy()

            if len(trends_df) == 0:
                st.warning("Uploaded file is empty.")
                st.stop()
        except Exception:
            st.error("Could not read this file. Check the format and try again.")
            st.stop()

        st.success(
            "Loaded: "
            + uploaded_file.name
            + " ("
            + str(len(trends_df))
            + " rows, "
            + str(trends_df.columns.size)
            + " columns)"
        )

        # Detect columns for KPIs and charts
        trends_date_col = None
        for col in trends_df.columns:
            if pd.api.types.is_datetime64_any_dtype(trends_df[col]):
                trends_date_col = col
                break
            if trends_df[col].dtype == "object" or str(trends_df[col].dtype) in ("string", "str"):
                try:
                    parsed = pd.to_datetime(trends_df[col], errors="coerce")
                    if parsed.notna().sum() > len(trends_df[col]) * 0.5:
                        trends_df[col] = parsed
                        trends_date_col = col
                        break
                except Exception:
                    continue

        trends_cat_cols = trends_df.select_dtypes(include="object").columns.tolist()
        trends_num_cols = trends_df.select_dtypes(include="number").columns.tolist()
        trends_non_id_num = [
            c for c in trends_num_cols
            if not c.lower().endswith("_id") and c.lower() not in ("id",)
        ]
        trends_slider_col = trends_non_id_num[0] if trends_non_id_num else None

        trends_revenue_col = None
        for c in trends_num_cols:
            if "revenue" in c.lower() or "value" in c.lower() or "amount" in c.lower():
                trends_revenue_col = c
                break
        trends_revenue_col = trends_revenue_col or trends_slider_col

        trends_cat_col = trends_cat_cols[0] if trends_cat_cols else None

        # Sidebar filters for Trends
        st.sidebar.header("Filters (Trends)")
        tf_keys = []

        trends_date_range = None
        if trends_date_col is not None:
            t_min = trends_df[trends_date_col].min().date()
            t_max = trends_df[trends_date_col].max().date()
            trends_date_range = st.sidebar.date_input(
                "Date Range",
                value=(t_min, t_max),
                key="trends_date_range_filter",
            )
            tf_keys.append("trends_date_range_filter")

        trends_selected_values = None
        if trends_cat_col is not None:
            all_t_values = trends_df[trends_cat_col].dropna().unique().tolist()
            trends_selected_values = st.sidebar.multiselect(
                f"Filter by {trends_cat_col}",
                options=all_t_values,
                default=all_t_values,
                key="trends_segment_filter",
            )
            tf_keys.append("trends_segment_filter")

        trends_val_range = None
        if trends_slider_col is not None:
            t_col_min = trends_df[trends_slider_col].min()
            t_col_max = trends_df[trends_slider_col].max()
            trends_val_range = st.sidebar.slider(
                f"{trends_slider_col} Range",
                min_value=t_col_min,
                max_value=t_col_max,
                value=(t_col_min, t_col_max),
                key="trends_slider_filter",
            )
            tf_keys.append("trends_slider_filter")

        trends_chart_type = st.sidebar.radio(
            "Chart type", ["Line", "Bar"], key="trends_chart_type_filter"
        )
        tf_keys.append("trends_chart_type_filter")

        if st.sidebar.button("Reset Filters"):
            for key in tf_keys:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        # Apply filters
        trends_mask = pd.Series([True] * len(trends_df), index=trends_df.index)
        if trends_date_range is not None:
            if isinstance(trends_date_range, tuple):
                s_date, e_date = trends_date_range
            else:
                s_date = e_date = trends_date_range
            trends_mask &= (trends_df[trends_date_col] >= pd.Timestamp(s_date)) & (
                trends_df[trends_date_col] <= pd.Timestamp(e_date)
            )
        if trends_selected_values is not None:
            trends_mask &= trends_df[trends_cat_col].isin(trends_selected_values)
        if trends_val_range is not None:
            trends_mask &= (trends_df[trends_slider_col] >= trends_val_range[0]) & (
                trends_df[trends_slider_col] <= trends_val_range[1]
            )
        trends_filtered = trends_df[trends_mask]

        if len(trends_filtered) == 0:
            st.warning(
                "No data matches the current filters. Try broadening your selection."
            )
            st.stop()

        st.write(
            f"Showing {len(trends_filtered):,} of {len(trends_df):,} records"
        )

        # KPI Dashboard charts
        if trends_revenue_col is not None:
            if trends_date_col is not None:
                st.subheader("Revenue Over Time")
                trend_data = (
                    trends_filtered.groupby(trends_date_col)[trends_revenue_col]
                    .sum()
                    .reset_index()
                    .sort_values(trends_date_col)
                    .set_index(trends_date_col)
                )
                if trends_chart_type == "Line":
                    st.line_chart(trend_data)
                else:
                    st.bar_chart(trend_data)
                st.divider()

            if trends_cat_col is not None:
                st.subheader("Revenue by segment")
                seg_data = (
                    trends_filtered.groupby(trends_cat_col)[trends_revenue_col]
                    .sum()
                    .reset_index()
                    .sort_values(trends_revenue_col, ascending=False)
                    .set_index(trends_cat_col)
                )
                st.bar_chart(seg_data)
                st.divider()
        else:
            st.info(
                "No numeric column detected. Upload data with a numeric "
                "field to see the KPI dashboard."
            )
    else:
        st.info("Upload a CSV or JSON file to begin.")

# --------------------------------------------------------------------------- #
# Page: Data Explorer
# --------------------------------------------------------------------------- #
elif page == "Data Explorer":
    st.title("Data Explorer")

    uploaded_file = st.file_uploader("Upload your dataset", type=["csv", "json"])

    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.getvalue()
            df = _load_data(file_bytes, uploaded_file.name)
            if df is None:
                st.error("Unsupported file type.")
                st.stop()
            df = df.copy()

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

        # "workflow_selected_segment" - stores the segment chosen in Step 1.
        # Without session state, adjusting any sidebar filter would rerun the
        # script and reset this selectbox to its default.
        if "workflow_selected_segment" not in st.session_state:
            st.session_state["workflow_selected_segment"] = "All"
        # "workflow_step" - tracks whether Step 1 is done (1) or Step 2 is
        # reached (2). Prevents Step 2 from rendering before Step 1 is confirmed.
        if "workflow_step" not in st.session_state:
            st.session_state["workflow_step"] = 1
        # "workflow_analysis_result" - caches the Step 2 computation so the
        # result is available for display without recomputing on every rerun.
        if "workflow_analysis_result" not in st.session_state:
            st.session_state["workflow_analysis_result"] = None

        # --- Detect column types for adaptive filters --------------------
        date_col = None
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_col = col
                break
            if df[col].dtype == "object" or str(df[col].dtype) in ("string", "str"):
                try:
                    parsed = pd.to_datetime(df[col], errors="coerce")
                    if parsed.notna().sum() > len(df[col]) * 0.5:
                        df[col] = parsed
                        date_col = col
                        break
                except Exception:
                    continue

        categorical_cols = df.select_dtypes(include="object").columns.tolist()
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        non_id_numeric = [
            c for c in numeric_cols
            if not c.lower().endswith("_id") and c.lower() not in ("id",)
        ]
        slider_col = non_id_numeric[0] if non_id_numeric else None

        # Adaptive analysis columns for the KPI dashboard
        revenue_col = None
        for c in numeric_cols:
            if "revenue" in c.lower() or "value" in c.lower() or "amount" in c.lower():
                revenue_col = c
                break
        revenue_col = revenue_col or slider_col

        customer_col = None
        for c in df.columns:
            if c.lower() in ("customer_id", "userid", "id"):
                customer_col = c
                break

        # --- Sidebar filters --------------------------------------------
        st.sidebar.header("Filters")
        filter_keys = []

        date_range = None
        if date_col is not None:
            d_min = df[date_col].min().date()
            d_max = df[date_col].max().date()
            date_range = st.sidebar.date_input(
                "Date Range", value=(d_min, d_max), key="date_range_filter"
            )
            filter_keys.append("date_range_filter")

        cat_col = None
        selected_values = None
        if categorical_cols:
            cat_col = categorical_cols[0]
            all_values = df[cat_col].dropna().unique().tolist()
            selected_values = st.sidebar.multiselect(
                f"Filter by {cat_col}",
                options=all_values,
                default=all_values,
                key="segment_filter",
            )
            filter_keys.append("segment_filter")

        val_range = None
        if slider_col is not None:
            col_min = df[slider_col].min()
            col_max = df[slider_col].max()
            val_range = st.sidebar.slider(
                f"{slider_col} Range",
                min_value=col_min,
                max_value=col_max,
                value=(col_min, col_max),
                key="slider_filter",
            )
            filter_keys.append("slider_filter")

        chart_type = st.sidebar.radio(
            "Chart type", ["Bar", "Line"], key="chart_type_filter"
        )
        filter_keys.append("chart_type_filter")

        if st.sidebar.button("Reset Filters"):
            for key in filter_keys:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        # --- Reset workflow (session state, not just filter widgets) -----
        if st.sidebar.button("Reset Workflow"):
            _workflow_keys = [
                "workflow_selected_segment",
                "workflow_step",
                "workflow_analysis_result",
            ]
            for key in _workflow_keys:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        # --- Apply all filters to create filtered DataFrame -------------
        mask = pd.Series([True] * len(df), index=df.index)
        if date_range is not None:
            if isinstance(date_range, tuple):
                start_date, end_date = date_range
            else:
                start_date = end_date = date_range
            mask &= (df[date_col] >= pd.Timestamp(start_date)) & (
                df[date_col] <= pd.Timestamp(end_date)
            )
        if selected_values is not None:
            mask &= df[cat_col].isin(selected_values)
        if val_range is not None:
            mask &= (df[slider_col] >= val_range[0]) & (
                df[slider_col] <= val_range[1]
            )
        filtered_df = df[mask]

        # --- Handle empty filter results --------------------------------
        if len(filtered_df) == 0:
            st.warning(
                "No data matches the current filters. Try broadening your selection."
            )
            st.stop()

        st.write(f"Showing {len(filtered_df):,} of {len(df):,} records")

        # --- Automatic preview (uses filtered data) --------------------
        st.header("Dataset Preview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", f"{len(filtered_df):,}")
        with col2:
            st.metric("Columns", str(len(filtered_df.columns)))
        with col3:
            total_nulls = filtered_df.isnull().sum().sum()
            total_cells = filtered_df.shape[0] * filtered_df.shape[1]
            null_pct = (total_nulls / total_cells) * 100 if total_cells else 0
            st.metric("Null %", f"{null_pct:.1f}%")
        st.divider()

        st.subheader("First 10 Rows")
        st.dataframe(filtered_df.head(10), use_container_width=True)

        st.subheader("Column Summary")
        f_len = len(filtered_df)
        summary = pd.DataFrame(
            {
                "Column": filtered_df.columns,
                "Type": filtered_df.dtypes.astype(str).values,
                "Non-Null": filtered_df.notnull().sum().values,
                "Null Count": filtered_df.isnull().sum().values,
                "Null %": (
                    filtered_df.isnull().sum() / f_len * 100
                    if f_len > 0
                    else 0
                ).round(1).values,
            }
        )
        st.dataframe(summary, use_container_width=True)

        # --- Descriptive statistics ------------------------------------
        st.subheader("Descriptive Statistics")
        st.dataframe(filtered_df.describe(), use_container_width=True)

        # --- KPI Dashboard (reactive metrics + charts) ------------------
        st.header("KPI Dashboard")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if revenue_col is not None:
                st.metric("Revenue", f"${filtered_df[revenue_col].sum():,.0f}")
            else:
                st.metric("Revenue", "—")
        with col2:
            if revenue_col is not None:
                st.metric("Avg Order", f"${filtered_df[revenue_col].mean():,.0f}")
            else:
                st.metric("Avg Order", "—")
        with col3:
            st.metric("Records", f"{len(filtered_df):,}")
        with col4:
            if customer_col is not None:
                st.metric("Customers", f"{filtered_df[customer_col].nunique():,}")
            else:
                st.metric("Customers", "—")
        with col5:
            kpi_nulls = filtered_df.isnull().sum().sum()
            kpi_cells = filtered_df.shape[0] * filtered_df.shape[1]
            kpi_null_pct = (kpi_nulls / kpi_cells) * 100 if kpi_cells else 0
            st.metric("Quality", f"{100 - kpi_null_pct:.1f}%")

        st.divider()

        # --- Three chart types wired to filtered_df -----------------------
        if revenue_col is not None:
            # Chart 1: trend over time (line or bar, controlled by sidebar radio)
            if date_col is not None:
                st.subheader(f"{revenue_col} Over Time")
                trend = (
                    filtered_df.groupby(date_col)[revenue_col]
                    .sum()
                    .reset_index()
                    .sort_values(date_col)
                    .set_index(date_col)
                )
                if chart_type == "Line":
                    st.line_chart(trend)
                else:
                    st.bar_chart(trend)

            # Chart 2: comparison by segment (bar)
            if cat_col is not None:
                st.subheader(f"{revenue_col} by {cat_col}")
                seg = (
                    filtered_df.groupby(cat_col)[revenue_col]
                    .sum()
                    .reset_index()
                    .sort_values(revenue_col, ascending=False)
                    .set_index(cat_col)
                )
                st.bar_chart(seg)

            # Chart 3: distribution (Plotly histogram)
            st.subheader(f"{revenue_col} Distribution")
            import plotly.express as px

            fig = px.histogram(
                filtered_df,
                x=revenue_col,
                nbins=30,
                title=f"Distribution of {revenue_col}",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No numeric column detected. Upload data with a numeric field to see the KPI dashboard.")

        # Progressive disclosure - raw data behind an expander
        with st.expander("Raw data"):
            st.dataframe(filtered_df, use_container_width=True)
            st.download_button(
                "Download CSV",
                data=filtered_df.to_csv(index=False).encode("utf-8"),
                file_name="data.csv",
                mime="text/csv",
            )

        # --- Multi-step analysis workflow (session state persists) -------
        st.divider()
        st.header("Analysis Workflow")

        st.subheader("Step 1: Select Analysis Segment")
        if cat_col is not None:
            available = sorted(filtered_df[cat_col].dropna().unique().tolist())
            opts = ["All"] + available
        else:
            opts = ["All"]

        current_seg = st.session_state["workflow_selected_segment"]
        if current_seg not in opts:
            current_seg = "All"
            st.session_state["workflow_selected_segment"] = "All"
        seg_index = opts.index(current_seg) if current_seg in opts else 0
        step1_segment = st.selectbox(
            "Choose a segment to analyse", opts, index=seg_index
        )

        if st.button("Confirm Segment"):
            st.session_state["workflow_selected_segment"] = step1_segment
            st.session_state["workflow_step"] = 2

        if st.session_state["workflow_step"] >= 2:
            st.subheader("Step 2: Segment Analysis")
            chosen = st.session_state["workflow_selected_segment"]
            if chosen == "All":
                analysis_df = filtered_df
            else:
                analysis_df = filtered_df[filtered_df[cat_col] == chosen]

            if len(analysis_df) == 0:
                st.warning(
                    "No data for the selected segment after the current "
                    "sidebar filters. Try broadening the filters."
                )
            else:
                if slider_col is not None:
                    result = float(analysis_df[slider_col].sum())
                    st.session_state["workflow_analysis_result"] = result
                    st.metric(f"{slider_col} Total", f"{result:,.0f}")
                else:
                    result = len(analysis_df)
                    st.session_state["workflow_analysis_result"] = result
                    st.metric("Row Count", f"{result:,}")

                st.caption(
                    f"Analysing: {chosen}. This selection persists when "
                    "sidebar filters change because it lives in session state."
                )

    else:
        st.info("Upload a CSV or JSON file to begin.")
