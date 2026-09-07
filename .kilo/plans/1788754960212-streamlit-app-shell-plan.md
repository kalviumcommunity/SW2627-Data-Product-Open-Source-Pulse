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

`/requirements.txt` (already created at project root):
```
streamlit==1.38.0
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

- [x] Sidebar radio switches between all three sections
- [x] Only the selected section is visible per selection
- [x] `st.columns` used for KPI cards and side-by-side content in every section
- [x] `st.expander` present in every section for optional/detail content
- [x] `st.header`, `st.subheader`, `st.divider` used consistently
- [x] KPIs are the first content shown in Overview (no scroll needed)
- [x] App starts cleanly from `pip install -r requirements.txt && streamlit run app.py`

### Part A validation results

Verified via Streamlit AppTest API (`st.AppTest.from_file`) + Playwright browser automation:
- Overview page renders all 5 KPI metric cards, sidebar navigation works
- Data Explorer section active; file uploader + info message visible
- CSV upload: success message with row/column count, preview, stats, chart
- JSON upload: success message with row/column count, preview, stats, chart
- Malformed CSV → error message, no traceback
- Empty CSV → warning message, no traceback

---

## Part B — Dataset Upload & Dynamic Preview System

Extend the existing `app.py` Data Explorer section to accept user-uploaded CSV/JSON files and render an automatic preview. This replaces the placeholder filters/tables that currently live in that section.

### Design decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Upload placement | In the **Data Explorer** section (main area, top) | Natural home — data upload precedes exploration; replaces existing placeholder content |
| Sidebar | Left untouched — `st.file_uploader` renders in main area | Keeps navigation stable; uploader is section-scoped |
| DataFrame scope | Local `df` inside `if uploaded_file is not None:` block | Matches the lesson pattern; Streamlit re-reads on every rerun |
| Caching | **Not added** (no `@st.cache_data`) | Lesson does not include it; datasets are small. Note as future enhancement for large files |
| `use_container_width` | Used as-is from lesson (Streamlit 1.38.0 supports it) | Matches lesson validation criteria exactly |
| `df.describe()` | Called with no args (numeric-only default in pandas 2.x) | Lesson validation says "Non-numeric columns gracefully excluded" |

### Integration target

Replace the Data Explorer `elif page == "Data Explorer":` block (lines 98–118 of original `app.py`) with the upload + preview flow. The section's `st.title("Data Explorer")` stays; everything below it becomes the upload system.

### Task 1 — File upload (CSV + JSON)

- `st.file_uploader("Upload your dataset", type=["csv", "json"])` into `uploaded_file`.
- `if uploaded_file is None:` → `st.info("Upload a CSV or JSON file to begin.")` and nothing else renders.
- Inside `if uploaded_file is not None:`, wrapped in `try/except`:
  - `.csv` → `pd.read_csv(uploaded_file)`
  - `.json` → `pd.read_json(uploaded_file)`
  - else → `st.error("Unsupported file type.")` + `st.stop()`
  - if `len(df) == 0` → `st.warning("Uploaded file is empty.")` + `st.stop()`
  - except → `st.error("Could not read this file...")` + `st.stop()`
- After successful parse: `st.success("Loaded: <name> (<rows> rows, <cols> columns)")`

### Task 2 — Automatic preview

Below the success message, still inside `if uploaded_file is not None:`:
- `st.header("Dataset Preview")`
- 3 `st.columns(3)` with `st.metric`: Rows, Columns, Null %
- `st.divider()`
- `st.subheader("First 10 Rows")` → `st.dataframe(df.head(10), use_container_width=True)`
- `st.subheader("Column Summary")` → build a `pd.DataFrame` with columns: Column, Type, Non-Null, Null Count, Null % → `st.dataframe(summary, use_container_width=True)`

### Task 3 — Descriptive statistics

- `st.subheader("Descriptive Statistics")` → `st.dataframe(df.describe(), use_container_width=True)`
- Default `describe()` covers numeric columns only; non-numeric columns are excluded automatically (pandas 2.x default).

### Task 4 — Error handling

- All three failure modes (unsupported type, empty file, parse exception) are caught before any preview renders.
- Each failure uses `st.error`/`st.warning` + `st.stop()` — no Python traceback reaches the user.
- The `else` branch for unsupported file type is technically unreachable (`type=` already filters to csv/json), but kept per the lesson for defense in depth.

### Task 5 — Downstream usability (Quick Exploration)

- After the statistics block, add `st.subheader("Quick Exploration")`.
- `numeric_cols = df.select_dtypes(include="number").columns.tolist()` — if empty, show `st.info("No numeric columns to chart.")`.
- `selected_col = st.selectbox("Select a column to visualise", numeric_cols)`.
- `st.bar_chart(df[selected_col].value_counts().head(20))` — renders a distribution bar chart of the top 20 value counts for the selected numeric column.

### Revised Data Explorer block structure

```
st.title("Data Explorer")          ← kept from current app.py

uploaded_file = st.file_uploader(...)
if uploaded_file is None:
    st.info("Upload a CSV or JSON file to begin.")
else:
    try:
        df = pd.read_csv / pd.read_json  (with type check + empty check + except)
    except / st.stop paths ...

    st.success("Loaded: ...")

    # Task 2: preview
    st.header("Dataset Preview")
    col1, col2, col3 = st.columns(3)  → Rows / Columns / Null %
    st.divider()
    st.subheader("First 10 Rows") → st.dataframe(df.head(10))
    st.subheader("Column Summary") → st.dataframe(summary)

    # Task 3: statistics
    st.subheader("Descriptive Statistics") → st.dataframe(df.describe())

    # Task 5: downstream exploration
    st.subheader("Quick Exploration")
    numeric_cols = ...
    if numeric_cols:
        selected_col = st.selectbox(...)
        st.bar_chart(df[selected_col].value_counts().head(20))
    else:
        st.info("No numeric columns to chart.")
