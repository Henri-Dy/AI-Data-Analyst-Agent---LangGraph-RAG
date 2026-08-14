"""Conditional edge functions (the "Intent Router" and the SQL retry loop)."""
from app.graph.state import GraphState

BRANCH_RAG = "rag_search"
BRANCH_SQL = "sql_generator"
BRANCH_STATS = "statistical_analysis"
BRANCH_JOIN = "join"

SQL_VALIDATOR = "sql_validator"
SQL_FIXER = "sql_fixer"
SQL_EXECUTOR = "sql_executor"
SQL_GIVE_UP = "sql_give_up"


def route_after_query_analysis(state: GraphState) -> list[str]:
    """Fans out to whichever branches the Query Analyzer flagged as needed.
    If none are needed, skips straight to the join node."""
    branches = []
    if state.get("requires_rag"):
        branches.append(BRANCH_RAG)
    if state.get("requires_sql"):
        branches.append(BRANCH_SQL)
    if state.get("requires_statistics"):
        branches.append(BRANCH_STATS)
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
