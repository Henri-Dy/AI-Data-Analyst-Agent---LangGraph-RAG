"""Evaluation harness: runs a fixed set of representative business questions
(questions.json) through the compiled graph end to end and scores the
results, so a change to any agent's prompt or logic can be checked against
a repeatable baseline instead of eyeballing a handful of manual questions.

Run with (requires an LLM API key in backend/.env, and the demo dataset
seeded — see the main README's Installation section). Like the scripts
under backend/scripts/, it must run with backend/ as the working directory
so `Settings` finds backend/.env (loaded relative to cwd, not to this file):

    cd backend
    python ../evaluation/evaluate.py

Writes a timestamped JSON report to evaluation/reports/.
"""
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

QUESTIONS_PATH = Path(__file__).parent / "questions.json"
REPORTS_DIR = Path(__file__).parent / "reports"


@dataclass
class QuestionResult:
    id: str
    question: str
    passed: bool
    sql_generated: bool
    sql_succeeded: bool
    chart_produced: bool
    confidence: float | None
    required_human_review: bool
    answer: str
    failure_reasons: list[str]
    duration_seconds: float


def load_questions() -> list[dict[str, Any]]:
    return json.loads(QUESTIONS_PATH.read_text())


def run_question(graph, question: dict[str, Any]) -> QuestionResult:
    """Runs one question through the graph and scores the result against
    that question's expectations. A question "passes" if the pipeline
    behaved consistently with what it claims to need — not on the
    narrative's factual content, which the graph's own Fact Checker
    already verifies before a report is returned.
    """
    config = {"configurable": {"thread_id": f"eval-{question['id']}"}}

    start = time.monotonic()
    result = graph.invoke({"question": question["question"]}, config=config)
    duration = time.monotonic() - start

    required_human_review = bool(graph.get_state(config).next)
    sql_query = result.get("sql_query")
    sql_results = result.get("sql_results")
    visualization = result.get("visualization") or {}
    report = result.get("final_report")

    failure_reasons = []
    if question.get("expects_sql") and not sql_query:
        failure_reasons.append("expected SQL to be generated, but none was")
    if sql_query and not sql_results:
        failure_reasons.append("SQL was generated but did not execute successfully")
    if report is None and not required_human_review:
        failure_reasons.append("no final report was produced")
    if report is not None and report.get("errors"):
        failure_reasons.append(f"report carries errors: {report['errors']}")

    return QuestionResult(
        id=question["id"],
        question=question["question"],
        passed=not failure_reasons,
        sql_generated=bool(sql_query),
        sql_succeeded=bool(sql_results),
        chart_produced=bool(visualization.get("chart_type")) and not visualization.get("error"),
        confidence=result.get("confidence"),
        required_human_review=required_human_review,
        answer=(report or {}).get("answer", ""),
        failure_reasons=failure_reasons,
        duration_seconds=round(duration, 2),
    )


def run_evaluation(graph, questions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    questions = load_questions() if questions is None else questions
    results = [run_question(graph, q) for q in questions]
    confidences = [r.confidence for r in results if r.confidence is not None]

    summary = {
        "total": len(results),
        "passed": sum(r.passed for r in results),
        "human_review_rate": sum(r.required_human_review for r in results) / len(results) if results else 0.0,
        "avg_confidence": sum(confidences) / len(confidences) if confidences else None,
    }
    return {"summary": summary, "results": [asdict(r) for r in results]}


def write_report(report: dict[str, Any]) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = REPORTS_DIR / f"{timestamp}.json"
    path.write_text(json.dumps(report, indent=2, default=str))
    return path


def main() -> None:
    from app.graph.graph import build_default_graph

    graph = build_default_graph()
    report = run_evaluation(graph)
    path = write_report(report)

    summary = report["summary"]
    print(f"Evaluated {summary['total']} question(s) — {summary['passed']} passed.")
    print(f"Human review rate: {summary['human_review_rate']:.0%}")
    if summary["avg_confidence"] is not None:
        print(f"Average confidence: {summary['avg_confidence']:.0%}")
    print(f"Report written to {path}")

    for result in report["results"]:
        if not result["passed"]:
            print(f"  FAILED [{result['id']}]: {'; '.join(result['failure_reasons'])}")


if __name__ == "__main__":
    main()
