"""Exercises the Python Data Analyst wired into the compiled graph: it must
run after a successful SQL execution when `requires_statistics` is set, and
must not run otherwise (no data, or not needed). Uses fake LLMs so no real
API key is required; the real Postgres instance provides schema lookups
and SQL execution.
"""
from langchain_community.embeddings import DeterministicFakeEmbedding

from app.agents.query_analyzer import QueryAnalysis
from app.agents.sql_generator import SQLGeneration
from app.database.models.rag_documents import EMBEDDING_DIM
from app.database.session import SessionLocal, engine
from app.graph.graph import build_graph


class FakeAnalyzer:
    def __init__(self, analysis: QueryAnalysis):
        self.analysis = analysis

    def invoke(self, prompt_input: dict) -> QueryAnalysis:
        return self.analysis


class FakeSQLGenerator:
    def __init__(self, sql: str):
        self.sql = sql

    def invoke(self, prompt_input: dict) -> SQLGeneration:
        return SQLGeneration(sql=self.sql, reasoning="fake")


def _build(analysis: QueryAnalysis, sql: str):
    return build_graph(
        analyzer=FakeAnalyzer(analysis),
        engine=engine,
        session_factory=SessionLocal,
        embeddings=DeterministicFakeEmbedding(size=EMBEDDING_DIM),
        sql_generator=FakeSQLGenerator(sql),
        sql_fixer=FakeSQLGenerator(sql),
    )


def test_python_analyst_runs_after_sql_execution_when_statistics_required():
    analysis = QueryAnalysis(
        metric="revenue", analysis_type="descriptive",
        requires_sql=True, requires_statistics=True, requires_rag=False,
    )
    graph = _build(analysis, "SELECT unit_price AS revenue FROM order_items LIMIT 20")

    result = graph.invoke(
        {"question": "describe revenue"}, config={"configurable": {"thread_id": "py-analyst-1"}}
    )

    assert result["sql_results"]["row_count"] == 20
    assert result["python_analysis"] is not None
    assert result["python_analysis"]["error"] is None
    assert result["python_analysis"]["summary"]["count"] == 20


def test_python_analyst_skipped_when_statistics_not_required():
    analysis = QueryAnalysis(
        metric="revenue", analysis_type="descriptive",
        requires_sql=True, requires_statistics=False, requires_rag=False,
    )
    graph = _build(analysis, "SELECT id FROM orders LIMIT 5")

    result = graph.invoke(
        {"question": "list some orders"}, config={"configurable": {"thread_id": "py-analyst-2"}}
    )

    assert result["sql_results"]["row_count"] == 5
    assert result.get("python_analysis") is None


def test_requires_statistics_alone_pulls_in_sql_branch_and_runs_analyst():
    """`requires_sql=False` but `requires_statistics=True`: the router must
    still take the SQL branch, since statistics need the SQL Executor's
    data — see route_after_query_analysis."""
    analysis = QueryAnalysis(
        metric="revenue", analysis_type="descriptive",
        requires_sql=False, requires_statistics=True, requires_rag=False,
    )
    graph = _build(analysis, "SELECT unit_price AS revenue FROM order_items LIMIT 10")

    result = graph.invoke(
        {"question": "describe revenue"}, config={"configurable": {"thread_id": "py-analyst-3"}}
    )

    assert result["sql_results"]["row_count"] == 10
    assert result["python_analysis"]["summary"]["count"] == 10
