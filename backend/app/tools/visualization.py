"""Visualization Agent: auto-selects and builds a Plotly chart from SQL
query results.

Deliberately LLM-free and independent from the Python Data Analyst: it
reads the same raw SQL rows and picks a chart type from the Query
Analyzer's `analysis_type` and the shape of the data, so a chart is
produced even for plain SQL questions that never asked for statistics.
"""
import json
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from app.tools.tabular import coerce_numeric_columns, find_time_column, resolve_metric_column

ANOMALY_Z_THRESHOLD = 2.5
MAX_BAR_GROUPS = 25


@dataclass
class VisualizationResult:
    chart_type: str | None = None
    figure: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def visualize(
    rows: list[dict],
    analysis_type: str,
    metric: str | None = None,
    dimensions: list[str] | None = None,
) -> VisualizationResult:
    """Builds the chart matching `analysis_type` over `rows` (the SQL
    Executor's result set). Never raises: malformed or unexpected data is
    reported back as an `error` instead of crashing the graph.
    """
    if not rows:
        return VisualizationResult(error="No rows to visualize.")

    df = coerce_numeric_columns(pd.DataFrame(rows))
    dimensions = [d for d in (dimensions or []) if d in df.columns]

    metric_col = resolve_metric_column(df, metric)
    if metric_col is None:
        return VisualizationResult(error="The query result has no numeric column to chart.")

    handler = _HANDLERS.get(analysis_type, _default_chart)
    try:
        fig, chart_type = handler(df, metric_col, dimensions)
    except _VisualizationError as e:
        return VisualizationResult(error=str(e))

    return VisualizationResult(chart_type=chart_type, figure=json.loads(pio.to_json(fig)))


class _VisualizationError(Exception):
    """Raised for expected failure modes (no dimension to group by, no time
    column, ...) and turned into `VisualizationResult.error` by `visualize()`."""


def _line_chart(df: pd.DataFrame, metric_col: str, dimensions: list[str]) -> tuple[go.Figure, str]:
    time_col = find_time_column(df)
    if time_col is None:
        raise _VisualizationError("Trend charts require a date/period column in the result set.")

    ordered = df[[time_col, metric_col]].dropna().sort_values(time_col)
    fig = go.Figure(
        go.Scatter(x=ordered[time_col].astype(str), y=ordered[metric_col], mode="lines+markers")
    )
    fig.update_layout(xaxis_title=time_col, yaxis_title=metric_col)
    return fig, "line"


def _bar_chart(df: pd.DataFrame, metric_col: str, dimensions: list[str]) -> tuple[go.Figure, str]:
    if not dimensions:
        raise _VisualizationError("Bar charts require at least one dimension column in the result set.")

    if len(dimensions) >= 2:
        return _stacked_bar_chart(df, metric_col, dimensions)

    group_col = dimensions[0]
    grouped = df.groupby(group_col)[metric_col].sum().sort_values(ascending=False).head(MAX_BAR_GROUPS)
    fig = go.Figure(go.Bar(x=grouped.index.astype(str), y=grouped.values))
    fig.update_layout(xaxis_title=group_col, yaxis_title=metric_col)
    return fig, "bar"


def _stacked_bar_chart(df: pd.DataFrame, metric_col: str, dimensions: list[str]) -> tuple[go.Figure, str]:
    group_col, stack_col = dimensions[0], dimensions[1]
    pivoted = df.pivot_table(
        index=group_col, columns=stack_col, values=metric_col, aggfunc="sum", fill_value=0
    ).head(MAX_BAR_GROUPS)

    fig = go.Figure(
        [go.Bar(name=str(stack_value), x=pivoted.index.astype(str), y=pivoted[stack_value]) for stack_value in pivoted.columns]
    )
    fig.update_layout(barmode="stack", xaxis_title=group_col, yaxis_title=metric_col, legend_title=stack_col)
    return fig, "stacked_bar"


def _histogram(df: pd.DataFrame, metric_col: str, dimensions: list[str]) -> tuple[go.Figure, str]:
    fig = go.Figure(go.Histogram(x=df[metric_col].dropna()))
    fig.update_layout(xaxis_title=metric_col, yaxis_title="count")
    return fig, "histogram"


def _heatmap(df: pd.DataFrame, metric_col: str, dimensions: list[str]) -> tuple[go.Figure, str]:
    numeric_df = df.select_dtypes(include="number").dropna()
    if numeric_df.shape[1] < 2:
        raise _VisualizationError("Correlation heatmaps require at least two numeric columns.")

    corr = numeric_df.corr()
    fig = go.Figure(
        go.Heatmap(
            z=corr.values, x=list(corr.columns), y=list(corr.index), colorscale="RdBu", zmin=-1, zmax=1
        )
    )
    return fig, "heatmap"


def _anomaly_scatter(df: pd.DataFrame, metric_col: str, dimensions: list[str]) -> tuple[go.Figure, str]:
    series = df[metric_col].dropna()
    if series.count() < 2 or series.std() == 0:
        raise _VisualizationError("Anomaly charts require variance in the metric column.")

    z_scores = (series - series.mean()) / series.std()
    is_anomaly = z_scores.abs() > ANOMALY_Z_THRESHOLD
    time_col = find_time_column(df)
    x = df.loc[series.index, time_col].astype(str) if time_col else series.index.astype(str)

    colors = ["crimson" if a else "steelblue" for a in is_anomaly]
    fig = go.Figure(go.Scatter(x=x, y=series, mode="markers", marker={"color": colors}))
    fig.update_layout(xaxis_title=time_col or "row", yaxis_title=metric_col)
    return fig, "scatter"


def _default_chart(df: pd.DataFrame, metric_col: str, dimensions: list[str]) -> tuple[go.Figure, str]:
    """No specific analysis_type match (e.g. plain SQL question with no
    statistics requested): chart whatever the data shape supports."""
    if dimensions:
        return _bar_chart(df, metric_col, dimensions)
    return _histogram(df, metric_col, dimensions)


_HANDLERS = {
    "trend": _line_chart,
    "comparison": _bar_chart,
    "ranking": _bar_chart,
    "root_cause": _bar_chart,
    "correlation": _heatmap,
    "anomaly_detection": _anomaly_scatter,
    "descriptive": _histogram,
}
