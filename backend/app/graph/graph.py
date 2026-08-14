"""Assembles the LangGraph workflow.

Phase 4 wires up: Query Analyzer -> Schema Agent -> Intent Router
(conditional fan-out) -> RAG Search / SQL Analysis / Statistical Analysis
-> Join -> END. SQL Analysis and Statistical Analysis are placeholders
until Phase 5 and Phase 6 replace them with real agents; the graph
structure and routing already work end-to-end today.
"""
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.query_analyzer import StructuredQueryAnalyzer
from app.core.config import get_settings
from app.graph.nodes import (
    join_node,
    make_query_analyzer_node,
    make_rag_search_node,
    make_schema_agent_node,
    sql_analysis_stub_node,
    statistical_analysis_stub_node,
)
from app.graph.routing import BRANCH_JOIN, BRANCH_RAG, BRANCH_SQL, BRANCH_STATS, route_after_query_analysis
from app.graph.state import GraphState


def build_graph(analyzer: StructuredQueryAnalyzer, engine, session_factory, embeddings, top_k: int = 5):
    """Builds and compiles the graph from injected dependencies, so it can
    run against fakes in tests or real providers in production."""
    workflow = StateGraph(GraphState)

    workflow.add_node("query_analyzer", make_query_analyzer_node(analyzer))
    workflow.add_node("schema_agent", make_schema_agent_node(engine))
    workflow.add_node(BRANCH_RAG, make_rag_search_node(session_factory, embeddings, top_k=top_k))
    workflow.add_node(BRANCH_SQL, sql_analysis_stub_node)
    workflow.add_node(BRANCH_STATS, statistical_analysis_stub_node)
    workflow.add_node(BRANCH_JOIN, join_node)

    workflow.set_entry_point("query_analyzer")
    workflow.add_edge("query_analyzer", "schema_agent")
    workflow.add_conditional_edges(
        "schema_agent",
        route_after_query_analysis,
        [BRANCH_RAG, BRANCH_SQL, BRANCH_STATS, BRANCH_JOIN],
    )
    workflow.add_edge(BRANCH_RAG, BRANCH_JOIN)
    workflow.add_edge(BRANCH_SQL, BRANCH_JOIN)
    workflow.add_edge(BRANCH_STATS, BRANCH_JOIN)
    workflow.add_edge(BRANCH_JOIN, END)

    return workflow.compile(checkpointer=MemorySaver())


def build_default_graph():
    """Production factory: real LLM, real DB engine, real embeddings."""
    from app.agents.query_analyzer import get_query_analyzer_llm
    from app.database.session import SessionLocal, engine
    from app.rag.embeddings import get_embeddings

    settings = get_settings()
    return build_graph(
        analyzer=get_query_analyzer_llm(),
        engine=engine,
        session_factory=SessionLocal,
        embeddings=get_embeddings(),
        top_k=settings.rag_top_k,
    )
