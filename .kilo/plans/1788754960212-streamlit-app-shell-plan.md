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

- [ ] Sidebar radio switches between all three sections
- [ ] Only the selected section is visible per selection
- [ ] `st.columns` used for KPI cards and side-by-side content in every section
- [ ] `st.expander` present in every section for optional/detail content
- [ ] `st.header`, `st.subheader`, `st.divider` used consistently
- [ ] KPIs are the first content shown in Overview (no scroll needed)
- [ ] App starts cleanly from `pip install -r requirements.txt && streamlit run app.py`

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

Replace the Data Explorer `elif page == "Data Explorer":` block (lines 98–118 of `app.py`) with the upload + preview flow. The section's `st.title("Data Explorer")` stays; everything below it becomes the upload system.

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

- [ ] CSV file loads and renders preview + statistics + bar chart
- [ ] JSON file loads and renders preview + statistics + bar chart
- [ ] No file uploaded → `st.info` message, no errors
- [ ] Malformed file → `st.error` message, no traceback
- [ ] Empty file → `st.warning` message, no traceback
- [ ] Column summary shows Column, Type, Non-Null, Null Count, Null %
- [ ] Descriptive statistics show for numeric columns only
- [ ] Quick Exploration bar chart updates when dropdown changes
- [ ] `pip install -r requirements.txt && streamlit run app.py` runs without errors

## Ordered implementation steps

1. Edit `app.py` Data Explorer block: add `st.file_uploader`, try/except loader, success message.
2. Add Task 2 preview (metrics, first 10 rows, column summary).
3. Add Task 3 descriptive statistics.
4. Add Task 5 quick exploration bar chart.
5. Verify with clean venv: install deps + run app.
6. Test upload of a sample CSV, sample JSON, malformed file, and empty file.
