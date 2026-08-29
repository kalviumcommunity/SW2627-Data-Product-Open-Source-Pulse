"""One visual language for every chart in the dashboard.

Defines the colour palette, the number formatters, and the matplotlib
defaults that all chart builders share. Importing this module and calling
``apply_matplotlib_theme()`` is the only styling step a chart should need.
"""

import re

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
# Semantic roles. These carry meaning and never rotate: reference lines are
# always neutral, targets always success, alerts always danger.
PALETTE = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "danger": "#d62728",
    "neutral": "#7f7f7f",
}

# Categorical series colours, drawn from the Okabe-Ito colour-blind safe set.
# The semantic palette above is deliberately not reused here: its green and
# red are a red-green pair that roughly 8% of men cannot distinguish, which
# is acceptable for a lone reference line but not for adjacent series.
CHART_COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00"]

# "Enterprise" is both a product line and a customer segment in this dataset.
# The two maps are kept separate and share no colour, so the charts never
# imply a relationship between the product and the segment of the same name.
PRODUCT_COLORS = {
    "Basic": "#56B4E9",
    "Pro": "#0072B2",
    "Enterprise": "#004C6D",
}
SEGMENT_COLORS = {
    "Enterprise": "#E69F00",
    "SMB": "#009E73",
    "Startup": "#CC79A7",
    "Individual": "#D55E00",
}

# KPI status ramp. Deliberately separate from CHART_COLORS: these three encode
# a judgement (on track / off track / flat), not a category, so they must not
# be reachable by the series colour cycle. The hexes match the ones
# funnel_analysis.py already uses, keeping one status vocabulary project-wide.
#
# This is a green-red pair, which colour vision deficiency flattens. Every KPI
# card therefore also carries an arrow and a written status, so colour is a
# reinforcement of the message and never the only carrier of it.
STATUS_COLORS = {
    "good": "#10b981",
    "bad": "#ef4444",
    "flat": "#f59e0b",
}

# Product tier is ordinal, so its three colours form a light-to-dark sequential
# ramp. Luminance alone separates them, which means the ramp survives greyscale
# printing and every form of colour vision deficiency without needing hatching.
# Customer segment is nominal, so it gets distinct hues plus a marker shape.
SEGMENT_MARKERS = {
    "Enterprise": "o",
    "SMB": "s",
    "Startup": "^",
    "Individual": "D",
}


# ---------------------------------------------------------------------------
# Number formatting
# ---------------------------------------------------------------------------
def fmt_currency(value, _pos=None):
    """Format a number as currency, scaling the unit to the magnitude.

    A fixed divisor cannot serve this project: product revenue peaks at
    $7,300 while customer lifetime value reaches $253,712. Dividing
    everything by 1e6 would label every product tick "$0.0M".
    """
    magnitude = abs(value)
    if magnitude >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if magnitude >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def fmt_count(value, _pos=None):
    """Format a plain count with thousands separators."""
    return f"{value:,.0f}"


def fmt_percent(value, decimals=1):
    """Format a 0-1 fraction as a percentage."""
    return f"{value * 100:.{decimals}f}%"


def md_safe(text):
    """Escape dollar signs so Streamlit does not read them as LaTeX.

    Streamlit's markdown treats ``$...$`` as a maths span. Two currency figures
    in one string therefore swallow everything between them and render it as an
    equation, which silently mangles any sentence quoting more than one amount.
    Escaping each dollar keeps the text literal.
    """
    if text is None:
        return None
    return re.sub(r"(?<!\\)\$", r"\\$", str(text))


def label_color(background_hex):
    """Return black or white text, whichever reads on the given fill colour."""
    red, green, blue = (
        int(background_hex.lstrip("#")[index : index + 2], 16) / 255
        for index in (0, 2, 4)
    )
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "#111111" if luminance > 0.5 else "#ffffff"


def currency_axis(ax, axis="y"):
    """Apply the currency formatter to one axis of a plot."""
    target = ax.yaxis if axis == "y" else ax.xaxis
    target.set_major_formatter(FuncFormatter(fmt_currency))


