"""Report Generator: assembles the final answer from everything the graph
already computed — SQL, chart, insights, sources — into one response.

Deliberately just an assembly step: it produces no new facts and calls no
LLM. Every field it writes was already verified (SQL by the validator/
executor, narrative claims by the Fact Checker) upstream.
"""
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Report:
    answer: str
    confidence: float
    sql: str | None = None
    sql_row_count: int | None = None
    chart: dict[str, Any] | None = None
    fact_check_notes: list[str] = field(default_factory=list)
    human_reviewed: bool = False
    sources: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_report(
    narrative: str,
    confidence: float,
    sql_query: str | None,
    sql_results: dict[str, Any] | None,
    visualization: dict[str, Any] | None,
    fact_check_notes: list[str],
    rag_context: list[dict[str, Any]],
    human_review: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, Any]:
    chart = None
    if visualization and visualization.get("chart_type") and not visualization.get("error"):
        chart = {"chart_type": visualization["chart_type"], "figure": visualization["figure"]}

    sources = [
        {"title": doc["title"], "category": doc["category"], "source_path": doc["source_path"]}
        for doc in (rag_context or [])
    ]

    report = Report(
        answer=narrative,
        confidence=confidence,
        sql=sql_query,
        sql_row_count=(sql_results or {}).get("row_count"),
        chart=chart,
        fact_check_notes=fact_check_notes,
        human_reviewed=human_review is not None,
        sources=sources,
        errors=errors,
    )
    return asdict(report)
