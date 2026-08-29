"""Shared Streamlit building blocks for every dashboard page.

Keeps page files declarative: a page states which data it wants and which
chart to draw, and these helpers handle the layout, the metric strip, the
figure lifecycle, and the download control.
"""

import io

import matplotlib.pyplot as plt
import streamlit as st

from src.dashboard import theme


def page_header(title, subtitle, question=None):
    """Render a page title, a one-line summary, and the question it answers."""
    st.title(title)
    st.caption(subtitle)
    if question:
        st.markdown(f"**This page answers:** {question}")
    st.divider()


def kpi_row(metrics):
    """Render a row of headline metrics.

    Each metric is a dict with ``label``, ``value``, and an optional ``delta``
    and ``help`` entry.
    """
    columns = st.columns(len(metrics))
    for column, metric in zip(columns, metrics):
        column.metric(
            label=metric["label"],
            value=metric["value"],
            delta=metric.get("delta"),
            delta_color=metric.get("delta_color", "normal"),
            help=metric.get("help"),
        )


def figure_bytes(fig, dpi=200):
    """Return a rendered PNG of a figure as bytes, for the download control."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
    buffer.seek(0)
    return buffer.getvalue()


def chart_block(fig, insight, filename, chart_type=None, rationale=None, key=None):
    """Render a figure with its insight, its design rationale, and a download.

    The figure is closed after rendering. Streamlit reruns the page on every
    interaction, so leaving figures open would accumulate them for the life of
    the session.
    """
    image = figure_bytes(fig)
    st.pyplot(fig, width="stretch")
    plt.close(fig)

    st.info(insight, icon=":material/lightbulb:")

    left, right = st.columns([3, 1])
    if chart_type and rationale:
        with left.expander(f"Why a {chart_type.lower()}?"):
            st.markdown(rationale)
    right.download_button(
        "Download PNG",
        data=image,
        file_name=filename,
        mime="image/png",
        width="stretch",
        key=key,
    )


def plotly_block(figure, insight, filename, interactions=None, key=None):
    """Render an interactive Plotly figure with its insight and interactions.

    ``theme=None`` matters: Streamlit otherwise applies its own chart theme and
    silently overrides the project colours, so the interactive charts would
    stop matching the static ones.
    """
    st.plotly_chart(
        figure,
        width="stretch",
        theme=None,
        config=theme.plotly_config(filename),
        key=key,
    )
    st.info(insight, icon=":material/lightbulb:")
    if interactions:
        with st.expander("What you can do with this chart"):
            st.markdown(interactions)


def palette_swatches():
    """Render the project palette as inline colour swatches."""

    def swatch(label, value):
        return (
            f'<div style="display:flex;align-items:center;gap:.6rem;'
            f'margin:.25rem 0;font-size:.9rem;">'
            f'<span style="width:2.4rem;height:1.1rem;border-radius:3px;'
            f'background:{value};border:1px solid rgba(128,128,128,.45);"></span>'
            f"<code>{value}</code><span>{label}</span></div>"
        )

    left, right = st.columns(2)
    with left:
        st.markdown("**Semantic roles**")
        roles = [
            "Default single-series fill",
            "Second accent series",
            "Targets and healthy thresholds",
            "Alerts and annotation arrows",
            "Reference lines and source notes",
        ]
        html = "".join(
            swatch(role, value)
            for (_name, value), role in zip(theme.PALETTE.items(), roles)
        )
        st.markdown(html, unsafe_allow_html=True)
    with right:
        st.markdown("**Categorical series (Okabe-Ito)**")
        st.markdown(
            "".join(swatch("", value) for value in theme.CHART_COLORS),
            unsafe_allow_html=True,
        )


def missing_artifact_warning(error):
    """Explain a missing upstream artifact and how to regenerate it."""
    st.error(str(error), icon=":material/error:")
    st.caption(
        "The dashboard reads the outputs committed by the analysis scripts. "
        "Run the named script from the project root, then reload this page."
    )