def count_axis(ax, axis="y"):
    """Apply the thousands-separator formatter to one axis of a plot."""
    target = ax.yaxis if axis == "y" else ax.xaxis
    target.set_major_formatter(FuncFormatter(fmt_count))


# ---------------------------------------------------------------------------
# Matplotlib defaults
# ---------------------------------------------------------------------------
def apply_matplotlib_theme():
    """Set the shared matplotlib defaults for every chart in the project."""
    mpl.use("Agg")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#cccccc",
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 12,
            "axes.prop_cycle": mpl.cycler(color=CHART_COLORS),
            "grid.color": "#dddddd",
            "grid.alpha": 0.6,
            "grid.linewidth": 0.7,
            "legend.frameon": True,
            "legend.framealpha": 0.9,
            "legend.fontsize": 10,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "figure.autolayout": False,
        }
    )


def annotation_box(facecolor="#fff8dc"):
    """Return the shared bbox style used by every callout annotation."""
    return {
        "boxstyle": "round,pad=0.45",
        "facecolor": facecolor,
        "edgecolor": PALETTE["neutral"],
        "alpha": 0.92,
    }


# ---------------------------------------------------------------------------
# Plotly
# ---------------------------------------------------------------------------
# The interactive charts must look like the static ones. Rather than restating
# colours in Plotly syntax, the template below is generated from the same
# PALETTE and CHART_COLORS defined above, so a palette change propagates to
# both rendering engines at once.
PLOTLY_TEMPLATE_NAME = "open_pulse"

HOVER_LABEL = {
    "bgcolor": "white",
    "bordercolor": "#cccccc",
    "font": {"size": 13, "family": "Helvetica, Arial, sans-serif"},
}


def register_plotly_template():
    """Register the project's Plotly template and make it the default.

    Plotly is imported lazily so that the matplotlib-only code path, including
    ``scripts/build_charts.py``, never needs it installed.
    """
    import plotly.graph_objects as go
    import plotly.io as pio

    if PLOTLY_TEMPLATE_NAME in pio.templates:
        pio.templates.default = PLOTLY_TEMPLATE_NAME
        return pio.templates[PLOTLY_TEMPLATE_NAME]

    template = go.layout.Template()
    template.layout = go.Layout(
        colorway=CHART_COLORS,
        font={"family": "Helvetica, Arial, sans-serif", "size": 13, "color": "#222222"},
        title={"font": {"size": 18, "color": "#111111"}, "x": 0.0, "xanchor": "left"},
        paper_bgcolor="white",
        plot_bgcolor="white",
        hoverlabel=HOVER_LABEL,
        margin={"l": 70, "r": 30, "t": 90, "b": 60},
        xaxis={
            "gridcolor": "#e6e6e6",
            "linecolor": "#cccccc",
            "zeroline": False,
            "title": {"font": {"size": 14}},
        },
        yaxis={
            "gridcolor": "#e6e6e6",
            "linecolor": "#cccccc",
            "zeroline": False,
            "title": {"font": {"size": 14}},
        },
        legend={
            "bgcolor": "rgba(255,255,255,0.9)",
            "bordercolor": "#cccccc",
            "borderwidth": 1,
        },
    )
    pio.templates[PLOTLY_TEMPLATE_NAME] = template
    pio.templates.default = PLOTLY_TEMPLATE_NAME
    return template


# Modebar configuration shared by every interactive chart. Zoom, pan, reset,
# and box/lasso select are Plotly defaults; this only removes the buttons that
# do not apply to business charts and names the PNG a viewer would download.
def plotly_config(filename="open_pulse_chart"):
    """Return the shared Plotly modebar configuration."""
    return {
        "displaylogo": False,
        "scrollZoom": True,
        "modeBarButtonsToRemove": ["autoScale2d"],
        "toImageButtonOptions": {
            "format": "png",
            "filename": filename,
            "scale": 2,
        },
    }
