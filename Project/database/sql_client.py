# database/sql_client.py

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from functools import lru_cache


@lru_cache(maxsize=100)
def get_sql_engine(uri: str) -> Engine:
    """Create and cache a SQLAlchemy engine from a connection URI."""
    return create_engine(
        uri,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )


def execute_sql(engine: Engine, sql: str) -> list[dict]:
    """Execute a SQL SELECT and return rows as a list of dicts."""
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        cols = list(result.keys())
        return [dict(zip(cols, row)) for row in result.fetchall()]
