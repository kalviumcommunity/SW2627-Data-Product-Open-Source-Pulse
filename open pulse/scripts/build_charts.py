"""Render the five business charts and document them.

Builds every chart through ``src/dashboard/charts.py`` - the same builders the
Streamlit pages use - so the exported PNG files and the dashboard always show
identical figures. Writes the images and CHARTS_README.md into output/.

Run: python scripts/build_charts.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt  # noqa: E402

from src.dashboard import charts, config, data_loader, theme  # noqa: E402


EXPORT_DPI = 300


def save(fig, path):
    """Write a figure to disk at print resolution and release it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=EXPORT_DPI, bbox_inches="tight")
    plt.close(fig)
    size_kb = path.stat().st_size / 1024
    print(f"  saved {path.name:38s} ({size_kb:,.0f} KB)")
    return path


def build_all():
    """Build all five charts, returning the figures and their key statistics."""
    revenue_by_product = data_loader.load_revenue_by_product()
    pivot = data_loader.load_segment_product_pivot()
    segment_metrics = data_loader.load_segment_metrics()
    trend = data_loader.load_revenue_trend()
    customers = data_loader.load_customer_segment_data()
    distribution_stats = data_loader.load_value_distribution_stats()

    figures = {
        1: charts.build_revenue_by_product(revenue_by_product),
        2: charts.build_revenue_trend(trend),
        3: charts.build_value_distribution(customers, distribution_stats),
        4: charts.build_revenue_composition(pivot, segment_metrics),
    }
    figures[5], correlation = charts.build_tickets_vs_value(customers)

    total_revenue = float(revenue_by_product.sum())
    facts = {
        "leader": str(revenue_by_product.index[0]),
        "leader_share": float(revenue_by_product.iloc[0]) / total_revenue,
        "total_revenue": total_revenue,
        "trend": data_loader.load_revenue_trend_summary(),
        "days": len(trend),
        "period_start": trend.index.min(),
        "period_end": trend.index.max(),
        "distribution": distribution_stats,
        "top_segment": str(segment_metrics["total_revenue"].idxmax()),
        "top_segment_share": float(segment_metrics["revenue_contribution"].max()) / 100,
        "correlation": correlation,
        "customer_count": len(customers),
    }
    return figures, facts


