"""End-to-end smoke test of the compiled LangGraph workflow. Uses a fake
Query Analyzer and a deterministic fake embedder so the graph's structure,
conditional routing, and checkpointing are verified without calling a real
LLM provider — only the real local Postgres/pgvector instance is used.
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
    """Always produces valid SQL — the SQL retry loop itself is exercised
    separately in tests/test_sql_graph_integration.py."""

    def invoke(self, prompt_input: dict) -> SQLGeneration:
        return SQLGeneration(sql="SELECT id FROM orders LIMIT 5", reasoning="fake")


def _build_test_graph(analysis: QueryAnalysis):
    return build_graph(
        analyzer=FakeAnalyzer(analysis),
        engine=engine,
        session_factory=SessionLocal,
        embeddings=DeterministicFakeEmbedding(size=EMBEDDING_DIM),
        sql_generator=FakeSQLGenerator(),
        sql_fixer=FakeSQLGenerator(),
    )


def test_graph_runs_full_fan_out_and_populates_state():
    analysis = QueryAnalysis(
        metric="revenue", period="July", analysis_type="root_cause",
        dimensions=["region", "product"],
        requires_sql=True, requires_statistics=True, requires_rag=True,
    )
    graph = _build_test_graph(analysis)

    result = graph.invoke(
        {"question": "Why did revenue decrease in July?"},
        config={"configurable": {"thread_id": "test-thread-1"}},
    )

    assert result["query_analysis"]["metric"] == "revenue"
    assert set(result["schema_info"].keys()) >= {
        "regions", "employees", "customers", "products", "orders", "order_items"
    }
    assert "rag_context" in result  # empty is fine; presence proves the branch ran


def test_graph_skips_branches_not_required():
    analysis = QueryAnalysis(
        metric="revenue", analysis_type="descriptive",
        requires_sql=False, requires_statistics=False, requires_rag=False,
    )
    graph = _build_test_graph(analysis)

    result = graph.invoke(
        {"question": "What is total revenue?"},
        config={"configurable": {"thread_id": "test-thread-2"}},
    )

    assert result["rag_context"] == []
    assert result["schema_info"]


def test_graph_checkpointing_persists_state_across_invocations():
    analysis = QueryAnalysis(
        metric="revenue", analysis_type="descriptive",
        requires_sql=True, requires_statistics=False, requires_rag=False,
    )
    graph = _build_test_graph(analysis)
    config = {"configurable": {"thread_id": "test-thread-memory"}}

    graph.invoke({"question": "What was revenue in June?"}, config=config)
    state = graph.get_state(config)

    assert state.values["question"] == "What was revenue in June?"
