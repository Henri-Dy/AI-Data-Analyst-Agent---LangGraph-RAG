from app.agents.query_analyzer import QueryAnalysis, analyze_query


class FakeAnalyzer:
    def __init__(self, result: QueryAnalysis):
        self.result = result
        self.last_input = None

    def invoke(self, prompt_input: dict) -> QueryAnalysis:
        self.last_input = prompt_input
        return self.result


def test_analyze_query_passes_question_through_and_returns_analysis():
    expected = QueryAnalysis(
        metric="revenue",
        period="July",
        analysis_type="root_cause",
        dimensions=["region", "product", "customer_segment"],
        requires_sql=True,
        requires_statistics=True,
        requires_rag=False,
    )
    fake = FakeAnalyzer(expected)

    result = analyze_query("Why did revenue decrease in July?", fake)

    assert result == expected
    assert fake.last_input == {"question": "Why did revenue decrease in July?"}


def test_query_analysis_defaults_dimensions_to_empty_list():
    analysis = QueryAnalysis(
        metric="revenue", analysis_type="descriptive",
        requires_sql=True, requires_statistics=False, requires_rag=False,
    )
    assert analysis.dimensions == []
    assert analysis.period is None
