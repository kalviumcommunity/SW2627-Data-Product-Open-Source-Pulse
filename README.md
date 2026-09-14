# Open Pulse

Open Pulse is a Python and Streamlit analytics product for understanding customer activity, revenue, segmentation, and retention. It provides an interactive dashboard for uploaded CSV or JSON data and a separate analytics workspace for repeatable data preparation, SQL metrics, validation, and scheduled output refreshes.

The project is intended for analysts, product teams, and maintainers who need to explore customer behavior and review reproducible metrics without rebuilding the analysis manually.

## Dataset

The repository contains sample datasets under `open pulse/data/raw/` and generated analytics under `open pulse/output/`.

The main customer-level dataset, `open pulse/output/customer_segment_data.csv`, contains:

| Column | Type | Description | Example |
|---|---|---|---|
| `customer_id` | integer | Customer identifier | `1` |
| `customer_type` | string | Customer segment label | `Startup` |
| `region` | string | Customer region | `North America` |
| `product_tier` | string | Product tier used by the customer | `Basic` |
| `lifetime_value` | float | Customer lifetime value | `2880.39` |
| `churn` | float | Customer churn indicator or modeled churn value | `0.1484` |
| `support_tickets` | float | Number of support tickets | `2.0` |
| `retention_days` | integer | Observed retention duration | `278` |

Transaction-oriented source files use `customer_id`, `transaction_amount`, and `transaction_date`. Segment analysis files use `customer_type`, `product`, `revenue`, `support_tickets`, and `churn`. The pipeline normalizes compatible revenue fields to `amount` and compatible segment fields to `segment`.

## Getting Started

From a fresh clone, run these commands from the repository root:

```bash
git clone <repository-url>
cd SW2627-Data-Product-Open-Source-Pulse
python -m venv .venv
```

Activate the environment and install dependencies:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# macOS or Linux
source .venv/bin/activate
pip install -r requirements.txt
```

Start the dashboard:

```bash
streamlit run app.py
```

The root application requires Python 3.9 or newer. The analytics workspace has its own dependency file at `open pulse/requirements.txt` and should be run from that directory when using its scripts.

## Usage

### Dashboard

Open the Streamlit URL and use the sidebar to select:

- **Overview** for the KPI summary and segment view.
- **Trends** to upload a CSV or JSON file, detect date and numeric fields, filter by date/category/value, and view line or bar charts.
- **Data Explorer** to upload a CSV or JSON file and inspect the data interactively.

Uploaded files must be non-empty and use a supported `.csv` or `.json` extension. The Trends view detects date-like columns, categorical columns, and revenue-like numeric columns containing `revenue`, `value`, or `amount` in their names.

### Analytics workspace

Run these commands from `open pulse/` when working with the repeatable analytics workflow:

```bash
pip install -r requirements.txt
python pipeline.py --input data/raw/segment_data.csv --output output
python validate_data.py output/customer_segment_data.csv
```

The pipeline also accepts any compatible input and output locations:

```bash
python pipeline.py --input data/raw/sample.csv --output output
```

The validation command checks required columns, numeric dtypes, a minimum row count of 100, and fully null columns. A failed check exits with a non-zero status.

### SQL metrics

Shared SQL metrics are stored in `open pulse/queries/` and run against the SQLite analytics database:

```bash
cd "open pulse"
python scripts/init_db.py
python scripts/run_shared_queries.py
python -m pytest tests/test_shared_queries.py -v
```

The metric contracts cover monthly active users, revenue by segment, and the conversion funnel. Results are written to `open pulse/output/` as CSV files.

## Pipeline Architecture

```text
CSV or JSON upload / scheduled source
				  |
				  v
Ingestion         Load the file and report input row count
				  |
				  v
Cleaning          Resolve compatible column names, remove missing IDs,
				  coerce numeric amounts, remove non-positive amounts
				  |
				  v
Aggregation       Group by segment and calculate revenue and order count
				  |
				  v
Output            Write cleaned.csv and aggregated.csv to output/
				  |
				  v
Validation        Check schema, dtypes, row count, and null-column quality
				  |
				  v
Dashboard         Load supported uploads, apply filters, and render charts
```

The scheduled workflow in `open pulse/.github/workflows/pipeline.yml` runs the pipeline every Monday at 06:00 UTC and supports manual dispatch. The validation workflow in `open pulse/.github/workflows/validate.yml` runs on pushes to `main` or `develop` and on pull requests targeting `main`.

## Derived Features and Metrics

| Name | Type | Description | Example |
|---|---|---|---|
| `amount` | float | Canonical numeric revenue field created from `amount`, `transaction_amount`, or `revenue` | `150.50` |
| `segment` | string | Canonical grouping field created from `segment` or `customer_type`; defaults to `All` when absent | `SMB` |
| `revenue` | float | Sum of `amount` for each segment in the aggregate output | `1250.00` |
| `orders` | integer | Number of source records for each segment | `18` |
| Monthly active users | integer | Distinct customers with activity in each month | `240` |
| Average order value | float | Revenue divided by order count for a segment-month | `45.20` |
| Revenue per customer | float | Revenue divided by distinct customers in the reporting period | `120.40` |
| Conversion rate | float | Converted funnel stage divided by the signup population | `0.42` |

The authoritative SQL metric names and result columns are documented in `open pulse/docs/SHARED_METRICS.md`. The broader source-field definitions are in `open pulse/docs/DATA_DICTIONARY.md`.

## Project Structure

```text
.
├── app.py                         Streamlit dashboard entrypoint
├── requirements.txt               Root dashboard dependencies
├── open pulse/
│   ├── pipeline.py                Ingest, clean, aggregate, and output runner
│   ├── validate_data.py            Schema and data-quality validation
│   ├── config/                     Runtime configuration
│   ├── data/raw/                   Source fixtures and sample inputs
│   ├── output/                     Generated CSV and analysis artifacts
│   ├── queries/                    Shared SQL metric definitions
│   ├── scripts/                    Analysis and database entrypoints
│   ├── src/                        Pipeline, database, analytics, and dashboard modules
│   ├── tests/                      Automated tests
│   └── .github/workflows/          Scheduled pipeline and validation workflows
```

## Known Limitations

- The dashboard Overview page currently displays fixed sample KPI values and placeholder chart text; uploaded data drives the Trends and Data Explorer pages.
- The dashboard accepts CSV and JSON uploads but does not persist uploads between sessions.
- The pipeline supports compatible revenue and segment aliases, but it still requires a customer identifier and a positive numeric revenue-like field.
- The current transaction sample has no transaction identifier, so the pipeline uses `customer_id` as the fallback record-count field.
- The repository includes generated sample outputs; production refreshes require a real source-data ingestion process and an agreed retention policy.
- The scheduled pipeline refreshes weekly and uses UTC. It is not a real-time processing system.
- SQLite is used for local analytics. A production deployment would need a managed database, credential management, and concurrency controls.
- Churn values and segment labels depend on the source dataset. They are not automatically validated as a universal business definition across every input.
- Email delivery and external alerting are not implemented in the root dashboard.

## Development Checks

From `open pulse/`:

```bash
python -m pytest -q
python -m py_compile pipeline.py validate_data.py
git diff --check
```
