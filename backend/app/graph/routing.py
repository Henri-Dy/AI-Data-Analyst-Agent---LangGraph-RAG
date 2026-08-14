"""Conditional edge functions (the "Intent Router")."""
from app.graph.state import GraphState

BRANCH_RAG = "rag_search"
BRANCH_SQL = "sql_analysis"
BRANCH_STATS = "statistical_analysis"
BRANCH_JOIN = "join"


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
