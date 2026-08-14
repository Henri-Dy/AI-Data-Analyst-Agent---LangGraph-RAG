from app.graph.routing import (
    BRANCH_JOIN,
    BRANCH_RAG,
    BRANCH_SQL,
    HUMAN_REVIEW,
    PYTHON_ANALYST,
    REPORT_GENERATOR,
    VISUALIZATION_AGENT,
    route_after_fact_check,
    route_after_query_analysis,
    route_after_sql_execution,
)


def test_routes_to_all_branches_when_all_required():
    branches = route_after_query_analysis(
        {"requires_rag": True, "requires_sql": True, "requires_statistics": True}
    )
    assert set(branches) == {BRANCH_RAG, BRANCH_SQL}


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


def test_requires_statistics_alone_still_routes_to_sql_branch():
    """Statistics have no data of their own — they run over the SQL
    Executor's results, so `requires_statistics` must pull in the SQL
    branch even when `requires_sql` itself is False."""
    branches = route_after_query_analysis(
        {"requires_rag": False, "requires_sql": False, "requires_statistics": True}
    )
    assert branches == [BRANCH_SQL]


def test_route_after_sql_execution_runs_python_analyst_when_needed():
    destination = route_after_sql_execution(
        {"requires_statistics": True, "sql_results": {"rows": [{"id": 1}], "row_count": 1}}
    )
    assert destination == PYTHON_ANALYST


def test_route_after_sql_execution_goes_to_visualization_when_stats_not_needed():
    """A chart is worth producing for any successful SQL question, not just
    statistical ones, so this skips the Python Analyst but not the chart."""
    destination = route_after_sql_execution(
        {"requires_statistics": False, "sql_results": {"rows": [{"id": 1}], "row_count": 1}}
    )
    assert destination == VISUALIZATION_AGENT


def test_route_after_sql_execution_skips_when_no_results():
    destination = route_after_sql_execution({"requires_statistics": True, "sql_results": None})
    assert destination == BRANCH_JOIN


def test_route_after_fact_check_goes_to_human_review_below_threshold():
    destination = route_after_fact_check({"confidence": 0.5}, confidence_threshold=0.70)
    assert destination == HUMAN_REVIEW


def test_route_after_fact_check_goes_to_report_generator_at_or_above_threshold():
    destination = route_after_fact_check({"confidence": 0.70}, confidence_threshold=0.70)
    assert destination == REPORT_GENERATOR


def test_route_after_fact_check_treats_missing_confidence_as_fully_confident():
    """No claims were made at all (nothing to fact-check) — nothing false
    to flag, so there's no reason to interrupt for human review."""
    destination = route_after_fact_check({"confidence": None}, confidence_threshold=0.70)
    assert destination == REPORT_GENERATOR
