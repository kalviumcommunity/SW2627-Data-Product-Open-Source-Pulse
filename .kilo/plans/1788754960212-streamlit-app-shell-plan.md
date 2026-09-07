# Streamlit App Shell Plan

## Context

The lesson describes building a standalone Streamlit app shell with sidebar navigation, three content sections, columns, expanders, and visual hierarchy. The existing `open pulse/` project is a more advanced multi-page app (`st.navigation()` + `st.Page`); this plan creates the lesson's standalone `app.py` at the project root, runnable via `pip install -r requirements.txt && streamlit run app.py`.

## File locations

| File | Path | Purpose |
|------|------|---------|
| App | `/app.py` | Single-file Streamlit app with sidebar radio navigation |
| Dependencies | `/requirements.txt` | Pinned dependencies |

## Task 1 — Sidebar navigation

- `st.set_page_config(page_title="Analytics Dashboard", layout="wide")` at top.
- `st.sidebar.title("Navigation")` then `st.sidebar.radio("Go to", ["Overview", "Trends", "Data Explorer"])` into `page`.
- `if/elif` blocks render each section in the main area; only the selected section is visible per rerun.

## Task 2 — Three sections with columns + expanders

### Overview
- `st.title("Business Overview")`
- 5 `st.columns(5)` holding `st.metric` cards: Revenue, Users, AOV, Churn, NPS.
- `st.expander("About These Metrics")` with a methodology write-up.

### Trends
- `st.title("Trend Analysis")`
- 2 `st.columns(2)` with placeholder chart text in each.
- `st.expander("Chart controls")` for optional chart-type selector.

### Data Explorer
- `st.title("Data Explorer")`
- 2 `st.columns(2)` for filter group (segment select, date range).
- `st.expander("Raw data")` wrapping a `st.dataframe` placeholder + `st.download_button`.

## Task 3 — Visual hierarchy

Across all three sections:
- `st.title` — once per section (acts as page name).
- `st.header` — major subsection within each section.
- `st.subheader` — sub-subsection within a major subsection.
- `st.divider()` — between major sections.

## Task 4 — Clean-environment dependencies

`/requirements.txt`:
```
streamlit==2.1.0
pandas==2.1.4
```

Validation: `pip install -r requirements.txt && streamlit run app.py` with no errors.

## Task 5 — Content above the fold

- Overview section leads with the 5 KPI columns immediately after `st.title`.
- No blank space, instructions, or empty placeholders before the KPIs.
- First impression = the metrics, no scroll required.

## Implementation steps (ordered)

1. Create `app.py` with `set_page_config`, sidebar radio, and three `if/elif` sections.
2. Fill each section: columns for side-by-side content, expanders for optional detail.
3. Apply consistent headers/subheaders/dividers per hierarchy pattern.
4. Create `requirements.txt` with pinned `streamlit` and `pandas`.
5. Run `pip install -r requirements.txt && streamlit run app.py` and verify no errors.
6. Verify sidebar radio switches sections; KPIs visible without scrolling.

## Validation checklist

- [ ] Sidebar radio switches between all three sections
- [ ] Only the selected section is visible per selection
- [ ] `st.columns` used for KPI cards and side-by-side content in every section
- [ ] `st.expander` present in every section for optional/detail content
- [ ] `st.header`, `st.subheader`, `st.divider` used consistently
- [ ] KPIs are the first content shown in Overview (no scroll needed)
- [ ] App starts cleanly from `pip install -r requirements.txt && streamlit run app.py`
