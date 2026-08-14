from app.agents.insight_agent import InsightClaim, InsightGeneration, generate_insight


class FakeInsightAgent:
    def __init__(self, result: InsightGeneration):
        self.result = result
        self.last_input = None

    def invoke(self, prompt_input: dict) -> InsightGeneration:
        self.last_input = prompt_input
        return self.result


def test_generate_insight_passes_all_context_through():
    expected = InsightGeneration(
        narrative="Revenue grew 12% in July, driven mostly by the North region.",
        claims=[InsightClaim(text="Revenue grew 12% in July.", value=12.0)],
    )
    fake = FakeInsightAgent(expected)

    result = generate_insight(
        question="Why did revenue grow in July?",
        analysis='{"metric": "revenue"}',
        rag_context="Revenue is defined as gross order value.",
        data_context="Summary: {'pct_change': 12.0}",
        agent=fake,
    )

    assert result == expected
    assert fake.last_input == {
        "question": "Why did revenue grow in July?",
        "analysis": '{"metric": "revenue"}',
        "rag_context": "Revenue is defined as gross order value.",
        "data_context": "Summary: {'pct_change': 12.0}",
    }


def test_insight_generation_defaults_claims_to_empty_list():
    result = InsightGeneration(narrative="No data was available to answer this question.")
    assert result.claims == []
