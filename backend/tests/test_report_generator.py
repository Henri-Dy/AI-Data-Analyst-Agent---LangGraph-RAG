from app.tools.report_generator import build_report


def test_report_assembles_all_fields():
    report = build_report(
        narrative="Revenue grew 12% in July.",
        confidence=0.95,
        sql_query="SELECT * FROM orders",
        sql_results={"columns": ["id"], "rows": [{"id": 1}], "row_count": 1, "truncated": False},
        visualization={"chart_type": "line", "figure": {"data": [], "layout": {}}, "error": None},
        fact_check_notes=['Verified: "Revenue grew 12%." (12.0).'],
        rag_context=[
            {"title": "Revenue Glossary", "category": "glossary", "content": "...", "source_path": "docs/rev.md", "distance": 0.1}
        ],
        human_review=None,
        errors=[],
    )

    assert report["answer"] == "Revenue grew 12% in July."
    assert report["confidence"] == 0.95
    assert report["sql"] == "SELECT * FROM orders"
    assert report["sql_row_count"] == 1
    assert report["chart"] == {"chart_type": "line", "figure": {"data": [], "layout": {}}}
    assert report["human_reviewed"] is False
    assert report["sources"] == [
        {"title": "Revenue Glossary", "category": "glossary", "source_path": "docs/rev.md"}
    ]


def test_report_omits_chart_when_visualization_failed():
    report = build_report(
        narrative="No data.",
        confidence=1.0,
        sql_query=None,
        sql_results=None,
        visualization={"chart_type": None, "figure": {}, "error": "No rows to visualize."},
        fact_check_notes=[],
        rag_context=[],
        human_review=None,
        errors=[],
    )

    assert report["chart"] is None
    assert report["sql_row_count"] is None


def test_report_marks_human_reviewed_when_review_present():
    report = build_report(
        narrative="Revised narrative.",
        confidence=0.4,
        sql_query=None,
        sql_results=None,
        visualization=None,
        fact_check_notes=["UNVERIFIED: ..."],
        rag_context=[],
        human_review={"approved": True, "reviewer_notes": "looks fine"},
        errors=[],
    )

    assert report["human_reviewed"] is True


def test_report_carries_errors_through():
    report = build_report(
        narrative="Could not run the query.",
        confidence=1.0,
        sql_query=None,
        sql_results=None,
        visualization=None,
        fact_check_notes=[],
        rag_context=[],
        human_review=None,
        errors=["SQL execution failed: syntax error"],
    )

    assert report["errors"] == ["SQL execution failed: syntax error"]
