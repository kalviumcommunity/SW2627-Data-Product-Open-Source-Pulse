"""SQLAlchemy engine/session setup for the analytics database."""

def get_engine(db_url=None):
    """Return a SQLAlchemy engine (default from config)."""
    ...

def get_session(engine=None):
    """Return a session bound to the engine."""
    ...

def init_db(engine=None):
    """Create all tables from sql/schema.sql."""
    ...