def write_readme(facts):
    """Write CHARTS_README.md describing every chart and design decision."""
    stats = facts["distribution"]
    palette_rows = "\n".join(
        f"| `{name}` | `{value}` | {role} |"
        for (name, value), role in zip(
            theme.PALETTE.items(),
            [
                "Default single-series fill",
                "Second series where a semantic accent is needed",
                "Targets, medians, and healthy thresholds",
                "Alerts, means on skewed data, and annotation arrows",
                "Reference lines, raw noise series, and source notes",
            ],
        )
    )

    content = f"""# Analysis Visualizations

Five charts covering the five core business data relationships. Every figure is
built by `src/dashboard/charts.py` and rendered by `python scripts/build_charts.py`
at {EXPORT_DPI} DPI. The Streamlit page **Business Overview** displays the same
builders, so these files and the dashboard cannot drift apart.

---

## Chart 1: Revenue by Product Line

![Chart 1](chart1_revenue_by_product.png)

- **Type:** Horizontal bar chart
- **Relationship:** Comparison across categories
- **Question:** Which product line generates the most revenue?
- **Data:** `output/segment_product_revenue_pivot.csv` (`analyze_segments.py`)
- **Key insight:** {facts['leader']} generates {theme.fmt_currency(facts['total_revenue'] * facts['leader_share'])}, or {facts['leader_share']:.1%} of the {theme.fmt_currency(facts['total_revenue'])} total.
- **Labels:** Title, x-axis "Revenue (USD)", y-axis "Product Line", currency data label on every bar, legend for the reference line.
- **Annotation:** Callout with arrow on the leading bar, plus a dashed vertical reference line at the average revenue per product so each bar reads as above or below par.
- **Why horizontal:** Product names are words, not quantities. Horizontal bars keep them readable without rotation.

## Chart 2: Daily Revenue Trend

![Chart 2](chart2_revenue_trend.png)

- **Type:** Multi-series line chart
- **Relationship:** Trend over time
- **Question:** Is revenue genuinely growing, or is the daily movement noise?
- **Data:** `output/revenue_trend_features.csv` (`analyze_revenue_trends.py`)
- **Key insight:** The 30-day average rose {facts['trend']['trend_magnitude_pct']:.1f}% over the period, so the trend is {facts['trend']['trend_direction']} rather than random daily variation.
- **Labels:** Title, x-axis "Date" formatted as `05 Jan`, y-axis "Revenue (USD)", legend naming all four series.
- **Annotation:** Arrow marking the peak day, plus a dotted reference line at the period average.
- **Scope note:** The source covers **{facts['days']} days** ({facts['period_start']:%d %b %Y} to {facts['period_end']:%d %b %Y}), not twelve months, and carries no product dimension. The three series are the raw values against their 7- and 30-day rolling averages. Titling this "12-month revenue by top 3 products" would describe data the project does not have.

## Chart 3: Customer Lifetime Value Distribution

![Chart 3](chart3_value_distribution.png)

- **Type:** Histogram, logarithmic value axis
- **Relationship:** Distribution of values
- **Question:** What is a typical customer worth, and how spread out is customer value?
- **Data:** `output/customer_segment_data.csv` ({stats['count']:,} customers)
- **Key insight:** Values run from {theme.fmt_currency(stats['min'])} to {theme.fmt_currency(stats['max'])} with skewness {stats['skewness']:.2f}. The mean of {theme.fmt_currency(stats['mean'])} sits {stats['mean'] / stats['median']:.1f}x above the median of {theme.fmt_currency(stats['median'])}, so the median is the honest headline figure.
- **Labels:** Title carrying the sample size, x-axis "Lifetime Value (USD, logarithmic scale)", y-axis "Number of Customers", legend for the median and mean lines.
- **Annotation:** Median and mean reference lines with a callout explaining why they differ, and a marker on the 99th percentile at {theme.fmt_currency(stats['percentiles']['0.99'])}.
- **Why logarithmic:** The range spans more than 5,000x. On a linear axis every customer below $50,000 collapses into a single bar and the shape of the distribution disappears.
- **Statistics source:** computed by `analyze_revenue_distribution.analyze_revenue()`, the same function behind `output/revenue_distribution_analysis.json`, called here on the larger customer dataset.

## Chart 4: Revenue Composition by Segment and Product

![Chart 4](chart4_revenue_composition.png)

- **Type:** Stacked bar chart
- **Relationship:** Composition and part-to-whole
- **Question:** How does each customer segment's revenue break down across product tiers?
- **Data:** `output/segment_product_revenue_pivot.csv` (`analyze_segments.py`)
- **Key insight:** The {facts['top_segment']} segment contributes {facts['top_segment_share']:.1%} of revenue, and within every segment the Enterprise product tier is the largest component.
- **Labels:** Title, x-axis "Customer Segment", y-axis "Revenue (USD)", legend titled "Product Line", currency labels inside each visible stack, segment total and share above each bar.
- **Annotation:** Callout tying the leading segment's revenue share to its customer count.
- **Segment count:** three products, within the five-segment readability limit.

## Chart 5: Support Tickets vs Customer Lifetime Value

![Chart 5](chart5_tickets_vs_value.png)

- **Type:** Scatter plot with fitted trend line
- **Relationship:** Correlation between two variables
- **Question:** Do higher-value customers generate more support load?
- **Data:** `output/customer_segment_data.csv` ({facts['customer_count']:,} customers)
- **Key insight:** Pearson r = {facts['correlation']['pearson']:.2f}, Spearman rho = {facts['correlation']['spearman']:.2f}. Ticket volume rises with customer value, which reframes support cost as a consequence of account size rather than a symptom of dissatisfaction.
- **Labels:** Title, x-axis "Support Tickets (count per customer)", y-axis "Lifetime Value (USD, logarithmic scale)", legend titled "Customer Segment" with the sample size per segment, correlation coefficients in a fixed panel.
- **Annotation:** Callout on the Enterprise cluster naming its average tickets and average value.
- **Substitution note:** The brief asks for marketing spend against revenue. The repository holds no marketing spend column in any raw or processed file, so the strongest genuine relationship in the data was used instead. `data/raw/correlation_data.csv` was rejected as a source: its `engagement` and `transactions_per_month` columns correlate at exactly r = 1.000, a synthetic artefact that plots as a straight line.
- **Caution:** Correlation is association, not causation. This is the same caveat `analyze_correlations.py` records in `output/correlation_business_analysis.json`.

---

## Colour Palette

Two palettes are defined in `src/dashboard/theme.py`. Semantic colours carry a
fixed meaning and never rotate:

| Token | Hex | Role |
|---|---|---|
{palette_rows}

Categorical series use the Okabe-Ito colour-blind safe set:

`{'`, `'.join(theme.CHART_COLORS)}`

**Why two palettes.** The semantic set pairs `success` green with `danger` red.
That is safe for a lone reference line read against a label, but placing the two
adjacent as neighbouring series would be unreadable for the roughly 8% of men
with red-green colour vision deficiency. Categorical series therefore come from
Okabe-Ito, which is distinguishable under all common forms of colour blindness.

**Fixed assignments.** `Basic`, `Pro`, and `Enterprise` hold the same colour in
every chart, as do the customer segments. `Enterprise` is both a product line
and a customer segment in this dataset, so the two maps deliberately share no
colour, and every axis label and legend title names its dimension explicitly
("Product Line", "Customer Segment"). A viewer must never read the Enterprise
product and the Enterprise segment as the same thing.

**Encoding beyond colour.** Product tier is ordinal, so its three colours form
a light-to-dark sequential ramp: luminance alone separates Basic, Pro, and
Enterprise, which survives greyscale printing without needing hatching.
Customer segment is nominal, so it gets distinct hues plus a distinct marker
shape per segment. No chart relies on hue alone to carry meaning.

## Number Formatting

`theme.fmt_currency` scales its unit to the magnitude of the value: `$7.3K` for
product revenue, `$253.7K` for customer value, `$1.2M` above a million. A fixed
`value / 1e6` divisor cannot serve this project - product revenue peaks at
{theme.fmt_currency(facts['total_revenue'] * facts['leader_share'])}, which would label every axis tick `$0.0M`.

## Regenerating

```
python scripts/build_charts.py
```

Requires the upstream artifacts in `output/`. If one is missing, the script
names the analysis script that produces it.
"""
    config.CHARTS_README.write_text(content, encoding="utf-8")
    print(f"  saved {config.CHARTS_README.name:38s} "
          f"({config.CHARTS_README.stat().st_size / 1024:,.0f} KB)")


