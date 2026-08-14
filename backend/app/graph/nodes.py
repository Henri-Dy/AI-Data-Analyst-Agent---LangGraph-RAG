"""Node factories for the LangGraph workflow.

Each `make_*_node` closes over its dependencies (LLM, DB engine, embeddings,
...) so the graph itself stays dependency-free and easy to test with fakes
(see tests/test_graph_smoke.py) while production wires in real providers
via app.graph.graph.build_default_graph().
"""
import json
from dataclasses import asdict

from app.agents.query_analyzer import StructuredQueryAnalyzer, analyze_query
from app.agents.schema_agent import inspect_schema, schema_to_prompt_context
from app.agents.sql_fixer import StructuredSQLGenerator as StructuredSQLFixer
from app.agents.sql_fixer import fix_sql
from app.agents.sql_generator import StructuredSQLGenerator, generate_sql
from app.graph.state import GraphState
from app.rag.retriever import retrieve
from app.tools.sql_executor import execute_sql
from app.tools.sql_validator import validate_sql


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
            },
            "schema_context": schema_to_prompt_context(schema),
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


def make_sql_generator_node(generator: StructuredSQLGenerator):
    def sql_generator_node(state: GraphState) -> dict:
        result = generate_sql(
            question=state["question"],
            schema=state.get("schema_context", ""),
            analysis=json.dumps(state.get("query_analysis") or {}),
            rag_context="\n\n".join(c["content"] for c in state.get("rag_context", [])),
            generator=generator,
        )
        return {"sql_query": result.sql, "sql_fix_attempts": 0, "sql_validation_errors": []}

    return sql_generator_node


def sql_validator_node(state: GraphState) -> dict:
    result = validate_sql(state["sql_query"], state["schema_info"])
    return {"sql_valid": result.valid, "sql_validation_errors": result.errors}


def make_sql_fixer_node(fixer: StructuredSQLFixer):
    def sql_fixer_node(state: GraphState) -> dict:
        result = fix_sql(
            question=state["question"],
            schema=state.get("schema_context", ""),
            sql=state["sql_query"],
            errors="; ".join(state.get("sql_validation_errors", [])),
            fixer=fixer,
        )
        return {"sql_query": result.sql, "sql_fix_attempts": state.get("sql_fix_attempts", 0) + 1}

    return sql_fixer_node


def make_sql_executor_node(engine, max_rows: int, timeout_seconds: int):
    def sql_executor_node(state: GraphState) -> dict:
        result = execute_sql(engine, state["sql_query"], max_rows=max_rows, timeout_seconds=timeout_seconds)
        if not result.success:
            return {
                "sql_results": None,
                "errors": [*state.get("errors", []), f"SQL execution failed: {result.error}"],
            }
        return {
            "sql_results": {
                "columns": result.columns,
                "rows": result.rows,
                "row_count": result.row_count,
                "truncated": result.truncated,
            }
        }

    return sql_executor_node


def sql_give_up_node(state: GraphState) -> dict:
    """Reached when the SQL Fixer exhausts its retry budget without producing
    valid SQL. Records the failure instead of silently dropping it."""
    errors = state.get("sql_validation_errors", [])
    return {
        "sql_results": None,
        "errors": [
            *state.get("errors", []),
            f"Could not produce valid SQL after {state.get('sql_fix_attempts', 0)} fix "
            f"attempt(s): {'; '.join(errors)}",
        ],
    }


def statistical_analysis_stub_node(state: GraphState) -> dict:
    """Placeholder — the Python Data Analyst agent ships in Phase 6."""
    return {}


def join_node(state: GraphState) -> dict:
    """Reconverges the parallel intent-router branches. A no-op today; later
    phases will extend this into the SQL Generator entry point."""
    return {}
