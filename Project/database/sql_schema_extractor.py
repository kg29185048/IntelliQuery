# database/sql_schema_extractor.py

from sqlalchemy import inspect


def extract_sql_schema(engine) -> dict:
    """
    Return a dict of {table_name: [column_name, ...]} for all tables
    in the connected SQL database.  Same shape as extract_full_schema()
    so the frontend schema panel works without changes.
    """
    inspector = inspect(engine)
    schema = {}
    for table_name in inspector.get_table_names():
        cols = [col["name"] for col in inspector.get_columns(table_name)]
        schema[table_name] = cols
    return schema
