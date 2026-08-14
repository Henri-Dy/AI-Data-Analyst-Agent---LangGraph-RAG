"""Fact Checker: deterministically verifies every numeric claim the Insight
Agent made against the actual computed data, before the answer is returned.

Deliberately LLM-free (like the SQL Validator, Python Analyst, and
Visualization Agent): a claim is only as trustworthy as the arithmetic that
checks it, and an LLM checking another LLM's numbers proves nothing.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

RELATIVE_TOLERANCE = 0.01
ABSOLUTE_TOLERANCE = 0.005


@dataclass
class FactCheckResult:
    confidence: float
    notes: list[str] = field(default_factory=list)


def fact_check(
    claims: list[dict],
    python_analysis: dict[str, Any] | None,
    sql_rows: list[dict] | None,
) -> FactCheckResult:
    """Checks each claim's asserted `value` against every number found in
    `python_analysis` (summary + table) and `sql_rows` — the only two
    sources of ground truth available to the graph. A claim with no
    numeric match anywhere in that data is flagged as unverified.

    `confidence` is the fraction of claims that verified; a narrative with
    no numeric claims at all trivially has nothing false to report, so it
    verifies at full confidence.
    """
    if not claims:
        return FactCheckResult(confidence=1.0, notes=["No numeric claims to verify."])

    trusted_values = _collect_trusted_values(python_analysis, sql_rows)

    notes = []
    verified = 0
    for claim in claims:
        text, value = claim.get("text", ""), claim.get("value")
        if value is not None and _matches_any(float(value), trusted_values):
            verified += 1
            notes.append(f'Verified: "{text}" ({value}).')
        else:
            notes.append(f'UNVERIFIED: "{text}" ({value}) matches no computed value.')

    return FactCheckResult(confidence=verified / len(claims), notes=notes)


def _matches_any(value: float, trusted_values: list[float]) -> bool:
    return any(
        abs(value - trusted) <= max(ABSOLUTE_TOLERANCE, RELATIVE_TOLERANCE * abs(trusted))
        for trusted in trusted_values
    )


def _collect_trusted_values(
    python_analysis: dict[str, Any] | None, sql_rows: list[dict] | None
) -> list[float]:
    values: list[float] = []

    if python_analysis:
        values.extend(_flatten_numbers(python_analysis.get("summary")))
        for row in python_analysis.get("table") or []:
            values.extend(_flatten_numbers(row))

    for row in sql_rows or []:
        values.extend(_flatten_numbers(row))

    return values


def _flatten_numbers(obj: Any) -> list[float]:
    if isinstance(obj, bool):
        return []
    if isinstance(obj, (int, float, Decimal)):
        return [float(obj)]
    if isinstance(obj, dict):
        return [n for v in obj.values() for n in _flatten_numbers(v)]
    if isinstance(obj, (list, tuple)):
        return [n for v in obj for n in _flatten_numbers(v)]
    return []
