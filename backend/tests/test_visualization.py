"""Unit tests for the Visualization Agent (deterministic, no DB/LLM needed —
`visualize()` operates purely on the SQL Executor's row/column output)."""
from decimal import Decimal

from app.tools.visualization import visualize


def test_trend_produces_line_chart():
    rows = [
        {"month": "2026-01", "revenue": 100},
        {"month": "2026-02", "revenue": 150},
        {"month": "2026-03", "revenue": 200},
    ]
    result = visualize(rows, analysis_type="trend", metric="revenue")

    assert result.error is None
    assert result.chart_type == "line"
    assert result.figure["data"][0]["type"] == "scatter"
    assert list(result.figure["data"][0]["y"]) == [100, 150, 200]


def test_trend_without_time_column_reports_error():
    rows = [{"revenue": 100}, {"revenue": 200}]
    result = visualize(rows, analysis_type="trend", metric="revenue")

    assert result.error is not None
    assert result.chart_type is None


def test_comparison_produces_bar_chart():
    rows = [
        {"region": "north", "revenue": 100},
        {"region": "south", "revenue": 400},
    ]
    result = visualize(rows, analysis_type="comparison", metric="revenue", dimensions=["region"])

    assert result.error is None
    assert result.chart_type == "bar"
    assert result.figure["data"][0]["type"] == "bar"


def test_comparison_without_dimensions_reports_error():
    rows = [{"revenue": 100}]
    result = visualize(rows, analysis_type="comparison", metric="revenue", dimensions=[])

    assert result.error is not None


def test_two_dimensions_produce_stacked_bar_chart():
    rows = [
        {"region": "north", "channel": "online", "revenue": 100},
        {"region": "north", "channel": "retail", "revenue": 50},
        {"region": "south", "channel": "online", "revenue": 200},
    ]
    result = visualize(
        rows, analysis_type="comparison", metric="revenue", dimensions=["region", "channel"]
    )

    assert result.error is None
    assert result.chart_type == "stacked_bar"
    assert result.figure["layout"]["barmode"] == "stack"
    assert len(result.figure["data"]) == 2  # one bar trace per channel


def test_correlation_produces_heatmap():
    rows = [
        {"revenue": 100, "orders": 10},
        {"revenue": 200, "orders": 20},
        {"revenue": 300, "orders": 30},
    ]
    result = visualize(rows, analysis_type="correlation", metric="revenue")

    assert result.error is None
    assert result.chart_type == "heatmap"
    assert result.figure["data"][0]["type"] == "heatmap"


def test_correlation_needs_second_numeric_column():
    rows = [{"revenue": 100}, {"revenue": 200}]
    result = visualize(rows, analysis_type="correlation", metric="revenue")

    assert result.error is not None


def test_anomaly_detection_produces_scatter_with_highlighted_point():
    normal = [100, 102, 98, 101, 99, 103, 97, 100, 102, 98]
    rows = [{"revenue": v} for v in normal] + [{"revenue": 5000}]
    result = visualize(rows, analysis_type="anomaly_detection", metric="revenue")

    assert result.error is None
    assert result.chart_type == "scatter"
    colors = result.figure["data"][0]["marker"]["color"]
    assert colors[-1] == "crimson"
    assert all(c == "steelblue" for c in colors[:-1])


def test_descriptive_produces_histogram():
    rows = [{"revenue": 100}, {"revenue": 200}, {"revenue": 300}]
    result = visualize(rows, analysis_type="descriptive", metric="revenue")

    assert result.error is None
    assert result.chart_type == "histogram"
    assert result.figure["data"][0]["type"] == "histogram"


def test_unknown_analysis_type_falls_back_to_bar_when_dimension_present():
    rows = [{"region": "north", "revenue": 100}, {"region": "south", "revenue": 200}]
    result = visualize(rows, analysis_type="something_new", metric="revenue", dimensions=["region"])

    assert result.error is None
    assert result.chart_type == "bar"


def test_unknown_analysis_type_falls_back_to_histogram_without_dimensions():
    rows = [{"revenue": 100}, {"revenue": 200}]
    result = visualize(rows, analysis_type="something_new", metric="revenue")

    assert result.error is None
    assert result.chart_type == "histogram"


def test_empty_rows_reports_error_without_raising():
    result = visualize([], analysis_type="descriptive", metric="revenue")

    assert result.error == "No rows to visualize."
    assert result.chart_type is None


def test_no_numeric_column_reports_error():
    rows = [{"region": "north"}, {"region": "south"}]
    result = visualize(rows, analysis_type="descriptive", metric="revenue")

    assert result.error is not None


def test_decimal_columns_are_recognized_as_numeric():
    rows = [{"revenue": Decimal("100.50")}, {"revenue": Decimal("200.25")}]
    result = visualize(rows, analysis_type="descriptive", metric="revenue")

    assert result.error is None
    assert result.chart_type == "histogram"


def test_figure_is_json_serializable_plotly_spec():
    rows = [{"revenue": 100}, {"revenue": 200}]
    result = visualize(rows, analysis_type="descriptive", metric="revenue")

    assert "data" in result.figure
    assert "layout" in result.figure
