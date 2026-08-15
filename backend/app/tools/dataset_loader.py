"""Turns an uploaded CSV into a queryable table.

Deterministic and LLM-free, like sql_validator.py/sql_executor.py: table
creation and deletion are plain pandas/SQLAlchemy operations, gated by a
denylist so a user-uploaded dataset can never collide with or replace the
demo/business tables the rest of the app depends on.
"""
import re

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

RESERVED_TABLE_NAMES = {
    "regions",
    "employees",
    "customers",
    "products",
    "orders",
    "order_items",
    "rag_documents",
    "alembic_version",
    "uploaded_datasets",
}


class DatasetTableError(ValueError):
    """Raised when a table name is reserved, or already exists."""


def sanitize_table_name(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0].lower()
    name = re.sub(r"[^a-z0-9_]+", "_", stem).strip("_") or "dataset"
    if name[0].isdigit():
        name = f"t_{name}"
    return name[:63]


def create_table_from_csv(engine: Engine, df: pd.DataFrame, table_name: str) -> int:
    """Creates `table_name` from `df`'s inferred schema and returns the row
    count. Raises `DatasetTableError` if the name is reserved or already
    taken by an existing table."""
    if table_name in RESERVED_TABLE_NAMES:
        raise DatasetTableError(f"'{table_name}' is a reserved table name")
    if inspect(engine).has_table(table_name):
        raise DatasetTableError(f"A table named '{table_name}' already exists")

    df.to_sql(table_name, engine, if_exists="fail", index=False)
    return len(df)


def drop_uploaded_table(engine: Engine, table_name: str) -> None:
    """Drops a previously uploaded table. Refuses to drop a reserved table
    even if somehow asked to — defense in depth, same reasoning
    sql_executor.py applies to SQL execution."""
    if table_name in RESERVED_TABLE_NAMES:
        raise DatasetTableError(f"'{table_name}' is a reserved table name")

    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
