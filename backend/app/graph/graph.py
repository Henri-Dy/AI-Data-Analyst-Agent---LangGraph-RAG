"""Assembles the LangGraph workflow.

Query Analyzer -> Schema Agent -> Intent Router (conditional fan-out) ->
  - RAG Search (real, Phase 3 retriever)
  - SQL Generator -> Validator -> (invalid, retries left) -> Fixer -> Validator
                             -> (valid) -> Executor -> (requires_statistics) -> Python Analyst -> Visualization Agent
                                                     -> (otherwise, rows exist) -> Visualization Agent
                             -> (invalid, retries exhausted) -> Give Up
-> Join -> Insight Agent -> Fact Checker -> (confidence < threshold) -> Human Review -> Report Generator -> END
                                          -> (confidence >= threshold) -----------------> Report Generator -> END
"""
from functools import partial

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.insight_agent import StructuredInsightAgent
from app.agents.query_analyzer import StructuredQueryAnalyzer
from app.agents.sql_fixer import StructuredSQLGenerator as StructuredSQLFixer
from app.agents.sql_generator import StructuredSQLGenerator
from app.core.config import get_settings
from app.graph.nodes import (
    fact_checker_node,
    human_review_node,
    join_node,
    make_insight_agent_node,
    make_query_analyzer_node,
    make_rag_search_node,
    make_schema_agent_node,
    make_sql_executor_node,
    make_sql_fixer_node,
    make_sql_generator_node,
    python_analyst_node,
    report_generator_node,
    sql_give_up_node,
    sql_validator_node,
    visualization_node,
)
from app.graph.routing import (
    BRANCH_JOIN,
    BRANCH_RAG,
    BRANCH_SQL,
    FACT_CHECKER,
    HUMAN_REVIEW,
    INSIGHT_AGENT,
    PYTHON_ANALYST,
    REPORT_GENERATOR,
    SQL_EXECUTOR,
    SQL_FIXER,
    SQL_GIVE_UP,
    SQL_VALIDATOR,
    VISUALIZATION_AGENT,
    route_after_fact_check,
    route_after_query_analysis,
    route_after_sql_execution,
    route_after_sql_validation,
)
from app.graph.state import GraphState


def build_graph(
    analyzer: StructuredQueryAnalyzer,
    engine,
    session_factory,
    embeddings,
    sql_generator: StructuredSQLGenerator,
    sql_fixer: StructuredSQLFixer,
    insight_agent: StructuredInsightAgent,
    top_k: int = 5,
    max_sql_rows: int = 10_000,
    sql_timeout_seconds: int = 15,
    max_sql_fix_attempts: int = 3,
    confidence_threshold: float = 0.70,
):
    """Builds and compiles the graph from injected dependencies, so it can
    run against fakes in tests or real providers in production."""
    workflow = StateGraph(GraphState)

    workflow.add_node("query_analyzer", make_query_analyzer_node(analyzer))
    workflow.add_node("schema_agent", make_schema_agent_node(engine))
    workflow.add_node(BRANCH_RAG, make_rag_search_node(session_factory, embeddings, top_k=top_k))
    workflow.add_node(BRANCH_SQL, make_sql_generator_node(sql_generator))
    workflow.add_node(SQL_VALIDATOR, sql_validator_node)
    workflow.add_node(SQL_FIXER, make_sql_fixer_node(sql_fixer))
    workflow.add_node(SQL_EXECUTOR, make_sql_executor_node(engine, max_sql_rows, sql_timeout_seconds))
    workflow.add_node(SQL_GIVE_UP, sql_give_up_node)
    workflow.add_node(PYTHON_ANALYST, python_analyst_node)
    workflow.add_node(VISUALIZATION_AGENT, visualization_node)
    workflow.add_node(BRANCH_JOIN, join_node)
    workflow.add_node(INSIGHT_AGENT, make_insight_agent_node(insight_agent))
    workflow.add_node(FACT_CHECKER, fact_checker_node)
    workflow.add_node(HUMAN_REVIEW, human_review_node)
    workflow.add_node(REPORT_GENERATOR, report_generator_node)

    workflow.set_entry_point("query_analyzer")
    workflow.add_edge("query_analyzer", "schema_agent")
    workflow.add_conditional_edges(
        "schema_agent",
        route_after_query_analysis,
        [BRANCH_RAG, BRANCH_SQL, BRANCH_JOIN],
    )
    workflow.add_edge(BRANCH_RAG, BRANCH_JOIN)

    workflow.add_edge(BRANCH_SQL, SQL_VALIDATOR)
    workflow.add_conditional_edges(
        SQL_VALIDATOR,
        partial(route_after_sql_validation, max_fix_attempts=max_sql_fix_attempts),
        [SQL_EXECUTOR, SQL_FIXER, SQL_GIVE_UP],
    )
    workflow.add_edge(SQL_FIXER, SQL_VALIDATOR)
    workflow.add_conditional_edges(
        SQL_EXECUTOR, route_after_sql_execution, [PYTHON_ANALYST, VISUALIZATION_AGENT, BRANCH_JOIN]
    )
    workflow.add_edge(SQL_GIVE_UP, BRANCH_JOIN)

    workflow.add_edge(PYTHON_ANALYST, VISUALIZATION_AGENT)
    workflow.add_edge(VISUALIZATION_AGENT, BRANCH_JOIN)

    workflow.add_edge(BRANCH_JOIN, INSIGHT_AGENT)
    workflow.add_edge(INSIGHT_AGENT, FACT_CHECKER)
    workflow.add_conditional_edges(
        FACT_CHECKER,
        partial(route_after_fact_check, confidence_threshold=confidence_threshold),
        [HUMAN_REVIEW, REPORT_GENERATOR],
    )
    workflow.add_edge(HUMAN_REVIEW, REPORT_GENERATOR)
    workflow.add_edge(REPORT_GENERATOR, END)

    return workflow.compile(checkpointer=MemorySaver())


def build_default_graph():
    """Production factory: real LLM, real DB engine, real embeddings."""
    from app.agents.insight_agent import get_insight_agent_llm
    from app.agents.query_analyzer import get_query_analyzer_llm
    from app.agents.sql_fixer import get_sql_fixer_llm
    from app.agents.sql_generator import get_sql_generator_llm
    from app.database.session import SessionLocal, engine
    from app.rag.embeddings import get_embeddings

    settings = get_settings()
    return build_graph(
        analyzer=get_query_analyzer_llm(),
        engine=engine,
        session_factory=SessionLocal,
        embeddings=get_embeddings(),
        sql_generator=get_sql_generator_llm(),
        sql_fixer=get_sql_fixer_llm(),
        insight_agent=get_insight_agent_llm(),
        top_k=settings.rag_top_k,
        max_sql_rows=settings.max_sql_rows,
        sql_timeout_seconds=settings.sql_timeout_seconds,
        max_sql_fix_attempts=settings.max_sql_fix_attempts,
        confidence_threshold=settings.confidence_threshold,
    )
