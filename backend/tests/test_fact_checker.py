from decimal import Decimal

from app.tools.fact_checker import fact_check


def test_no_claims_verifies_at_full_confidence():
    result = fact_check(claims=[], python_analysis=None, sql_rows=None)

    assert result.confidence == 1.0
    assert "No numeric claims" in result.notes[0]


def test_claim_matching_python_analysis_summary_verifies():
    claims = [{"text": "Average revenue is 200.", "value": 200.0}]
    python_analysis = {"summary": {"mean": 200.0, "count": 3}, "table": []}

    result = fact_check(claims, python_analysis, sql_rows=None)

    assert result.confidence == 1.0
    assert result.notes[0].startswith("Verified")


def test_claim_matching_python_analysis_table_verifies():
    claims = [{"text": "The south region grew 12.5%.", "value": 12.5}]
    python_analysis = {"summary": {}, "table": [{"group": "south", "share_pct": 12.5}]}

    result = fact_check(claims, python_analysis, sql_rows=None)

    assert result.confidence == 1.0


def test_claim_matching_sql_rows_verifies():
    claims = [{"text": "There were 42 orders.", "value": 42.0}]

    result = fact_check(claims, python_analysis=None, sql_rows=[{"order_count": 42}])

    assert result.confidence == 1.0


def test_unverified_claim_lowers_confidence():
    claims = [
        {"text": "Average revenue is 200.", "value": 200.0},
        {"text": "Revenue tripled.", "value": 300.0},
    ]
    python_analysis = {"summary": {"mean": 200.0}, "table": []}

    result = fact_check(claims, python_analysis, sql_rows=None)

    assert result.confidence == 0.5
    assert any(note.startswith("UNVERIFIED") for note in result.notes)
    assert any(note.startswith("Verified") for note in result.notes)


def test_claim_within_relative_tolerance_still_verifies():
    claims = [{"text": "Average revenue is about 200.", "value": 200.4}]
    python_analysis = {"summary": {"mean": 200.0}, "table": []}

    result = fact_check(claims, python_analysis, sql_rows=None)

    assert result.confidence == 1.0


def test_decimal_values_in_sql_rows_are_matched():
    claims = [{"text": "Unit price is 19.99.", "value": 19.99}]

    result = fact_check(claims, python_analysis=None, sql_rows=[{"unit_price": Decimal("19.99")}])

    assert result.confidence == 1.0


def test_claim_with_no_value_is_unverified():
    claims = [{"text": "It's a nice trend.", "value": None}]

    result = fact_check(claims, python_analysis={"summary": {"mean": 1.0}, "table": []}, sql_rows=None)

    assert result.confidence == 0.0
