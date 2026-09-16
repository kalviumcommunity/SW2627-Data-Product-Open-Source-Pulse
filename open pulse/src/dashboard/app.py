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

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402
from src.dashboard import theme  # noqa: E402

theme_preference = st.query_params.get("theme")
if theme_preference in {"light", "dark"}:
    st.session_state["dark_mode"] = theme_preference == "dark"
else:
    st.session_state.setdefault("dark_mode", False)
dark_mode = st.session_state["dark_mode"]


def save_theme_preference():
    """Persist the toggle in the URL so navigation and reloads keep the mode."""
    st.query_params["theme"] = "dark" if st.session_state["dark_mode"] else "light"

st.set_page_config(
    page_title="Open Pulse Analytics",
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="expanded",
)
theme.set_dark_mode(dark_mode)
colors = theme.active_tokens()

_streamlit_dataframe = st.dataframe


def _themed_dataframe(data=None, *args, **kwargs):
    """Keep dataframe cell colours aligned with the dashboard appearance."""
    if isinstance(data, pd.DataFrame):
        foreground = colors["text"]
        background = colors["table"]
        header = colors["table_header"]
        data = (
            data.style
            .set_properties(**{"color": foreground, "background-color": background})
            .set_table_styles([
                {"selector": "th", "props": [("color", foreground), ("background-color", header)]},
            ])
        )
    return _streamlit_dataframe(data, *args, **kwargs)


st.dataframe = _themed_dataframe

