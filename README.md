# Open Pulse

Analyze first-time contributor journeys and identify onboarding factors that discourage contributors from making future contributions, enabling open-source maintainers to improve contributor retention.

## Stack
- Python
- pandas / numpy (analytics)
- SQL (SQLite via SQLAlchemy)
- Streamlit (dashboard)

## Structure
```
.
├── config/              # Configuration files
├── data/                # raw / processed / sqlite data
├── sql/                 # SQL schema + analytics queries
├── src/
│   ├── database/        # DB connection, schema init, queries
│   ├── data_pipeline/   # Load raw GitHub data -> transform -> DB
│   ├── analytics/       # First-time contributor + retention metrics
│   └── dashboard/       # Streamlit app
├── scripts/             # CLI entrypoints (init_db, run_pipeline, run_dashboard)
├── notebooks/           # Exploratory analysis
└── tests/               # Unit tests
```

## Setup
```
pip install -r requirements.txt
python scripts/init_db.py
python scripts/run_pipeline.py
streamlit run src/dashboard/app.py
```
