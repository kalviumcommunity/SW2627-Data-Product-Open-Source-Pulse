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

# Artifacts produced by the analysis scripts and consumed by the dashboard.
SEGMENT_REVENUE_PIVOT = OUTPUT_DIR / "segment_product_revenue_pivot.csv"
SEGMENT_METRICS = OUTPUT_DIR / "segment_metrics.csv"
SEGMENT_INSIGHTS = OUTPUT_DIR / "segment_insights.csv"
SEGMENT_SUMMARY = OUTPUT_DIR / "segment_analysis_summary.json"
REVENUE_TREND_FEATURES = OUTPUT_DIR / "revenue_trend_features.csv"
REVENUE_TREND_SUMMARY = OUTPUT_DIR / "revenue_trend_analysis.json"
CUSTOMER_SEGMENT_DATA = OUTPUT_DIR / "customer_segment_data.csv"

# Chart files written by scripts/build_charts.py.
CHART_FILES = {
    1: OUTPUT_DIR / "chart1_revenue_by_product.png",
    2: OUTPUT_DIR / "chart2_revenue_trend.png",
    3: OUTPUT_DIR / "chart3_value_distribution.png",
    4: OUTPUT_DIR / "chart4_revenue_composition.png",
    5: OUTPUT_DIR / "chart5_tickets_vs_value.png",
}
CHARTS_README = OUTPUT_DIR / "CHARTS_README.md"

# Order used for every product axis, legend, and colour lookup.
PRODUCT_ORDER = ["Basic", "Pro", "Enterprise"]