def main():
    """Render every chart, write the documentation, and report the results."""
    print("=" * 70)
    print("BUILDING BUSINESS VISUALIZATIONS")
    print("=" * 70)
    print(f"Output directory: {config.OUTPUT_DIR}")
    print()

    figures, facts = build_all()
    for number, figure in figures.items():
        save(figure, config.CHART_FILES[number])
    write_readme(facts)

    print()
    print("=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)
    print(f"  Total revenue                {theme.fmt_currency(facts['total_revenue'])}")
    print(f"  Leading product              {facts['leader']} ({facts['leader_share']:.1%} of revenue)")
    print(f"  Trend direction              {facts['trend']['trend_direction'].upper()} "
          f"({facts['trend']['trend_magnitude_pct']:.1f}% over {facts['days']} days)")
    print(f"  Lifetime value skewness      {facts['distribution']['skewness']:.2f} "
          f"(median {theme.fmt_currency(facts['distribution']['median'])}, "
          f"mean {theme.fmt_currency(facts['distribution']['mean'])})")
    print(f"  Leading segment              {facts['top_segment']} ({facts['top_segment_share']:.1%} of revenue)")
    print(f"  Tickets vs value             Pearson r = {facts['correlation']['pearson']:.2f}, "
          f"Spearman rho = {facts['correlation']['spearman']:.2f}")
    print()
    print(f"{len(figures)} charts and 1 README written to output/")


if __name__ == "__main__":
    main()
