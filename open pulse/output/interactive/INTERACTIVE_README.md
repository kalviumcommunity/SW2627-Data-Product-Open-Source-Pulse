# Interactive Charts

Four Plotly charts covering hover detail, metric switching, and free-form
exploration. Built by `src/dashboard/interactive.py` and exported by
`python scripts/build_interactive_charts.py`. The Streamlit page
**Interactive Explorer** renders the same figure objects, so these files and
the dashboard cannot drift apart.

Open any `.html` file directly in a browser. No Python and no server are
required. The Plotly library is loaded from the Plotly CDN, so the page needs an internet connection on first open.

---

## chart1_revenue_trend.html

- **Question:** How did revenue move day to day, and what sat behind each day?
- **Data:** `output/revenue_trend_features.csv` (59 days, 01 Jan to 28 Feb 2025)
- **Hover:** four fields the axes do not show - order count, average order
  value, and the 7-day average - under a unified `x` hover, so one pointer
  position reads every series at that date at once.
- **Range selector:** 7D / 14D / 1M / All buttons above the plot.
- **Range slider:** the strip beneath the plot; drag either handle for any
  custom window.
- **Note on the buttons:** the source spans 59 days, so the
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
- **Data:** `output/customer_segment_data.csv` (1,000 customers), Pearson r = 0.52
- **Interactions:**
  - **Zoom** - click and drag any region
  - **Pan** - hold shift and drag, or pick the pan tool in the mode bar
  - **Reset** - double-click anywhere on the plot
  - **Box / lasso select** - pick either tool in the mode bar and draw
  - **Isolate a segment** - click a legend entry to hide it, double-click to
    show it alone
- **Hover:** customer id, region, product tier, lifetime value, ticket count,
  and retention days, so a single point identifies a real account.
- **Why interactive here:** 1,000 points overplot badly in a
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
