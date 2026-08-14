from app.agents.schema_agent import inspect_schema
from app.database.session import engine
from app.graph.nodes import make_schema_agent_node
from app.tools.sql_validator import validate_sql


def _schema_info():
    # Re-use the exact serialization the graph produces, via the real DB.
    state = make_schema_agent_node(engine)({})
    return state["schema_info"]


def test_valid_select_passes():
    schema = _schema_info()
    result = validate_sql(
        "SELECT region_id, COUNT(*) FROM orders GROUP BY region_id", schema
    )
    assert result.valid
    assert result.errors == []


def test_rejects_forbidden_keywords():
    schema = _schema_info()
    for sql in [
        "DROP TABLE orders",
        "DELETE FROM orders",
        "UPDATE orders SET status = 'completed'",
        "INSERT INTO orders (id) VALUES (1)",
        "ALTER TABLE orders ADD COLUMN x INT",
        "TRUNCATE orders",
        "CREATE TABLE evil (id INT)",
    ]:
        result = validate_sql(sql, schema)
        assert not result.valid, f"expected {sql!r} to be rejected"


def test_rejects_stacked_statements_injection():
    schema = _schema_info()
    result = validate_sql("SELECT * FROM orders; DELETE FROM orders", schema)
    assert not result.valid
    assert any("forbidden" in e.lower() for e in result.errors)
    assert any("one sql statement" in e.lower() for e in result.errors)


def test_rejects_unknown_table():
    schema = _schema_info()
    result = validate_sql("SELECT * FROM made_up_table", schema)
    assert not result.valid
    assert any("made_up_table" in e for e in result.errors)


def test_rejects_unknown_column():
    schema = _schema_info()
    result = validate_sql("SELECT nonexistent_col FROM orders", schema)
    assert not result.valid
    assert any("nonexistent_col" in e for e in result.errors)


def test_rejects_empty_sql():
    result = validate_sql("", {})
    assert not result.valid


def test_rejects_syntax_error():
    schema = _schema_info()
    result = validate_sql("SELEC * FROM orders", schema)
    assert not result.valid
