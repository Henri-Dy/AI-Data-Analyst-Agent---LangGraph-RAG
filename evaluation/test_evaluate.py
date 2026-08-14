"""Tests the evaluation harness's scoring/report logic against a fake graph
(same fake-LLM pattern as the backend test suite), so it's verified without
a real LLM API key or a real run of all ten questions. `evaluate.py`'s own
`main()` — wiring the real `build_default_graph()` — is exercised manually,
not here.

Run from backend/ (`cd backend && pytest ../evaluation/test_evaluate.py`),
same as evaluate.py itself: `Settings` loads backend/.env relative to the
working directory, so the real DATABASE_URL is only picked up from there.
"""
import json

from evaluate import run_evaluation, run_question, write_report

from langchain_community.embeddings import DeterministicFakeEmbedding

from app.agents.insight_agent import InsightGeneration
from app.agents.query_analyzer import QueryAnalysis
from app.agents.sql_generator import SQLGeneration
from app.database.models.rag_documents import EMBEDDING_DIM
from app.database.session import SessionLocal, engine
from app.graph.graph import build_graph


class FakeAnalyzer:
    def __init__(self, analysis: QueryAnalysis):
        self.analysis = analysis

    def invoke(self, prompt_input: dict) -> QueryAnalysis:
        return self.analysis


class FakeSQLGenerator:
    def __init__(self, sql: str):
        self.sql = sql

    def invoke(self, prompt_input: dict) -> SQLGeneration:
        return SQLGeneration(sql=self.sql, reasoning="fake")


class FakeInsightAgent:
    def invoke(self, prompt_input: dict) -> InsightGeneration:
        return InsightGeneration(narrative="Here is the answer.", claims=[])


def _build_graph(analysis: QueryAnalysis, sql: str):
    return build_graph(
        analyzer=FakeAnalyzer(analysis),
        engine=engine,
        session_factory=SessionLocal,
        embeddings=DeterministicFakeEmbedding(size=EMBEDDING_DIM),
        sql_generator=FakeSQLGenerator(sql),
        sql_fixer=FakeSQLGenerator(sql),
        insight_agent=FakeInsightAgent(),
    )


def test_run_question_passes_when_sql_is_expected_and_succeeds():
    analysis = QueryAnalysis(
        metric="revenue", analysis_type="descriptive",
        requires_sql=True, requires_statistics=False, requires_rag=False,
    )
    graph = _build_graph(analysis, "SELECT 100 AS revenue")

    result = run_question(graph, {"id": "q1", "question": "What is revenue?", "expects_sql": True})

    assert result.passed
    assert result.sql_generated
    assert result.sql_succeeded
    assert result.confidence == 1.0
    assert result.answer == "Here is the answer."
    assert result.failure_reasons == []


def test_run_question_fails_when_sql_expected_but_not_generated():
    analysis = QueryAnalysis(
        metric="revenue", analysis_type="descriptive",
        requires_sql=False, requires_statistics=False, requires_rag=False,
    )
    graph = _build_graph(analysis, "SELECT 100 AS revenue")

    result = run_question(graph, {"id": "q2", "question": "What is revenue?", "expects_sql": True})

    assert not result.passed
    assert any("expected SQL" in reason for reason in result.failure_reasons)


def test_run_evaluation_aggregates_summary_stats():
    analysis = QueryAnalysis(
        metric="revenue", analysis_type="descriptive",
        requires_sql=True, requires_statistics=False, requires_rag=False,
    )
    graph = _build_graph(analysis, "SELECT 100 AS revenue")
    questions = [
        {"id": "q1", "question": "What is revenue?", "expects_sql": True},
        {"id": "q2", "question": "What was revenue last month?", "expects_sql": True},
    ]

    report = run_evaluation(graph, questions)

    assert report["summary"]["total"] == 2
    assert report["summary"]["passed"] == 2
    assert report["summary"]["human_review_rate"] == 0.0
    assert report["summary"]["avg_confidence"] == 1.0
    assert len(report["results"]) == 2


def test_write_report_creates_a_timestamped_json_file(tmp_path, monkeypatch):
    import evaluate as evaluate_module

    monkeypatch.setattr(evaluate_module, "REPORTS_DIR", tmp_path)
    report = {"summary": {"total": 1, "passed": 1}, "results": []}

    path = write_report(report)

    assert path.parent == tmp_path
    assert path.suffix == ".json"
    assert json.loads(path.read_text()) == report
