"""SQL Validator: enforces read-only access and basic schema consistency.

Deterministic and LLM-free by design — validation must never depend on a
model's judgment about what counts as "safe SQL".
"""
import re
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

FORBIDDEN_KEYWORDS = ("DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE")
_FORBIDDEN_PATTERN = re.compile(r"\b(" + "|".join(FORBIDDEN_KEYWORDS) + r")\b", re.IGNORECASE)

DIALECT = "postgres"


@dataclass
class SQLValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


def validate_sql(sql: str, schema_info: dict) -> SQLValidationResult:
    """Validates `sql` against the forbidden-keyword list, single-SELECT-statement
    rule, and the known tables/columns in `schema_info` (as produced by the
    Schema Agent). Returns every problem found, not just the first.
    """
    errors: list[str] = []

    if not sql or not sql.strip():
        return SQLValidationResult(valid=False, errors=["SQL query is empty."])

    if _FORBIDDEN_PATTERN.search(sql):
        found = sorted(set(m.upper() for m in _FORBIDDEN_PATTERN.findall(sql)))
        errors.append(f"Query contains forbidden write/DDL keyword(s): {', '.join(found)}.")

    try:
        statements = [s for s in sqlglot.parse(sql, read=DIALECT) if s is not None]
    except sqlglot.errors.ParseError as e:
        return SQLValidationResult(valid=False, errors=errors + [f"SQL syntax error: {e}"])

    if len(statements) != 1:
        errors.append(f"Exactly one SQL statement is required; found {len(statements)}.")
    elif not isinstance(statements[0], (exp.Select, exp.Union)):
        errors.append("Only SELECT statements are allowed.")

    if statements:
        table_errors, column_errors = _check_schema_consistency(statements[0], schema_info)
        errors.extend(table_errors)
        errors.extend(column_errors)

    return SQLValidationResult(valid=len(errors) == 0, errors=errors)


def _check_schema_consistency(statement: exp.Expression, schema_info: dict) -> tuple[list[str], list[str]]:
    known_tables = {name.lower() for name in schema_info}
    known_columns = {
        col["name"].lower() for table in schema_info.values() for col in table["columns"]
    }

    table_errors: list[str] = []
    referenced_tables = {t.name.lower() for t in statement.find_all(exp.Table) if t.name}
    unknown_tables = referenced_tables - known_tables
    if unknown_tables:
        table_errors.append(f"Unknown table(s): {', '.join(sorted(unknown_tables))}.")

    column_errors: list[str] = []
    referenced_columns = {
        c.name.lower() for c in statement.find_all(exp.Column) if c.name and c.name != "*"
    }
    # Best-effort check: columns are validated against the union of all known
    # columns rather than resolved per-table (which would require full join
    # resolution), so this catches typos without false-positiving on
    # legitimate multi-table joins.
    unknown_columns = referenced_columns - known_columns
    if unknown_columns:
        column_errors.append(f"Unknown column(s): {', '.join(sorted(unknown_columns))}.")

    return table_errors, column_errors
