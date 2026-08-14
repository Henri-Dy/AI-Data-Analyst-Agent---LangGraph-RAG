from app.graph.routing import BRANCH_JOIN, BRANCH_RAG, BRANCH_SQL, BRANCH_STATS, route_after_query_analysis


def test_routes_to_all_branches_when_all_required():
    branches = route_after_query_analysis(
        {"requires_rag": True, "requires_sql": True, "requires_statistics": True}
    )
    assert set(branches) == {BRANCH_RAG, BRANCH_SQL, BRANCH_STATS}


def test_routes_to_join_only_when_nothing_required():
    branches = route_after_query_analysis(
        {"requires_rag": False, "requires_sql": False, "requires_statistics": False}
    )
    assert branches == [BRANCH_JOIN]


def test_routes_to_sql_only():
    branches = route_after_query_analysis(
        {"requires_rag": False, "requires_sql": True, "requires_statistics": False}
    )
    assert branches == [BRANCH_SQL]
