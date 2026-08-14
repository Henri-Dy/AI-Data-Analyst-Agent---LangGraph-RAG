"""Schema Agent: inspects the live PostgreSQL schema so downstream agents
(SQL Generator in particular) always work from ground truth, not a stale
hardcoded description."""
from dataclasses import dataclass, field

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

# Internal/system tables that are not part of the business schema exposed
# to the SQL Generator.
EXCLUDED_TABLES = {"alembic_version", "rag_documents"}

SAMPLE_VALUES_LIMIT = 5


@dataclass
class ColumnInfo:
    name: str
    type: str
    nullable: bool
    sample_values: list[str] = field(default_factory=list)


@dataclass
class TableInfo:
    name: str
    columns: list[ColumnInfo]
    primary_key: list[str]
    foreign_keys: list[dict]
    row_count: int


def inspect_schema(engine: Engine) -> dict[str, TableInfo]:
    """Returns a description of every business table: columns, types,
    nullability, foreign keys, row counts, and a few sample values per
    column to help the SQL Generator understand the data, not just the DDL.
    """
    inspector = inspect(engine)
    schema: dict[str, TableInfo] = {}

    with engine.connect() as conn:
        for table_name in inspector.get_table_names():
            if table_name in EXCLUDED_TABLES:
                continue

            pk = inspector.get_pk_constraint(table_name).get("constrained_columns", [])
            fks = [
                {
                    "columns": fk["constrained_columns"],
                    "references_table": fk["referred_table"],
                    "references_columns": fk["referred_columns"],
                }
                for fk in inspector.get_foreign_keys(table_name)
            ]
            row_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()

            columns = []
            for col in inspector.get_columns(table_name):
                sample_values = _get_sample_values(conn, table_name, col["name"])
                columns.append(
                    ColumnInfo(
                        name=col["name"],
                        type=str(col["type"]),
                        nullable=col["nullable"],
                        sample_values=sample_values,
                    )
                )

            schema[table_name] = TableInfo(
                name=table_name,
                columns=columns,
                primary_key=pk,
                foreign_keys=fks,
                row_count=row_count,
            )

    return schema


def _get_sample_values(conn, table_name: str, column_name: str) -> list[str]:
    query = text(
        f'SELECT DISTINCT "{column_name}" FROM "{table_name}" '
        f'WHERE "{column_name}" IS NOT NULL LIMIT :limit'
    )
    rows = conn.execute(query, {"limit": SAMPLE_VALUES_LIMIT}).scalars().all()
    return [str(v) for v in rows]


def schema_to_prompt_context(schema: dict[str, TableInfo]) -> str:
    """Renders the schema as compact text suitable for an LLM prompt."""
    lines = []
    for table in schema.values():
        lines.append(f"Table {table.name} ({table.row_count:,} rows):")
        for col in table.columns:
            pk_marker = " [PK]" if col.name in table.primary_key else ""
            samples = f" e.g. {col.sample_values}" if col.sample_values else ""
            lines.append(f"  - {col.name}: {col.type}{pk_marker}{samples}")
        for fk in table.foreign_keys:
            lines.append(
                f"  FK: {', '.join(fk['columns'])} -> "
                f"{fk['references_table']}.{', '.join(fk['references_columns'])}"
            )
    return "\n".join(lines)