```

### Validation checklist

- [x] CSV file loads and renders preview + statistics + bar chart
- [x] JSON file loads and renders preview + statistics + bar chart
- [x] No file uploaded → `st.info` message, no errors
- [x] Malformed file → `st.error` message, no traceback
- [x] Empty file → `st.warning` message, no traceback
- [x] Column summary shows Column, Type, Non-Null, Null Count, Null %
- [x] Descriptive statistics show for numeric columns only
- [x] Quick Exploration bar chart updates when dropdown changes
- [x] `pip install -r requirements.txt && streamlit run app.py` runs without errors

### Part B validation results

Verified via Playwright browser automation (43+ assertions):
- CSV upload: success "10 rows, 5 columns", all preview sections, all stats, chart rendered (33 SVGs)
- JSON upload: success "10 rows, 5 columns", date picker appeared (auto-parsed date column)
- Malformed CSV: error "Could not read this file", no traceback
- Empty CSV: warning "Uploaded file is empty", no traceback
- No file: info message "Upload a CSV or JSON file to begin."

---

## Part C — Streamlit Filters & Interactive Widgets

Add adaptive sidebar filters to the Data Explorer section so users can filter the uploaded dataset by date, category, and numeric threshold, with all downstream content reacting instantly.

### Design decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Filter placement | `st.sidebar` below the navigation radio | Keeps all controls in one panel; only appears when data is loaded |
| Widget adaptability | Scan DataFrame schema to decide which widgets to render | Works with any uploaded data — date_input for datetime cols, multiselect for categorical, slider for numeric |
| ID column exclusion | Skip columns ending in `_id` or named exactly `id` for slider | Prevents a meaningless row-index slider |
| Date auto-detection | Try `pd.to_datetime` on object columns; treat as date if >50% parse | Catches string-encoded dates in CSV uploads |
| Filter application | Build a boolean `mask` and apply with `df[mask]` | Clean, extensible — easy to add more filters |
| Reset strategy | Store widget keys in a list; delete only those keys from `st.session_state` on reset | Preserves the file_uploader state; user doesn't need to re-upload |
| `st.rerun()` | Used after deleting session state keys | Forces fresh widget creation with defaults |
| Preview source | Uses `filtered_df` (not raw `df`) | All preview/stats/charts reflect the current filter state |

### Task 1 — Three widget types (adaptive)

After loading `df`, scan column types, then render sidebar filters:
- **Date picker** (`st.sidebar.date_input`): appears if any column is datetime (native or auto-parsed from string)
- **Multi-select** (`st.sidebar.multiselect`): first object/categorical column, all values selected by default
- **Slider** (`st.sidebar.slider`): first numeric non-ID column, full range by default
- **Radio** (`st.sidebar.radio`): "Chart type" — Bar / Line (always present)

All widgets have explicit `key=` attributes tracked in `filter_keys` list.

### Task 2 — Wire filters to DataFrame

Build a boolean mask from all active widgets:
```python
mask = pd.Series([True] * len(df), index=df.index)
if date_range: mask &= (df[date_col] >= start) & (df[date_col] <= end)
if selected_values: mask &= df[cat_col].isin(selected_values)
if val_range: mask &= (df[slider_col] >= val_range[0]) & (df[slider_col] <= val_range[1])
filtered_df = df[mask]
```
All downstream content (preview, stats, exploration, raw data) reads from `filtered_df`.

### Task 3 — Meaningful defaults

Every widget defaults to show all data:
- Date range: full data span (min → max)
- Multi-select: all values selected
- Slider: full range (min → max)
- Radio: "Bar" (first option)

Result on first load: "Showing 10 of 10 records" — no empty state.

### Task 4 — Empty filter handling

```python
if len(filtered_df) == 0:
    st.warning("No data matches the current filters. Try broadening your selection.")
    st.stop()
```
Placed after filter application and before any preview renders. No traceback, no crash.

### Task 5 — Reset mechanism

```python
if st.sidebar.button("Reset Filters"):
    for key in filter_keys:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
```
Deletes only filter widget keys from session state, preserving the uploaded file. `st.rerun()` re-creates widgets with fresh defaults.

### Validation checklist

- [x] At least 3 widget types visible (date_input, multiselect, slider, radio)
- [x] Changing any widget updates the displayed data (row count changes)
- [x] All widgets have meaningful defaults (full dataset visible on first load)
- [x] Empty filter combination shows warning, no crash, no traceback
- [x] Reset button restores all widgets to defaults (full dataset shown again)
- [x] `pip install -r requirements.txt && streamlit run app.py` runs without errors

### Part C validation results

Verified via Playwright browser automation (43 assertions):
- CSV upload (with date column): 4 widgets visible (date picker, multiselect, slider, radio) + reset button
- Default view shows "10 of 10 records"
- Clear multiselect → "No data matches" warning appears
- Reset Filters → restores "10 of 10 records"
- JSON upload: same 4 widgets, date picker auto-appears (date column parsed)
- Malformed CSV → error message, no traceback
- Empty CSV → warning message, no traceback
- All preview sections, statistics, charts, and raw data expander render correctly with filtered data
