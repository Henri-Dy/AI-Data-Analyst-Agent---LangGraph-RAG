"""Node factories for the LangGraph workflow.

Each `make_*_node` closes over its dependencies (LLM, DB engine, embeddings,
...) so the graph itself stays dependency-free and easy to test with fakes
(see tests/test_graph_smoke.py) while production wires in real providers
via app.graph.graph.build_default_graph().
"""
import json
from dataclasses import asdict

from langgraph.types import interrupt

from app.agents.insight_agent import StructuredInsightAgent, generate_insight
from app.agents.query_analyzer import StructuredQueryAnalyzer, analyze_query
from app.agents.schema_agent import inspect_schema, schema_to_prompt_context
from app.agents.sql_fixer import StructuredSQLGenerator as StructuredSQLFixer
from app.agents.sql_fixer import fix_sql
from app.agents.sql_generator import StructuredSQLGenerator, generate_sql
from app.graph.state import GraphState
from app.rag.retriever import retrieve
from app.tools.fact_checker import fact_check
from app.tools.python_analyst import analyze
from app.tools.report_generator import build_report
from app.tools.sql_executor import execute_sql
from app.tools.sql_validator import validate_sql
from app.tools.visualization import visualize

DATA_CONTEXT_SAMPLE_ROWS = 20


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


def python_analyst_node(state: GraphState) -> dict:
    analysis = state.get("query_analysis") or {}
    result = analyze(
        rows=state["sql_results"]["rows"],
        analysis_type=analysis.get("analysis_type", "descriptive"),
        metric=analysis.get("metric"),
        dimensions=analysis.get("dimensions"),
    )
    return {"python_analysis": asdict(result)}


def visualization_node(state: GraphState) -> dict:
    analysis = state.get("query_analysis") or {}
    result = visualize(
        rows=state["sql_results"]["rows"],
        analysis_type=analysis.get("analysis_type", "descriptive"),
        metric=analysis.get("metric"),
        dimensions=analysis.get("dimensions"),
    )
    return {"visualization": asdict(result)}


def join_node(state: GraphState) -> dict:
    """Reconverges the parallel intent-router branches (RAG / SQL+stats+chart)
    before the Insight Agent turns whatever they produced into an answer."""
    return {}


def _build_data_context(state: GraphState) -> str:
    """Bounded, prompt-ready summary of whatever data the graph actually
    computed. Prefers the Python Analyst's already-aggregated output (small,
    verified numbers) over dumping raw SQL rows, and caps the row sample so
    a large result set never blows the Insight Agent's context window."""
    python_analysis = state.get("python_analysis")
    if python_analysis and not python_analysis.get("error"):
        parts = [f"Statistical analysis ({python_analysis['analysis_type']}):"]
        parts.append(f"Summary: {json.dumps(python_analysis['summary'], default=str)}")
        if python_analysis.get("table"):
            sample = python_analysis["table"][:DATA_CONTEXT_SAMPLE_ROWS]
            parts.append(f"Table (first {len(sample)} rows): {json.dumps(sample, default=str)}")
        return "\n".join(parts)

    sql_results = state.get("sql_results")
    if sql_results:
        sample = sql_results["rows"][:DATA_CONTEXT_SAMPLE_ROWS]
        return (
            f"SQL result: {sql_results['row_count']} row(s), columns {sql_results['columns']}.\n"
            f"Sample rows: {json.dumps(sample, default=str)}"
        )

    return "No SQL or statistical data was retrieved for this question."


def make_insight_agent_node(agent: StructuredInsightAgent):
    def insight_agent_node(state: GraphState) -> dict:
        result = generate_insight(
            question=state["question"],
            analysis=json.dumps(state.get("query_analysis") or {}),
            rag_context="\n\n".join(c["content"] for c in state.get("rag_context", [])),
            data_context=_build_data_context(state),
            agent=agent,
        )
        return {
            "insights": result.narrative,
            "insight_claims": [c.model_dump() for c in result.claims],
        }

    return insight_agent_node


def fact_checker_node(state: GraphState) -> dict:
    result = fact_check(
        claims=state.get("insight_claims", []),
        python_analysis=state.get("python_analysis"),
        sql_rows=(state.get("sql_results") or {}).get("rows"),
    )
    return {"confidence": result.confidence, "fact_check_notes": result.notes}


def human_review_node(state: GraphState) -> dict:
    """Pauses the graph via LangGraph's interrupt/resume mechanism when
    confidence falls below threshold, handing a human reviewer the
    narrative, its confidence, and the Fact Checker's notes. Resuming with
    `Command(resume={"approved": bool, "reviewer_notes": str, "edited_narrative": str | None})`
    lets the reviewer approve as-is or correct the narrative before the
    Report Generator runs.
    """
    decision = interrupt(
        {
            "reason": "confidence_below_threshold",
            "confidence": state.get("confidence"),
            "narrative": state.get("insights"),
            "fact_check_notes": state.get("fact_check_notes", []),
        }
    )
    return {
        "human_review": {
            "approved": decision.get("approved", False),
            "reviewer_notes": decision.get("reviewer_notes"),
        },
        "insights": decision.get("edited_narrative") or state.get("insights"),
    }


def report_generator_node(state: GraphState) -> dict:
    report = build_report(
        narrative=state.get("insights") or "",
        confidence=state.get("confidence") if state.get("confidence") is not None else 1.0,
        sql_query=state.get("sql_query"),
        sql_results=state.get("sql_results"),
        visualization=state.get("visualization"),
        fact_check_notes=state.get("fact_check_notes", []),
        rag_context=state.get("rag_context", []),
        human_review=state.get("human_review"),
        errors=state.get("errors", []),
    )
    return {"final_report": report}
