"""Shared paths and artifact names for the dashboard and chart builders.

Every path is resolved from this file's location rather than the working
directory, so charts render identically whether they are produced by
``scripts/build_charts.py``, by Streamlit, or from an arbitrary shell.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SQL_DIR = PROJECT_ROOT / "sql"

# Analytics database. Gitignored: it is rebuilt from the committed artifacts.
DB_PATH = DATA_DIR / "open_pulse.db"
KPI_VIEWS_SQL = SQL_DIR / "analytics" / "kpi_views.sql"

# Artifacts produced by the analysis scripts and consumed by the dashboard.
SEGMENT_REVENUE_PIVOT = OUTPUT_DIR / "segment_product_revenue_pivot.csv"
SEGMENT_METRICS = OUTPUT_DIR / "segment_metrics.csv"
PRODUCT_SEGMENT_METRICS = OUTPUT_DIR / "product_segment_metrics.csv"
SEGMENT_INSIGHTS = OUTPUT_DIR / "segment_insights.csv"
SEGMENT_SUMMARY = OUTPUT_DIR / "segment_analysis_summary.json"
REVENUE_TREND_FEATURES = OUTPUT_DIR / "revenue_trend_features.csv"
REVENUE_TREND_SUMMARY = OUTPUT_DIR / "revenue_trend_analysis.json"
CUSTOMER_SEGMENT_DATA = OUTPUT_DIR / "customer_segment_data.csv"
DAILY_METRICS = OUTPUT_DIR / "daily_metrics.csv"

# KPI outputs
KPI_SUMMARY = OUTPUT_DIR / "kpi_summary.csv"
KPI_LINEAGE = OUTPUT_DIR / "KPI_LINEAGE.md"

# Chart files written by scripts/build_charts.py.
CHART_FILES = {
    1: OUTPUT_DIR / "chart1_revenue_by_product.png",
    2: OUTPUT_DIR / "chart2_revenue_trend.png",
    3: OUTPUT_DIR / "chart3_value_distribution.png",
    4: OUTPUT_DIR / "chart4_revenue_composition.png",
    5: OUTPUT_DIR / "chart5_tickets_vs_value.png",
}
CHARTS_README = OUTPUT_DIR / "CHARTS_README.md"

# Narrative evidence charts and the standalone story document.
DOCS_DIR = PROJECT_ROOT / "docs"
NARRATIVE_CHARTS = {
    "churn_by_segment": OUTPUT_DIR / "narrative1_churn_by_segment.png",
    "paradox": OUTPUT_DIR / "narrative2_ticket_paradox.png",
    "opportunity": OUTPUT_DIR / "narrative3_where_the_value_is.png",
}
CHURN_NARRATIVE = DOCS_DIR / "CHURN_NARRATIVE.md"
EXECUTIVE_SUMMARY = DOCS_DIR / "EXECUTIVE_SUMMARY.md"
TECHNICAL_ANALYSIS = DOCS_DIR / "TECHNICAL_ANALYSIS.md"
AUDIENCE_VERSIONS = DOCS_DIR / "AUDIENCE_VERSIONS.md"
NARRATIVE_REVIEW = DOCS_DIR / "NARRATIVE_REVIEW.md"

# Interactive Plotly exports live in their own folder so they never collide
# with the static PNG report documented by CHARTS_README.md.
INTERACTIVE_DIR = OUTPUT_DIR / "interactive"
INTERACTIVE_FILES = {
    "revenue_trend": INTERACTIVE_DIR / "chart1_revenue_trend.html",
    "product_performance": INTERACTIVE_DIR / "chart2_product_performance.html",
    "metric_selector": INTERACTIVE_DIR / "chart3_metric_selector.html",
    "scatter_explorer": INTERACTIVE_DIR / "chart4_interactive_scatter.html",
}
INTERACTIVE_README = INTERACTIVE_DIR / "INTERACTIVE_README.md"

# Order used for every product axis, legend, and colour lookup.
PRODUCT_ORDER = ["Basic", "Pro", "Enterprise"]
