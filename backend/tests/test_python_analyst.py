"""Unit tests for the Python Data Analyst (deterministic, no DB/LLM needed —
`analyze()` operates purely on the SQL Executor's row/column output)."""
from dataclasses import asdict
from decimal import Decimal

from app.tools.python_analyst import analyze


def _assert_no_numpy_leaks(obj, path="result"):
    """LangGraph's checkpointer msgpack-serializes graph state on every
    step (needed for the interrupt/resume human-review flow), and msgpack
    doesn't know how to encode numpy scalar types. pandas silently
    upcasts a whole row to a shared dtype in `.iterrows()`, so a plain
    `int()`/`float()` cast in the source isn't enough on its own to catch
    this — this walks the actual returned structure and fails on any
    leftover `numpy.*` type."""
    type_module = type(obj).__module__
    assert not type_module.startswith("numpy"), f"{path} is {type(obj)}, not a native Python type"
    if isinstance(obj, dict):
        for key, value in obj.items():
            _assert_no_numpy_leaks(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            _assert_no_numpy_leaks(value, f"{path}[{i}]")


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
    _assert_no_numpy_leaks(asdict(result))

    assert result.error is None
    assert result.table[0] == {"group": "south", "sum": 400.0, "mean": 400.0, "count": 1}
    assert result.table[1]["group"] == "north"
    assert result.table[1]["sum"] == 150.0
    assert result.summary["top_group"] == "south"


def test_group_comparison_with_integer_dimension_returns_native_int_group():
    """Regression test: grouping by an int column (e.g. a foreign key like
    `region_id`) used to come back as `numpy.float64` — pandas' `.iterrows()`
    upcasts an entire row to one shared dtype when the row mixes the int64
    group column with the float64 sum/mean columns, silently turning the
    group key into a float. That broke LangGraph's checkpoint serialization
    (see _assert_no_numpy_leaks) the moment a comparison/ranking/root_cause
    question grouped by a numeric column and confidence dropped low enough
    to hit the human-review interrupt."""
    rows = [
        {"region_id": 1, "revenue": 100.5},
        {"region_id": 2, "revenue": 300.25},
        {"region_id": 1, "revenue": 50.0},
    ]
    result = analyze(rows, analysis_type="comparison", metric="revenue", dimensions=["region_id"])
    _assert_no_numpy_leaks(asdict(result))

    assert result.error is None
    assert result.table[0]["group"] == 2
    assert type(result.table[0]["group"]) is int
    assert type(result.summary["top_group"]) is int


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


def test_anomaly_detection_with_other_int_column_returns_native_types():
    """Same regression as test_group_comparison_with_integer_dimension...:
    the anomalous rows carry every original column through (`region_id`
    here), and `.iterrows()` used to upcast that int column to float64
    alongside the float `revenue` column in the same row."""
    normal = [100, 102, 98, 101, 99, 103, 97, 100, 102, 98]
    rows = [{"region_id": i, "revenue": v} for i, v in enumerate(normal)] + [{"region_id": 99, "revenue": 5000}]
    result = analyze(rows, analysis_type="anomaly_detection", metric="revenue")
    _assert_no_numpy_leaks(asdict(result))

    assert result.table[0]["region_id"] == 99
    assert type(result.table[0]["region_id"]) is int


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
