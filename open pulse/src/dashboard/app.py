"""Streamlit entry point for the Open Pulse analytics dashboard.

Run from the project root:

    streamlit run src/dashboard/app.py

Streamlit places this file's own directory on ``sys.path``, not the project
root, so the bootstrap below runs before any project import. Pages are
registered explicitly through ``st.navigation`` rather than relying on
filename discovery, which keeps the ordering, grouping, and titles under our
control and stops unfinished page stubs from appearing in the sidebar.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

st.set_page_config(
    page_title="Open Pulse Analytics",
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = {
    "Business Analytics": [
        st.Page(
            "pages/3_Executive_Summary.py",
            title="Executive Summary",
            icon=":material/speed:",
            default=True,
        ),
        st.Page(
            "pages/1_Business_Overview.py",
            title="Business Overview",
            icon=":material/insights:",
        ),
        st.Page(
            "pages/2_Interactive_Explorer.py",
            title="Interactive Explorer",
            icon=":material/touch_app:",
        ),
        st.Page(
            "pages/4_Churn_Story.py",
            title="Why Customers Leave",
            icon=":material/menu_book:",
        ),
        st.Page(
            "pages/5_Decision_Brief.py",
            title="Decision Brief",
            icon=":material/gavel:",
        ),
    ],
}

with st.sidebar:
    st.markdown("### Open Pulse")
    st.caption(
        "Analytics over the outputs of the data pipeline in `scripts/`. "
        "Every figure is built from a committed artifact in `output/`."
    )

st.navigation(PAGES).run()
