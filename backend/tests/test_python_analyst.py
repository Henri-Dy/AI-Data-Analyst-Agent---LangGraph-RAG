"""Unit tests for the Python Data Analyst (deterministic, no DB/LLM needed —
`analyze()` operates purely on the SQL Executor's row/column output)."""
from decimal import Decimal

from app.tools.python_analyst import analyze


def test_descriptive_stats():
    rows = [{"revenue": 100}, {"revenue": 200}, {"revenue": 300}]
    result = analyze(rows, analysis_type="descriptive", metric="revenue")

    assert result.error is None
    assert result.summary["count"] == 3
    assert result.summary["mean"] == 200
    assert result.summary["sum"] == 600


def test_group_comparison_sorts_by_sum_descending():
    rows = [
        {"region": "north", "revenue": 100},
        {"region": "south", "revenue": 400},
        {"region": "north", "revenue": 50},
    ]
    result = analyze(rows, analysis_type="comparison", metric="revenue", dimensions=["region"])

    assert result.error is None
    assert result.table[0] == {"group": "south", "sum": 400.0, "mean": 400.0, "count": 1}
    assert result.table[1]["group"] == "north"
    assert result.table[1]["sum"] == 150.0
    assert result.summary["top_group"] == "south"


def test_group_comparison_without_dimensions_reports_error():
    rows = [{"revenue": 100}]
    result = analyze(rows, analysis_type="comparison", metric="revenue", dimensions=[])

    assert result.error is not None
    assert "dimension" in result.error.lower()


def test_ranking_reuses_group_comparison_handler():
    rows = [{"product": "A", "units": 10}, {"product": "B", "units": 30}]
    result = analyze(rows, analysis_type="ranking", metric="units", dimensions=["product"])

    assert result.error is None
    assert result.table[0]["group"] == "B"


def test_trend_detects_increasing_direction():
    rows = [
        {"month": "2026-01", "revenue": 100},
        {"month": "2026-02", "revenue": 150},
        {"month": "2026-03", "revenue": 200},
    ]
    result = analyze(rows, analysis_type="trend", metric="revenue")

    assert result.error is None
    assert result.summary["direction"] == "increasing"
    assert result.summary["time_column"] == "month"
    assert result.summary["first_value"] == 100
    assert result.summary["last_value"] == 200
    assert len(result.table) == 3


def test_trend_without_time_column_reports_error():
    rows = [{"revenue": 100}, {"revenue": 200}]
    result = analyze(rows, analysis_type="trend", metric="revenue")

    assert result.error is not None
    assert "date/period" in result.error


def test_correlation_finds_strongest_pair():
    rows = [
        {"revenue": 100, "orders": 10, "returns": 50},
        {"revenue": 200, "orders": 20, "returns": 5},
        {"revenue": 300, "orders": 30, "returns": 1},
    ]
    result = analyze(rows, analysis_type="correlation", metric="revenue")

    assert result.error is None
    assert result.summary["strongest_correlation"]["column"] == "orders"
    assert result.summary["strongest_correlation"]["correlation"] > 0.99


def test_correlation_needs_second_numeric_column():
    rows = [{"revenue": 100}, {"revenue": 200}]
    result = analyze(rows, analysis_type="correlation", metric="revenue")

    assert result.error is not None


def test_anomaly_detection_flags_outlier():
    # A single wild outlier against enough normal points that it can't drag
    # the standard deviation up far enough to mask its own z-score.
    normal = [100, 102, 98, 101, 99, 103, 97, 100, 102, 98]
    rows = [{"revenue": v} for v in normal] + [{"revenue": 5000}]
    result = analyze(rows, analysis_type="anomaly_detection", metric="revenue")

    assert result.error is None
    assert result.summary["anomaly_count"] == 1
    assert result.table[0]["revenue"] == 5000


def test_anomaly_detection_with_no_variance_reports_no_anomalies():
    rows = [{"revenue": 100}, {"revenue": 100}, {"revenue": 100}]
    result = analyze(rows, analysis_type="anomaly_detection", metric="revenue")

    assert result.error is None
    assert result.summary["anomaly_count"] == 0


def test_contribution_analysis_shares_sum_to_100_percent():
    rows = [
        {"region": "north", "revenue": 100},
        {"region": "south", "revenue": 300},
    ]
    result = analyze(rows, analysis_type="root_cause", metric="revenue", dimensions=["region"])

    assert result.error is None
    assert result.summary["top_contributor"] == "south"
    total_share = sum(row["share_pct"] for row in result.table)
    assert round(total_share, 6) == 100.0


def test_unknown_analysis_type_falls_back_to_descriptive():
    rows = [{"revenue": 100}, {"revenue": 200}]
    result = analyze(rows, analysis_type="something_new", metric="revenue")

    assert result.analysis_type == "descriptive"
    assert result.error is None


def test_empty_rows_reports_error_without_raising():
    result = analyze([], analysis_type="descriptive", metric="revenue")

    assert result.error == "No rows to analyze."


def test_decimal_columns_are_recognized_as_numeric():
    """psycopg returns PostgreSQL NUMERIC columns as decimal.Decimal, which
    pandas would otherwise treat as dtype object and hide from analysis."""
    rows = [{"revenue": Decimal("100.50")}, {"revenue": Decimal("200.25")}, {"revenue": Decimal("300.00")}]
    result = analyze(rows, analysis_type="descriptive", metric="revenue")

    assert result.error is None
    assert result.summary["sum"] == 600.75


def test_metric_resolution_falls_back_to_first_numeric_column():
    rows = [{"id": 1, "revenue": 500}]
    result = analyze(rows, analysis_type="descriptive", metric="nonexistent_metric_name")

    assert result.error is None
    assert result.summary["metric"] == "id"
