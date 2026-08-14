"""Exercises the /api/chat and /api/chat/resume SSE endpoints end to end,
including the human-review interrupt/resume cycle, against a fake graph
(same fakes as tests/test_graph_insight_report_integration.py) so no real
LLM API key is required. The real Postgres instance executes the query.
"""
import json

from fastapi.testclient import TestClient
from langchain_community.embeddings import DeterministicFakeEmbedding

from app.agents.insight_agent import InsightClaim, InsightGeneration
from app.agents.query_analyzer import QueryAnalysis
from app.agents.sql_generator import SQLGeneration
from app.database.models.rag_documents import EMBEDDING_DIM
from app.database.session import SessionLocal, engine
from app.graph.graph import build_graph
from app.services.chat_service import get_graph
from main import app

ANALYSIS = QueryAnalysis(
    metric="revenue", analysis_type="descriptive",
    requires_sql=True, requires_statistics=False, requires_rag=False,
)


class FakeAnalyzer:
    def invoke(self, prompt_input: dict) -> QueryAnalysis:
        return ANALYSIS


class FixedSQLGenerator:
    def invoke(self, prompt_input: dict) -> SQLGeneration:
        return SQLGeneration(sql="SELECT 100 AS revenue", reasoning="fixed")


class ScriptedInsightAgent:
    def __init__(self, result: InsightGeneration):
        self.result = result

    def invoke(self, prompt_input: dict) -> InsightGeneration:
        return self.result


def _fake_graph(insight_agent):
    return build_graph(
        analyzer=FakeAnalyzer(),
        engine=engine,
        session_factory=SessionLocal,
        embeddings=DeterministicFakeEmbedding(size=EMBEDDING_DIM),
        sql_generator=FixedSQLGenerator(),
        sql_fixer=FixedSQLGenerator(),
        insight_agent=insight_agent,
    )


def _parse_sse_events(text: str) -> list[dict]:
    events = []
    for block in text.replace("\r\n", "\n").strip().split("\n\n"):
        if not block.strip():
            continue
        event_type, data = None, None
        for line in block.splitlines():
            if line.startswith("event:"):
                event_type = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data = line.removeprefix("data:").strip()
        events.append({"event": event_type, "data": json.loads(data) if data else None})
    return events


def test_chat_streams_updates_and_done_for_a_verified_answer():
    verified_agent = ScriptedInsightAgent(
        InsightGeneration(narrative="Revenue is 100.", claims=[InsightClaim(text="Revenue is 100.", value=100.0)])
    )
    app.dependency_overrides[get_graph] = lambda: _fake_graph(verified_agent)
    try:
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"question": "What is revenue?"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    events = _parse_sse_events(response.text)

    event_types = [e["event"] for e in events]
    assert "update" in event_types
    assert event_types[-1] == "done"

    done_event = events[-1]
    assert done_event["data"]["report"]["answer"] == "Revenue is 100."
    assert done_event["data"]["report"]["human_reviewed"] is False
    assert done_event["data"]["thread_id"]


def test_chat_auto_generates_thread_id_when_not_provided():
    verified_agent = ScriptedInsightAgent(InsightGeneration(narrative="No claims here.", claims=[]))
    app.dependency_overrides[get_graph] = lambda: _fake_graph(verified_agent)
    try:
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"question": "Hello?"})
    finally:
        app.dependency_overrides.clear()

    events = _parse_sse_events(response.text)
    thread_ids = {e["data"]["thread_id"] for e in events if e["data"]}
    assert len(thread_ids) == 1
    assert len(next(iter(thread_ids))) > 0


def test_chat_interrupts_for_human_review_and_resume_completes_it():
    unverified_agent = ScriptedInsightAgent(
        InsightGeneration(narrative="Revenue is 999.", claims=[InsightClaim(text="Revenue is 999.", value=999.0)])
    )
    fake_graph = _fake_graph(unverified_agent)
    app.dependency_overrides[get_graph] = lambda: fake_graph
    try:
        with TestClient(app) as client:
            first = client.post(
                "/api/chat", json={"question": "What is revenue?", "thread_id": "api-thread-1"}
            )
            first_events = _parse_sse_events(first.text)
            assert first_events[-1]["event"] == "interrupt"
            assert first_events[-1]["data"]["confidence"] == 0.0

            second = client.post(
                "/api/chat/resume",
                json={
                    "thread_id": "api-thread-1",
                    "approved": True,
                    "reviewer_notes": "fixed the number",
                    "edited_narrative": "Revenue is 100.",
                },
            )
    finally:
        app.dependency_overrides.clear()

    second_events = _parse_sse_events(second.text)
    assert second_events[-1]["event"] == "done"
    report = second_events[-1]["data"]["report"]
    assert report["answer"] == "Revenue is 100."
    assert report["human_reviewed"] is True
