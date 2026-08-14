"""Exercises the SQL retry loop (Generator -> Validator -> Fixer -> Validator
-> Executor / Give Up) inside the compiled graph, using fake LLMs so no real
API key is required. The real Postgres instance is used for validation
(schema lookups) and execution.
"""
from langchain_community.embeddings import DeterministicFakeEmbedding

from app.agents.query_analyzer import QueryAnalysis
from app.agents.sql_generator import SQLGeneration
from app.database.models.rag_documents import EMBEDDING_DIM
from app.database.session import SessionLocal, engine
from app.graph.graph import build_graph

SQL_ANALYSIS = QueryAnalysis(
    metric="revenue", analysis_type="ranking",
    requires_sql=True, requires_statistics=False, requires_rag=False,
)


class FakeAnalyzer:
    def invoke(self, prompt_input: dict) -> QueryAnalysis:
        return SQL_ANALYSIS


class ScriptedGenerator:
    """Returns invalid SQL once, matching a real LLM's occasional first miss."""

    def invoke(self, prompt_input: dict) -> SQLGeneration:
        return SQLGeneration(sql="SELECT nonexistent_col FROM orders", reasoning="oops")


class SucceedingFixer:
    def invoke(self, prompt_input: dict) -> SQLGeneration:
        assert "nonexistent_col" in prompt_input["errors"]
        return SQLGeneration(sql="SELECT id FROM orders LIMIT 5", reasoning="fixed")


class AlwaysBadFixer:
    def invoke(self, prompt_input: dict) -> SQLGeneration:
        return SQLGeneration(sql="SELECT still_bad FROM orders", reasoning="still bad")


def _build(generator, fixer, max_sql_fix_attempts=3):
    return build_graph(
        analyzer=FakeAnalyzer(),
        engine=engine,
        session_factory=SessionLocal,
        embeddings=DeterministicFakeEmbedding(size=EMBEDDING_DIM),
        sql_generator=generator,
        sql_fixer=fixer,
        max_sql_fix_attempts=max_sql_fix_attempts,
    )


def test_sql_fixer_recovers_after_one_bad_generation():
    graph = _build(ScriptedGenerator(), SucceedingFixer())

    result = graph.invoke(
        {"question": "top products?"}, config={"configurable": {"thread_id": "sql-recover"}}
    )

    assert result["sql_valid"] is True
    assert result["sql_fix_attempts"] == 1
    assert result["sql_results"]["row_count"] == 5
    assert not result.get("errors")


def test_sql_retry_loop_gives_up_after_max_attempts():
    graph = _build(ScriptedGenerator(), AlwaysBadFixer(), max_sql_fix_attempts=3)

    result = graph.invoke(
        {"question": "top products?"}, config={"configurable": {"thread_id": "sql-giveup"}}
    )

    assert result["sql_valid"] is False
    assert result["sql_fix_attempts"] == 3
    assert result["sql_results"] is None
    assert any("after 3 fix attempt" in e for e in result["errors"])


def test_valid_sql_on_first_try_skips_the_fixer_entirely():
    class GoodGenerator:
        def invoke(self, prompt_input: dict) -> SQLGeneration:
            return SQLGeneration(sql="SELECT id FROM regions", reasoning="fine")

    class FixerThatShouldNeverRun:
        def invoke(self, prompt_input: dict) -> SQLGeneration:
            raise AssertionError("fixer should not run when SQL is valid on the first try")

    graph = _build(GoodGenerator(), FixerThatShouldNeverRun())

    result = graph.invoke(
        {"question": "list regions"}, config={"configurable": {"thread_id": "sql-first-try"}}
    )

    assert result["sql_valid"] is True
    assert result["sql_fix_attempts"] == 0
    assert result["sql_results"]["row_count"] == 6
