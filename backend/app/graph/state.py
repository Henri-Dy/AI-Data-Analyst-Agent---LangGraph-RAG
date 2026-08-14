"""The shared state threaded through every node of the LangGraph workflow.

Fields are grouped by the phase that populates them. Later phases extend
this state rather than replacing it, so earlier nodes keep working
unchanged as the graph grows.
"""
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class GraphState(TypedDict, total=False):
    # --- Input / conversation memory (Phase 4) ---
    question: str
    messages: Annotated[list, add_messages]

    # --- Query Analyzer / Intent Router (Phase 4) ---
    query_analysis: dict[str, Any] | None
    requires_sql: bool
    requires_statistics: bool
    requires_rag: bool

    # --- Schema Agent (Phase 4) ---
    schema_info: dict[str, Any] | None
    schema_context: str

    # --- RAG Search (Phase 4, using the Phase 3 retriever) ---
    rag_context: list[dict[str, Any]]

    # --- SQL Generator / Validator / Fixer / Executor (Phase 5) ---
    sql_query: str | None
    sql_valid: bool | None
    sql_validation_errors: list[str]
    sql_fix_attempts: int
    sql_results: dict[str, Any] | None

    # --- Python Data Analyst (Phase 6) ---
    python_analysis: dict[str, Any] | None

    # --- Visualization Agent (Phase 7) ---
    visualization: dict[str, Any] | None

    # --- Insight Agent / Fact Checker / Report Generator (Phase 8) ---
    insights: str | None
    confidence: float | None
    fact_check_notes: list[str]
    final_report: dict[str, Any] | None

    # --- Cross-cutting ---
    errors: list[str]
