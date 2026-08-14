from app.agents.sql_fixer import fix_sql
from app.agents.sql_generator import SQLGeneration, generate_sql


class FakeSQLModel:
    def __init__(self, result: SQLGeneration):
        self.result = result
        self.last_input = None

    def invoke(self, prompt_input: dict) -> SQLGeneration:
        self.last_input = prompt_input
        return self.result


def test_generate_sql_passes_context_through():
    expected = SQLGeneration(sql="SELECT 1", reasoning="trivial")
    fake = FakeSQLModel(expected)

    result = generate_sql(
        question="What is total revenue?",
        schema="Table orders...",
        analysis='{"metric": "revenue"}',
        rag_context="",
        generator=fake,
    )

    assert result == expected
    assert fake.last_input == {
        "question": "What is total revenue?",
        "schema": "Table orders...",
        "analysis": '{"metric": "revenue"}',
        "rag_context": "",
    }


def test_fix_sql_passes_errors_through():
    expected = SQLGeneration(sql="SELECT id FROM orders", reasoning="fixed")
    fake = FakeSQLModel(expected)

    result = fix_sql(
        question="top orders?",
        schema="Table orders...",
        sql="SELECT bad_col FROM orders",
        errors="Unknown column(s): bad_col.",
        fixer=fake,
    )

    assert result == expected
    assert fake.last_input["errors"] == "Unknown column(s): bad_col."
    assert fake.last_input["sql"] == "SELECT bad_col FROM orders"
