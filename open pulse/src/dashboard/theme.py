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
THEME_TOKENS = {
    "light": {
        "background": "#F8FAFC",
        "surface": "#FFFFFF",
        "table": "#FFFFFF",
        "input": "#FFFFFF",
        "sidebar": "#FFFFFF",
        "navbar": "#FFFFFF",
        "text": "#0F172A",
        "text_secondary": "#64748B",
        "text_muted": "#94A3B8",
        "border": "#E2E8F0",
        "strong_border": "#CBD5E1",
        "primary": "#0C0C3C",
        "secondary": "#53C5CC",
        "success": "#16A34A",
        "warning": "#D97706",
        "danger": "#DC2626",
        "hover": "#F1F5F9",
        "active": "#E2E8F0",
        "table_header": "#F1F5F9",
        "table_alt": "#F8FAFC",
        "grid": "#E2E8F0",
        "callout": "#EFF6FF",
        "shadow": "rgba(15, 23, 42, .10)",
    },
    "dark": {
        "background": "#000000",
        "surface": "#111111",
        "table": "#0D0D0D",
        "input": "#151515",
        "sidebar": "#050505",
        "navbar": "#000000",
        "text": "#FFFFFF",
        "text_secondary": "#D4D4D4",
        "text_muted": "#A3A3A3",
        "border": "#2F2F2F",
        "strong_border": "#444444",
        "primary": "#53C5CC",
        "secondary": "#53C5CC",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",
        "hover": "#202020",
        "active": "#2A2A2A",
        "table_header": "#202020",
        "table_alt": "#111111",
        "grid": "#2F2F2F",
        "callout": "#202020",
        "shadow": "rgba(0, 0, 0, .45)",
    },
}

_DARK_MODE = False
ACTIVE_THEME = THEME_TOKENS["light"]
PALETTE = {
    "primary": ACTIVE_THEME["primary"],
    "secondary": ACTIVE_THEME["secondary"],
    "success": ACTIVE_THEME["success"],
    "danger": ACTIVE_THEME["danger"],
    "neutral": ACTIVE_THEME["text_secondary"],
}

# Categorical series colours, drawn from the Okabe-Ito colour-blind safe set.
# The semantic palette above is deliberately not reused here: its green and
# red are a red-green pair that roughly 8% of men cannot distinguish, which
# is acceptable for a lone reference line but not for adjacent series.
CHART_COLORS_LIGHT = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00"]
CHART_COLORS_DARK = ["#53C5CC", "#F59E0B", "#22C55E", "#F472B6", "#38BDF8", "#FB7185"]
CHART_COLORS = list(CHART_COLORS_LIGHT)

# "Enterprise" is both a product line and a customer segment in this dataset.
# The two maps are kept separate and share no colour, so the charts never
# imply a relationship between the product and the segment of the same name.
PRODUCT_COLORS_LIGHT = {
    "Basic": "#56B4E9",
    "Pro": "#0072B2",
    "Enterprise": "#004C6D",
}
PRODUCT_COLORS_DARK = {
    "Basic": "#67E8F9",
    "Pro": "#53C5CC",
    "Enterprise": "#C084FC",
}
PRODUCT_COLORS = dict(PRODUCT_COLORS_LIGHT)
SEGMENT_COLORS_LIGHT = {
    "Enterprise": "#E69F00",
    "SMB": "#009E73",
    "Startup": "#CC79A7",
    "Individual": "#D55E00",
}
SEGMENT_COLORS_DARK = {
    "Enterprise": "#F59E0B",
    "SMB": "#22C55E",
    "Startup": "#F472B6",
    "Individual": "#FB923C",
}
SEGMENT_COLORS = dict(SEGMENT_COLORS_LIGHT)

