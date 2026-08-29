"""Page: interactive Plotly charts the viewer drives themselves.

Reached through ``src/dashboard/app.py``, which puts the project root on
sys.path before this module is imported.
"""

import streamlit as st

from src.dashboard import components, config, data_loader, interactive, theme


def sidebar_filters(customers):
    """Render the customer filters and return the filtered frame.

    The filters are scoped to the customer-level section. The revenue trend and
    the product charts aggregate different sources with no customer dimension,
    so applying these controls to them would be misleading.
    """
    with st.sidebar:
        st.markdown("### Customer filters")
        st.caption(
            "These apply to the customer explorer and its table below. "
            "The revenue and product charts come from separate aggregates."
        )

        segments = sorted(customers["customer_type"].unique())
        chosen_segments = st.multiselect(
            "Customer segment", segments, default=segments
        )

        regions = sorted(customers["region"].unique())
        chosen_regions = st.multiselect("Region", regions, default=regions)

        max_tickets = int(customers["support_tickets"].max())
        ticket_range = st.slider(
            "Support tickets", 0, max_tickets, (0, max_tickets),
            help="Filter to customers whose ticket count falls in this range.",
        )

        min_value = st.number_input(
            "Minimum lifetime value ($)",
            min_value=0,
            max_value=int(customers["lifetime_value"].max()),
            value=0,
            step=500,
        )

    filtered = customers[
        customers["customer_type"].isin(chosen_segments)
        & customers["region"].isin(chosen_regions)
        & customers["support_tickets"].between(*ticket_range)
        & (customers["lifetime_value"] >= min_value)
    ]
    return filtered


