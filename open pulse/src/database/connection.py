"""SQLAlchemy engine/session setup for the analytics database."""

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_engine(db_url=None):
    url = db_url or f"sqlite:///{PROJECT_ROOT / 'analytics.db'}"
    return create_engine(url, future=True)


def get_session(engine=None):
    return Session(engine or get_engine())


def init_db(engine=None):
    active_engine = engine or get_engine()
    schema = (PROJECT_ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    statements = [statement.strip() for statement in schema.split(";") if statement.strip()]
    with active_engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
    return active_engine
