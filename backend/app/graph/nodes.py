"""Node factories for the LangGraph workflow.

Each `make_*_node` closes over its dependencies (LLM, DB engine, embeddings,
...) so the graph itself stays dependency-free and easy to test with fakes
(see tests/test_graph_smoke.py) while production wires in real providers
via app.graph.graph.build_default_graph().
"""
from dataclasses import asdict

from app.agents.query_analyzer import StructuredQueryAnalyzer, analyze_query
from app.agents.schema_agent import inspect_schema
from app.graph.state import GraphState
from app.rag.retriever import retrieve


def make_query_analyzer_node(analyzer: StructuredQueryAnalyzer):
    def query_analyzer_node(state: GraphState) -> dict:
        analysis = analyze_query(state["question"], analyzer)
        return {
            "query_analysis": analysis.model_dump(),
            "requires_sql": analysis.requires_sql,
            "requires_statistics": analysis.requires_statistics,
            "requires_rag": analysis.requires_rag,
            # Default; overwritten by rag_search_node when that branch runs.
            "rag_context": [],
        }

    return query_analyzer_node


def make_schema_agent_node(engine):
    def schema_agent_node(state: GraphState) -> dict:
        schema = inspect_schema(engine)
        return {
            "schema_info": {
                name: {**asdict(table), "columns": [asdict(c) for c in table.columns]}
                for name, table in schema.items()
            }
        }

    return schema_agent_node


def make_rag_search_node(session_factory, embeddings, top_k: int = 5):
    def rag_search_node(state: GraphState) -> dict:
        if not state.get("requires_rag"):
            return {"rag_context": []}

        session = session_factory()
        try:
            results = retrieve(session, embeddings, state["question"], top_k=top_k)
        finally:
            session.close()
        return {"rag_context": [asdict(r) for r in results]}

    return rag_search_node


def sql_analysis_stub_node(state: GraphState) -> dict:
    """Placeholder — SQL generation/validation/execution ships in Phase 5."""
    return {}


def statistical_analysis_stub_node(state: GraphState) -> dict:
    """Placeholder — the Python Data Analyst agent ships in Phase 6."""
    return {}


def join_node(state: GraphState) -> dict:
    """Reconverges the parallel intent-router branches. A no-op today; later
    phases will extend this into the SQL Generator entry point."""
    return {}
