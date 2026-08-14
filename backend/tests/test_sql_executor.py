from app.database.session import engine
from app.tools.sql_executor import execute_sql


def test_executes_valid_select():
    result = execute_sql(
        engine, "SELECT id FROM regions ORDER BY id", max_rows=100, timeout_seconds=5
    )
    assert result.success
    assert result.row_count == 6
    assert not result.truncated
    assert result.columns == ["id"]


def test_caps_row_count_and_flags_truncation():
    result = execute_sql(engine, "SELECT id FROM orders", max_rows=10, timeout_seconds=5)
    assert result.success
    assert result.row_count == 10
    assert result.truncated


def test_read_only_transaction_blocks_side_effects():
    result = execute_sql(
        engine, "SELECT setval('regions_id_seq', 999)", max_rows=5, timeout_seconds=5
    )
    assert not result.success
    assert "read-only" in result.error.lower()


def test_statement_timeout_is_enforced():
    result = execute_sql(engine, "SELECT pg_sleep(2)", max_rows=5, timeout_seconds=1)
    assert not result.success
    assert "timeout" in result.error.lower()