st.markdown(
    f"""
    <style>
    :root {{
        color-scheme: {"dark" if dark_mode else "light"};
        --pulse-bg: {colors["background"]};
        --pulse-surface: {colors["surface"]};
        --pulse-table: {colors["table"]};
        --pulse-input: {colors["input"]};
        --pulse-sidebar: {colors["sidebar"]};
        --pulse-navbar: {colors["navbar"]};
        --pulse-control-bg: {colors["input"]};
        --pulse-control-hover: {colors["hover"]};
        --pulse-active: {colors["active"]};
        --pulse-table-header: {colors["table_header"]};
        --pulse-table-row: {colors["table"]};
        --pulse-table-row-alt: {colors["table_alt"]};
        --pulse-text: {colors["text"]};
        --pulse-muted: {colors["text_secondary"]};
        --pulse-border: {colors["border"]};
        --pulse-strong-border: {colors["strong_border"]};
        --pulse-accent: {colors["primary"]};
        --pulse-accent-secondary: {colors["secondary"]};
        --pulse-success: {colors["success"]};
        --pulse-warning: {colors["warning"]};
        --pulse-error: {colors["danger"]};
        --pulse-shadow: {colors["shadow"]};
    }}
    html, body, .stApp {{
        background: var(--pulse-bg);
        color: var(--pulse-text);
        color-scheme: {"dark" if dark_mode else "light"};
        transition: background-color 220ms ease, color 220ms ease;
    }}
    [data-testid="stHeader"] {{
        background: var(--pulse-navbar);
        transition: background-color 220ms ease, border-color 220ms ease;
    }}
    [data-testid="stSidebar"] {{
        background: var(--pulse-sidebar);
        transition: background-color 220ms ease, border-color 220ms ease;
    }}
    [data-testid="stSidebar"] * {{ color: var(--pulse-text); }}
    [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background: var(--pulse-active);
        border-left: 3px solid var(--pulse-accent-secondary);
        transition: background-color 180ms ease, border-color 180ms ease,
                    color 180ms ease;
    }}
    [data-testid="stCheckbox"] input {{ accent-color: var(--pulse-accent-secondary); }}
    [data-testid="stButton"] button,
    [data-testid="stDownloadButton"] button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stFileUploader"] button {{
        background: var(--pulse-control-bg);
        color: var(--pulse-text);
        border: 1px solid var(--pulse-border);
        box-shadow: 0 1px 2px var(--pulse-shadow);
        transition: background-color 180ms ease, color 180ms ease,
                border-color 180ms ease, box-shadow 180ms ease;
    }}
    [data-testid="stButton"] button:hover,
    [data-testid="stDownloadButton"] button:hover,
    [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stFileUploader"] button:hover {{
        background: var(--pulse-control-hover);
        color: var(--pulse-text);
        border-color: var(--pulse-muted);
    }}
    [data-testid="stButton"] button:focus,
    [data-testid="stDownloadButton"] button:focus,
    [data-testid="stFormSubmitButton"] button:focus,
    [data-testid="stFileUploader"] button:focus {{
        color: var(--pulse-text);
        border-color: var(--pulse-muted);
        box-shadow: 0 0 0 2px var(--pulse-border);
    }}
    [data-testid="stFileUploaderDropzone"] {{
        background: var(--pulse-control-bg) !important;
        border-color: var(--pulse-border) !important;
    }}
    [data-testid="stFileUploaderDropzoneInstructions"] * {{
        color: var(--pulse-muted) !important;
    }}
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {{
        background: var(--pulse-control-bg);
        color: var(--pulse-text);
        border-color: var(--pulse-border);
        transition: background-color 180ms ease, color 180ms ease,
                    border-color 180ms ease, box-shadow 180ms ease;
        transition: background-color 180ms ease, color 180ms ease,
                border-color 180ms ease, box-shadow 180ms ease;
    }}
    [data-baseweb="select"] *,
    [data-baseweb="input"] *,
    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stNumberInput"] input::placeholder {{
        color: var(--pulse-text);
    }}
    [data-testid="stExpander"],
    [data-testid="stPopover"] > div,
    [data-testid="stAlert"],
    [role="tooltip"] {{
        background: var(--pulse-surface);
        color: var(--pulse-text);
        border-color: var(--pulse-border);
        box-shadow: 0 4px 12px var(--pulse-shadow);
        transition: background-color 220ms ease, color 220ms ease,
                    border-color 220ms ease, box-shadow 220ms ease;
    }}
    [data-testid="stAlert"] p,
    [data-testid="stExpander"] p {{ color: var(--pulse-text); }}
    [aria-busy="true"],
    [data-testid="stSpinner"] {{ color: var(--pulse-accent-secondary); }}
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"] {{ color: var(--pulse-muted); }}
    [data-testid="stDataFrame"],
    [data-testid="stTable"] {{
        background: var(--pulse-table);
        border: 1px solid var(--pulse-border);
        color: var(--pulse-text);
        color-scheme: {"dark" if dark_mode else "light"};
        transition: background-color 220ms ease, color 220ms ease,
                    border-color 220ms ease, box-shadow 220ms ease;
    }}
    [data-testid="stDataFrame"] .stDataFrameGlideDataEditor {{
        --gdg-text-dark: {colors["text"]} !important;
        --gdg-text-medium: {colors["text_secondary"]} !important;
        --gdg-text-light: {colors["text_muted"]} !important;
        --gdg-text-bubble: {colors["text_secondary"]} !important;
        --gdg-bg-icon-header: {colors["text_muted"]} !important;
        --gdg-fg-icon-header: {colors["text"]} !important;
        --gdg-text-header: {colors["text_secondary"]} !important;
        --gdg-text-group-header: {colors["text_secondary"]} !important;
        --gdg-bg-group-header: {colors["table_header"]} !important;
        --gdg-bg-group-header-hovered: {colors["hover"]} !important;
        --gdg-text-header-selected: {colors["text"]} !important;
        --gdg-bg-cell: {colors["table"]} !important;
        --gdg-bg-cell-medium: {colors["table"]} !important;
        --gdg-bg-header: {colors["table_header"]} !important;
        --gdg-bg-header-has-focus: {colors["hover"]} !important;
        --gdg-bg-header-hovered: {colors["hover"]} !important;
        --gdg-bg-bubble: {colors["input"]} !important;
        --gdg-bg-bubble-selected: {colors["hover"]} !important;
        --gdg-border-color: {colors["border"]} !important;
        --gdg-horizontal-border-color: {colors["border"]} !important;
        --gdg-drilldown-border: {colors["text_muted"]} !important;
    }}
    [data-testid="stDataFrameResizable"] {{
        border-color: var(--pulse-border) !important;
    }}
    [data-testid="stTable"] thead {{ background: var(--pulse-table-header); }}
    [data-testid="stTable"] tbody tr:nth-child(even) {{
        background: var(--pulse-table-row-alt);
    }}
    [data-testid="stTable"] th,
    [data-testid="stTable"] td {{
        color: var(--pulse-text);
        border-color: var(--pulse-border);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

PAGES = {
    "Contributor Retention": [
        st.Page("pages/0_Contributor_Dashboard.py", title="Contributor Dashboard", icon=":material/monitoring:", default=True),
        st.Page("pages/1_Contributor_Insights.py", title="Onboarding Insights", icon=":material/lightbulb:"),
        st.Page("pages/2_Contributors.py", title="Contributors", icon=":material/group:"),
        st.Page("pages/3_PR_Analysis.py", title="PR Analysis", icon=":material/rate_review:"),
        st.Page("pages/4_Issue_Analysis.py", title="Issue Analysis", icon=":material/bug_report:"),
        st.Page("pages/5_Recommendations.py", title="Recommendations", icon=":material/task_alt:"),
    ],
    "Business Analytics": [
        st.Page(
            "pages/3_Executive_Summary.py",
            title="Executive Summary",
            icon=":material/speed:",
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
        st.Page(
            "pages/6_Dashboard_Layout.py",
            title="Dashboard Layout",
            icon=":material/view_quilt:",
        ),
    ],
}

with st.sidebar:
    st.markdown("### Open Pulse")
    st.toggle(
        "Dark mode",
        key="dark_mode",
        help="Switch the dashboard between light and dark appearance.",
        on_change=save_theme_preference,
    )
    st.caption(
        "Analytics over the outputs of the data pipeline in `scripts/`. "
        "Every figure is built from a committed artifact in `output/`."
    )

st.navigation(PAGES).run()
