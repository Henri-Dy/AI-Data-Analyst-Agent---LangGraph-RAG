"""Conditional edge functions (the "Intent Router" and the SQL retry loop)."""
from app.graph.state import GraphState

BRANCH_RAG = "rag_search"
BRANCH_SQL = "sql_generator"
BRANCH_JOIN = "join"

SQL_VALIDATOR = "sql_validator"
SQL_FIXER = "sql_fixer"
SQL_EXECUTOR = "sql_executor"
SQL_GIVE_UP = "sql_give_up"
PYTHON_ANALYST = "python_analyst"
VISUALIZATION_AGENT = "visualization_agent"


def route_after_query_analysis(state: GraphState) -> list[str]:
    """Fans out to whichever branches the Query Analyzer flagged as needed.
    Statistical analysis has no data of its own to work from in this system
    — everything lives in Postgres — so `requires_statistics` routes into
    the SQL branch too; the Python Analyst then runs on the SQL Executor's
    results (see `route_after_sql_execution`). If nothing is needed, skips
    straight to the join node."""
    branches = []
    if state.get("requires_rag"):
        branches.append(BRANCH_RAG)
    if state.get("requires_sql") or state.get("requires_statistics"):
        branches.append(BRANCH_SQL)
    return branches or [BRANCH_JOIN]


def route_after_sql_validation(state: GraphState, max_fix_attempts: int) -> str:
    """Generator -> Validator -> (invalid) -> Fixer -> Validator, up to
    `max_fix_attempts` times, mirroring the retry loop from the architecture
    spec. Valid SQL proceeds to execution; exhausted retries give up cleanly."""
    if state.get("sql_valid"):
        return SQL_EXECUTOR
    if state.get("sql_fix_attempts", 0) >= max_fix_attempts:
        return SQL_GIVE_UP
    return SQL_FIXER


def route_after_sql_execution(state: GraphState) -> str:
    """Routes SQL results to the Python Data Analyst when statistics were
    requested (it hands off to the Visualization Agent itself once done —
    see `graph.py`), or straight to the Visualization Agent otherwise: a
    chart is worth producing for any successful SQL question, not just
    statistical ones. No rows at all means nothing to show; skip to join."""
    if not state.get("sql_results"):
        return BRANCH_JOIN
    if state.get("requires_statistics"):
        return PYTHON_ANALYST
    return VISUALIZATION_AGENT