def render():
    """Draw the whole page."""
    components.page_header(
        "Interactive Explorer",
        "The same findings, but you drive them: hover for exact values, "
        "switch metric without a reload, zoom into any region.",
        question="What sits behind each point, and what happens if I look closer?",
    )

    try:
        trend = data_loader.load_revenue_trend()
        product_metrics = data_loader.load_product_metrics()
        customers = data_loader.load_customer_segment_data()
    except data_loader.MissingArtifactError as error:
        components.missing_artifact_warning(error)
        return

    filtered = sidebar_filters(customers)

    st.subheader("Revenue over time")
    components.plotly_block(
        interactive.build_revenue_trend(trend),
        insight=(
            f"{len(trend)} days from {trend.index.min():%d %b} to "
            f"{trend.index.max():%d %b %Y}. Hover any day to read its order "
            "count and average order value, neither of which is on an axis."
        ),
        filename="revenue_trend",
        interactions=(
            "- **Hover** any point for revenue, orders, average order value, "
            "and the 7-day average, all at that date\n"
            "- **7D / 14D / 1M / All** buttons jump to a fixed window\n"
            "- **Range slider** under the plot drags to any custom window\n"
            "- **Drag** on the plot to zoom, **double-click** to reset\n"
            "- **Click a legend entry** to hide that series"
        ),
        key="plot_trend",
    )

    st.divider()
    st.subheader("Product performance")

    left, right = st.columns(2)
    with left:
        st.markdown("**Revenue, with detail on hover**")
        st.plotly_chart(
            interactive.build_product_performance(product_metrics),
            width="stretch",
            theme=None,
            config=theme.plotly_config("product_performance"),
            key="plot_product",
        )
    with right:
        st.markdown("**One chart, three metrics**")
        st.plotly_chart(
            interactive.build_metric_selector(product_metrics),
            width="stretch",
            theme=None,
            config=theme.plotly_config("metric_selector"),
            key="plot_selector",
        )

    st.info(theme.md_safe(
        "Every tier holds the same six customers, so the dropdown shows a flat "
        "customer count while revenue and average value both rank "
        "Enterprise > Pro > Basic. The revenue gap is entirely price, not volume."),
        icon=":material/lightbulb:",
    )

    st.divider()
    st.subheader("Customer explorer")

    if filtered.empty:
        st.warning(
            "No customers match the current filters. Widen a filter in the sidebar.",
            icon=":material/filter_alt_off:",
        )
        return

    components.kpi_row(
        [
            {
                "label": "Customers shown",
                "value": f"{len(filtered):,}",
                "delta": f"of {len(customers):,}",
                "delta_color": "off",
            },
            {
                "label": "Median lifetime value",
                "value": theme.fmt_currency(filtered["lifetime_value"].median()),
            },
            {
                "label": "Mean support tickets",
                "value": f"{filtered['support_tickets'].mean():.1f}",
            },
            {
                "label": "Mean retention",
                "value": f"{filtered['retention_days'].mean():,.0f} days",
            },
        ]
    )

    figure, correlation = interactive.build_scatter_explorer(filtered)
    components.plotly_block(
        figure,
        insight=(
            f"Pearson r = {correlation['pearson']:.2f} across the "
            f"{len(filtered):,} customers currently shown. Zoom into a cluster "
            "to read individual accounts; the hover names the customer id, "
            "region, tier, and retention."
        ),
        filename="customer_explorer",
        interactions=(
            "- **Drag** to zoom into a region, **double-click** to reset\n"
            "- **Shift + drag**, or the pan tool, to move around\n"
            "- **Box select** and **lasso select** in the mode bar to draw a "
            "selection\n"
            "- **Click a legend entry** to hide a segment, **double-click** to "
            "show it alone\n"
            "- **Hover** any point for the customer id, region, tier, value, "
            "tickets, and retention"
        ),
        key="plot_scatter",
    )

    with st.expander(f"Underlying data ({len(filtered):,} rows)"):
        st.dataframe(
            filtered[
                [
                    "customer_id",
                    "customer_type",
                    "region",
                    "product_tier",
                    "lifetime_value",
                    "support_tickets",
                    "retention_days",
                ]
            ].sort_values("lifetime_value", ascending=False),
            width="stretch",
            hide_index=True,
            column_config={
                "lifetime_value": st.column_config.NumberColumn(
                    "Lifetime value", format="$%.2f"
                ),
                "retention_days": st.column_config.NumberColumn(
                    "Retention (days)", format="%d"
                ),
            },
        )
        st.download_button(
            "Download filtered data (CSV)",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="filtered_customers.csv",
            mime="text/csv",
            key="download_filtered",
        )

    st.divider()
    with st.expander("Choosing a date range control: buttons or slider?"):
        st.markdown(
            """
Both sit on the revenue chart above, because they answer different needs.

**Range selector buttons** suit known, named periods. One click gives "the last
month" with no dragging and no chance of landing on a slightly wrong window.
Use buttons when the periods people ask for are predictable: last week, last
quarter, year to date.

**The range slider** suits arbitrary windows. "The middle three weeks of
February, because that is when the campaign ran" cannot be expressed as a
button. The slider gives it directly, and keeps the whole series visible for
context while you drag.

Offering both is the normal choice for a business time series: the buttons
carry the common cases, the slider carries everything else.

```python
figure.update_xaxes(
    rangeselector={"buttons": [
        {"count": 7,  "label": "7D",  "step": "day",   "stepmode": "backward"},
        {"count": 1,  "label": "1M",  "step": "month", "stepmode": "backward"},
        {"count": 1,  "label": "YTD", "step": "year",  "stepmode": "todate"},
        {"step": "all", "label": "All"},
    ]},
    rangeslider={"visible": True, "thickness": 0.08},
    type="date",
)
```

This project's series spans 59 days, so the shipped buttons step in days and
weeks. A 3M, 6M, or YTD button would select a range the data does not contain.
            """
        )
        if config.INTERACTIVE_README.exists():
            st.caption(
                f"Full interaction reference: "
                f"`output/interactive/{config.INTERACTIVE_README.name}`"
            )


render()
