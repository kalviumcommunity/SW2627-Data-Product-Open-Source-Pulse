"""Export the interactive Plotly charts as standalone HTML files.

Builds every figure through ``src/dashboard/interactive.py`` - the same
builders the Streamlit page uses - and writes them to output/interactive/,
alongside a README describing each chart's interactions.

Run: python scripts/build_interactive_charts.py
     python scripts/build_interactive_charts.py --offline
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard import config, data_loader, interactive, theme  # noqa: E402


def save(figure, path, plotlyjs):
    """Write a figure as a self-contained interactive HTML page."""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(
        path,
        include_plotlyjs=plotlyjs,
        full_html=True,
        config=theme.plotly_config(path.stem),
        # Without a fixed id, Plotly mints a fresh UUID for the container div on
        # every export, so rebuilding produces a one-line diff in each file even
        # when nothing about the chart changed.
        div_id=f"chart-{path.stem}",
    )
    size_kb = path.stat().st_size / 1024
    print(f"  saved {path.name:38s} ({size_kb:>7,.0f} KB)")


def build_all():
    """Build every interactive figure and return it with its key statistics."""
    trend = data_loader.load_revenue_trend()
    product_metrics = data_loader.load_product_metrics()
    customers = data_loader.load_customer_segment_data()

    figures = {
        "revenue_trend": interactive.build_revenue_trend(trend),
        "product_performance": interactive.build_product_performance(product_metrics),
        "metric_selector": interactive.build_metric_selector(product_metrics),
    }
    figures["scatter_explorer"], correlation = interactive.build_scatter_explorer(
        customers
    )

    facts = {
        "days": len(trend),
        "period_start": trend.index.min(),
        "period_end": trend.index.max(),
        "products": list(product_metrics.index),
        "customers": len(customers),
        "correlation": correlation["pearson"],
    }
    return figures, facts


def write_readme(facts, plotlyjs):
    """Describe every interactive chart and the interactions it supports."""
    delivery = (
        "loaded from the Plotly CDN, so the page needs an internet connection "
        "on first open"
        if plotlyjs == "cdn"
        else "embedded in the file, so the page works with no network at all"
    )
    content = f"""# Interactive Charts

Four Plotly charts covering hover detail, metric switching, and free-form
exploration. Built by `src/dashboard/interactive.py` and exported by
`python scripts/build_interactive_charts.py`. The Streamlit page
**Interactive Explorer** renders the same figure objects, so these files and
the dashboard cannot drift apart.

Open any `.html` file directly in a browser. No Python and no server are
required. The Plotly library is {delivery}.

---

## chart1_revenue_trend.html

- **Question:** How did revenue move day to day, and what sat behind each day?
- **Data:** `output/revenue_trend_features.csv` ({facts['days']} days, {facts['period_start']:%d %b} to {facts['period_end']:%d %b %Y})
- **Hover:** four fields the axes do not show - order count, average order
  value, and the 7-day average - under a unified `x` hover, so one pointer
  position reads every series at that date at once.
- **Range selector:** 7D / 14D / 1M / All buttons above the plot.
- **Range slider:** the strip beneath the plot; drag either handle for any
  custom window.
- **Note on the buttons:** the source spans {facts['days']} days, so the
  buttons step in days and weeks. The 3M, 6M, and YTD buttons of a
  twelve-month chart would select ranges this dataset does not contain.

## chart2_product_performance.html

- **Question:** How much does each product line earn, and from how many customers?
- **Data:** `output/product_segment_metrics.csv`, rolled up to product level
- **Hover:** revenue, customer count, average revenue per customer, and share
  of total revenue - four fields, within the three-to-five range that stays
  scannable.
- **Why this matters:** the bar shows revenue only. The hover answers "is that
  revenue from many small customers or few large ones?" without a second chart.

## chart3_metric_selector.html

- **Question:** Which product leads on revenue, on customer count, and on
  average customer value?
- **Interaction:** the **Metric** dropdown switches between the three, and the
  y-axis title, tick format, and range switch with it.
- **How it works:** all three traces are added up front and the dropdown
  toggles `visible`. Nothing is re-fetched or re-computed, so the switch is
  instant.
- **The finding:** the ranking is identical on revenue and average value but
  flat on customer count - every tier holds the same number of customers, so
  the revenue gap is entirely price, not volume.

## chart4_interactive_scatter.html

- **Question:** Does support load rise with customer value, and which
  customers sit outside the pattern?
- **Data:** `output/customer_segment_data.csv` ({facts['customers']:,} customers), Pearson r = {facts['correlation']:.2f}
- **Interactions:**
  - **Zoom** - click and drag any region
  - **Pan** - hold shift and drag, or pick the pan tool in the mode bar
  - **Reset** - double-click anywhere on the plot
  - **Box / lasso select** - pick either tool in the mode bar and draw
  - **Isolate a segment** - click a legend entry to hide it, double-click to
    show it alone
- **Hover:** customer id, region, product tier, lifetime value, ticket count,
  and retention days, so a single point identifies a real account.
- **Why interactive here:** {facts['customers']:,} points overplot badly in a
  static image. Zoom is what makes the individual customer readable.

---

## Which range control to use

Both controls exist on chart 1, because they answer different needs.

**Range selector buttons** suit known, named periods. A viewer who wants "the
last month" gets it in one click, with no dragging and no chance of selecting
a slightly wrong window. Use buttons when the periods people ask for are
predictable - last week, last quarter, year to date.

**The range slider** suits arbitrary windows. A viewer who wants "the middle
three weeks of February, because that is when the campaign ran" cannot express
that as a button, and the slider gives it directly while keeping the full
series visible for context.

Offering both is the normal choice for a business time series: the buttons
carry the common cases and the slider carries everything else.

## Regenerating

```
python scripts/build_interactive_charts.py            # Plotly from CDN, small files
python scripts/build_interactive_charts.py --offline  # Plotly embedded, works offline
```
"""
    config.INTERACTIVE_README.write_text(content, encoding="utf-8")
    size_kb = config.INTERACTIVE_README.stat().st_size / 1024
    print(f"  saved {config.INTERACTIVE_README.name:38s} ({size_kb:>7,.0f} KB)")


def main():
    """Export every interactive chart and its documentation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="embed plotly.js in each file so it opens with no network",
    )
    arguments = parser.parse_args()
    plotlyjs = True if arguments.offline else "cdn"

    print("=" * 70)
    print("BUILDING INTERACTIVE CHARTS")
    print("=" * 70)
    print(f"Output directory: {config.INTERACTIVE_DIR}")
    print(f"Plotly library:   {'embedded (offline)' if arguments.offline else 'CDN'}")
    print()

    figures, facts = build_all()
    for key, figure in figures.items():
        save(figure, config.INTERACTIVE_FILES[key], plotlyjs)
    write_readme(facts, plotlyjs)

    print()
    print(f"{len(figures)} interactive charts and 1 README written to "
          f"output/{config.INTERACTIVE_DIR.name}/")


if __name__ == "__main__":
    main()
