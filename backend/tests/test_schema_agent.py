from app.agents.schema_agent import inspect_schema, schema_to_prompt_context
from app.database.session import engine

EXPECTED_TABLES = {"regions", "employees", "customers", "products", "orders", "order_items"}


def test_inspect_schema_covers_all_business_tables():
    schema = inspect_schema(engine)
    assert EXPECTED_TABLES.issubset(schema.keys())
    # Internal tables must never leak into the SQL Generator's context.
    assert "alembic_version" not in schema
    assert "rag_documents" not in schema


def test_inspect_schema_captures_foreign_keys_and_row_counts():
    schema = inspect_schema(engine)
    orders = schema["orders"]
    assert orders.row_count > 0
    fk_targets = {fk["references_table"] for fk in orders.foreign_keys}
    assert {"customers", "employees", "regions"}.issubset(fk_targets)


def test_schema_to_prompt_context_is_renderable_text():
    schema = inspect_schema(engine)
    context = schema_to_prompt_context(schema)
    assert "Table orders" in context
    assert "FK:" in context
