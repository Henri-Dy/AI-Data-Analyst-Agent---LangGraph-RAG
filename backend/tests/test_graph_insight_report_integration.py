"""Exercises the Insight Agent -> Fact Checker -> (Human Review) -> Report
Generator tail of the compiled graph, including the genuine LangGraph
interrupt/resume cycle for low-confidence answers. Uses fake LLMs so no
real API key is required; the real Postgres instance executes the (fixed,
literal) SQL so the Fact Checker has a deterministic number to check
claims against.
"""
from langchain_community.embeddings import DeterministicFakeEmbedding
from langgraph.types import Command

from app.agents.insight_agent import InsightClaim, InsightGeneration
from app.agents.query_analyzer import QueryAnalysis
from app.agents.sql_generator import SQLGeneration
from app.database.models.rag_documents import EMBEDDING_DIM
from app.database.session import SessionLocal, engine
from app.graph.graph import build_graph
from app.graph.routing import HUMAN_REVIEW

ANALYSIS = QueryAnalysis(
    metric="revenue", analysis_type="descriptive",
    requires_sql=True, requires_statistics=False, requires_rag=False,
)


class FakeAnalyzer:
    def invoke(self, prompt_input: dict) -> QueryAnalysis:
        return ANALYSIS


class FixedSQLGenerator:
    """A literal, table-free query — deterministic across runs, so the
    Fact Checker always has the same number (100) to check claims against."""

    def invoke(self, prompt_input: dict) -> SQLGeneration:
        return SQLGeneration(sql="SELECT 100 AS revenue", reasoning="fixed")


class ScriptedInsightAgent:
    def __init__(self, result: InsightGeneration):
        self.result = result

    def invoke(self, prompt_input: dict) -> InsightGeneration:
        return self.result


def _build(insight_agent, confidence_threshold=0.70):
    return build_graph(
        analyzer=FakeAnalyzer(),
        engine=engine,
        session_factory=SessionLocal,
        embeddings=DeterministicFakeEmbedding(size=EMBEDDING_DIM),
        sql_generator=FixedSQLGenerator(),
        sql_fixer=FixedSQLGenerator(),
        insight_agent=insight_agent,
        confidence_threshold=confidence_threshold,
    )


def test_verified_claim_produces_report_without_human_review():
    agent = ScriptedInsightAgent(
        InsightGeneration(
            narrative="Revenue is 100.",
            claims=[InsightClaim(text="Revenue is 100.", value=100.0)],
        )
    )
    graph = _build(agent)

    result = graph.invoke(
        {"question": "What is revenue?"}, config={"configurable": {"thread_id": "insight-verified"}}
    )

    assert result["confidence"] == 1.0
    assert result["final_report"]["answer"] == "Revenue is 100."
    assert result["final_report"]["confidence"] == 1.0
    assert result["final_report"]["human_reviewed"] is False
    assert result["final_report"]["sql"] == "SELECT 100 AS revenue"
    assert any(note.startswith("Verified") for note in result["final_report"]["fact_check_notes"])


def test_unverified_claim_interrupts_for_human_review_then_resumes():
    agent = ScriptedInsightAgent(
        InsightGeneration(
            narrative="Revenue is 999.",
            claims=[InsightClaim(text="Revenue is 999.", value=999.0)],
        )
    )
    graph = _build(agent)
    config = {"configurable": {"thread_id": "insight-unverified"}}

    graph.invoke({"question": "What is revenue?"}, config=config)
    state = graph.get_state(config)

    assert state.next == (HUMAN_REVIEW,)
    interrupt_payload = state.tasks[0].interrupts[0].value
    assert interrupt_payload["confidence"] == 0.0
    assert any(note.startswith("UNVERIFIED") for note in interrupt_payload["fact_check_notes"])

    result = graph.invoke(
        Command(resume={"approved": True, "reviewer_notes": "Corrected the figure.", "edited_narrative": "Revenue is 100."}),
        config=config,
    )

    assert result["human_review"] == {"approved": True, "reviewer_notes": "Corrected the figure."}
    assert result["final_report"]["answer"] == "Revenue is 100."
    assert result["final_report"]["human_reviewed"] is True


def test_interrupt_survives_checkpointing_a_python_analyst_int_dimension():
    """Regression test: LangGraph's checkpointer msgpack-serializes the
    full graph state at the human-review interrupt boundary. A
    comparison/ranking/root_cause analysis grouped by an integer column
    (e.g. `region_id`) used to leave a `numpy.float64` in `python_analysis`
    (see test_python_analyst.py::test_group_comparison_with_integer_dimension...),
    which made the checkpointer's serialization step itself blow up with
    "Type is not msgpack serializable" the moment confidence was low enough
    to interrupt — a failure only reachable through this exact combination
    (statistics + an int group column + an interrupt), not through the
    unit tests or the graph tests that use requires_statistics=False.
    """
    analysis = QueryAnalysis(
        metric="revenue", analysis_type="comparison", dimensions=["region_id"],
        requires_sql=True, requires_statistics=True, requires_rag=False,
    )

    class GroupedAnalyzer:
        def invoke(self, prompt_input: dict) -> QueryAnalysis:
            return analysis

    class GroupedSQLGenerator:
        def invoke(self, prompt_input: dict) -> SQLGeneration:
            return SQLGeneration(
                sql="SELECT * FROM (VALUES (1, 100.5), (2, 300.25), (1, 50.0)) AS t(region_id, revenue)",
                reasoning="fixed",
            )

    agent = ScriptedInsightAgent(
        InsightGeneration(
            narrative="Revenue is much higher in region 2.",
            claims=[InsightClaim(text="Region 2 made 999.", value=999.0)],  # deliberately unverifiable
        )
    )
    graph = build_graph(
        analyzer=GroupedAnalyzer(),
        engine=engine,
        session_factory=SessionLocal,
        embeddings=DeterministicFakeEmbedding(size=EMBEDDING_DIM),
        sql_generator=GroupedSQLGenerator(),
        sql_fixer=GroupedSQLGenerator(),
        insight_agent=agent,
    )
    config = {"configurable": {"thread_id": "insight-numpy-regression"}}

    # This used to raise inside the checkpointer before it ever got to
    # return; reaching the assertions at all is the regression check.
    graph.invoke({"question": "Compare revenue by region"}, config=config)
    state = graph.get_state(config)

    assert state.next == (HUMAN_REVIEW,)
    assert state.values["python_analysis"]["table"][0]["group"] == 2
    assert type(state.values["python_analysis"]["table"][0]["group"]) is int


def test_confidence_threshold_is_configurable():
    """A lower threshold accepts the same partially-verified answer without
    pausing for human review."""
    agent = ScriptedInsightAgent(
        InsightGeneration(
            narrative="Revenue is 999.",
            claims=[InsightClaim(text="Revenue is 999.", value=999.0)],
        )
    )
    graph = _build(agent, confidence_threshold=0.0)

    result = graph.invoke(
        {"question": "What is revenue?"}, config={"configurable": {"thread_id": "insight-low-threshold"}}
    )

    assert result["final_report"]["human_reviewed"] is False
    assert result["final_report"]["answer"] == "Revenue is 999."
