# database/sql_client.py

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def get_sql_engine(uri: str) -> Engine:
    """Create a SQLAlchemy engine from a connection URI."""
    return create_engine(uri)


def execute_sql(engine: Engine, sql: str) -> list[dict]:
    """Execute a SQL SELECT and return rows as a list of dicts."""
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        cols = list(result.keys())
        return [dict(zip(cols, row)) for row in result.fetchall()]