# KPI status ramp. Deliberately separate from CHART_COLORS: these three encode
# a judgement (on track / off track / flat), not a category, so they must not
# be reachable by the series colour cycle. The hexes match the ones
# funnel_analysis.py already uses, keeping one status vocabulary project-wide.
#
# This is a green-red pair, which colour vision deficiency flattens. Every KPI
# card therefore also carries an arrow and a written status, so colour is a
# reinforcement of the message and never the only carrier of it.
STATUS_COLORS = {
    "good": ACTIVE_THEME["success"],
    "bad": ACTIVE_THEME["danger"],
    "flat": ACTIVE_THEME["warning"],
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


def fmt_currency_exec(value):
    """Money rounded to the precision an executive actually reads.

    "$12.1M" lands; "$12,094,579" invites the reader to check the arithmetic
    instead of the argument. Exact figures belong in the technical appendix.
    Differs from ``fmt_currency`` by dropping the decimal on thousands.
    """
    magnitude = abs(value)
    if magnitude >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if magnitude >= 1_000:
        return f"${value / 1_000:,.0f}K"
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


def active_tokens():
    """Return the semantic tokens for the currently selected appearance."""
    return ACTIVE_THEME


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
            "figure.facecolor": ACTIVE_THEME["surface"],
            "axes.facecolor": ACTIVE_THEME["surface"],
            "axes.edgecolor": ACTIVE_THEME["border"],
            "text.color": ACTIVE_THEME["text"],
            "axes.labelcolor": ACTIVE_THEME["text_secondary"],
            "xtick.color": ACTIVE_THEME["text_secondary"],
            "ytick.color": ACTIVE_THEME["text_secondary"],
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 12,
            "axes.prop_cycle": mpl.cycler(color=CHART_COLORS),
            "grid.color": ACTIVE_THEME["grid"],
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


def annotation_box(facecolor=None):
    """Return the shared bbox style used by every callout annotation."""
    facecolor = facecolor or ACTIVE_THEME["callout"]
    return {
        "boxstyle": "round,pad=0.45",
        "facecolor": facecolor,
        "edgecolor": ACTIVE_THEME["border"],
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
PLOTLY_DARK_TEMPLATE_NAME = "open_pulse_dark"
ALTAIR_THEME_NAME = "open_pulse"
ALTAIR_DARK_THEME_NAME = "open_pulse_dark"

HOVER_LABEL = {
    "bgcolor": ACTIVE_THEME["surface"],
    "bordercolor": ACTIVE_THEME["border"],
    "font": {"size": 13, "family": "Helvetica, Arial, sans-serif"},
}


def set_dark_mode(enabled):
    """Set the chart appearance to match the dashboard shell."""
    import altair as alt

    global _DARK_MODE, ACTIVE_THEME
    _DARK_MODE = bool(enabled)
    ACTIVE_THEME = THEME_TOKENS["dark" if _DARK_MODE else "light"]
    PALETTE.update(
        {
            "primary": ACTIVE_THEME["primary"],
            "secondary": ACTIVE_THEME["secondary"],
            "success": ACTIVE_THEME["success"],
            "danger": ACTIVE_THEME["danger"],
            "neutral": ACTIVE_THEME["text_secondary"],
        }
    )
    STATUS_COLORS.update(
        {
            "good": ACTIVE_THEME["success"],
            "bad": ACTIVE_THEME["danger"],
            "flat": ACTIVE_THEME["warning"],
        }
    )
    HOVER_LABEL.update(
        {"bgcolor": ACTIVE_THEME["surface"], "bordercolor": ACTIVE_THEME["border"]}
    )
    CHART_COLORS[:] = CHART_COLORS_DARK if _DARK_MODE else CHART_COLORS_LIGHT
    PRODUCT_COLORS.clear()
    PRODUCT_COLORS.update(PRODUCT_COLORS_DARK if _DARK_MODE else PRODUCT_COLORS_LIGHT)
    SEGMENT_COLORS.clear()
    SEGMENT_COLORS.update(SEGMENT_COLORS_DARK if _DARK_MODE else SEGMENT_COLORS_LIGHT)
    theme_name = ALTAIR_DARK_THEME_NAME if _DARK_MODE else ALTAIR_THEME_NAME
    if theme_name not in alt.themes.names():
        text_color = ACTIVE_THEME["text"]
        grid_color = ACTIVE_THEME["grid"]
        background = ACTIVE_THEME["background"]

        def chart_theme():
            return {
                "config": {
                    "background": background,
                    "axis": {
                        "labelColor": text_color,
                        "titleColor": text_color,
                        "domainColor": grid_color,
                        "gridColor": grid_color,
                    },
                    "legend": {
                        "labelColor": text_color,
                        "titleColor": text_color,
                    },
                    "title": {"color": text_color},
                    "view": {"stroke": "transparent"},
                }
            }

        alt.themes.register(theme_name, chart_theme)
    alt.themes.enable(theme_name)


def register_plotly_template():
    """Register the project's Plotly template and make it the default.

    Plotly is imported lazily so that the matplotlib-only code path, including
    ``scripts/build_charts.py``, never needs it installed.
    """
    import plotly.graph_objects as go
    import plotly.io as pio

    template_name = PLOTLY_DARK_TEMPLATE_NAME if _DARK_MODE else PLOTLY_TEMPLATE_NAME
    if template_name in pio.templates:
        pio.templates.default = template_name
        return pio.templates[template_name]

    template = go.layout.Template()
    paper_background = ACTIVE_THEME["surface"]
    plot_background = ACTIVE_THEME["background"]
    text_color = ACTIVE_THEME["text"]
    grid_color = ACTIVE_THEME["grid"]
    line_color = ACTIVE_THEME["border"]
    template.layout = go.Layout(
        colorway=CHART_COLORS,
        font={"family": "Helvetica, Arial, sans-serif", "size": 13, "color": text_color},
        title={"font": {"size": 18, "color": text_color}, "x": 0.0, "xanchor": "left"},
        paper_bgcolor=paper_background,
        plot_bgcolor=plot_background,
        hoverlabel=HOVER_LABEL,
        margin={"l": 70, "r": 30, "t": 90, "b": 60},
        xaxis={
            "gridcolor": grid_color,
            "linecolor": line_color,
            "zeroline": False,
            "title": {"font": {"size": 14, "color": text_color}},
        },
        yaxis={
            "gridcolor": grid_color,
            "linecolor": line_color,
            "zeroline": False,
            "title": {"font": {"size": 14, "color": text_color}},
        },
        legend={
            "bgcolor": ACTIVE_THEME["surface"],
            "bordercolor": line_color,
            "borderwidth": 1,
        },
    )
    pio.templates[template_name] = template
    pio.templates.default = template_name
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
