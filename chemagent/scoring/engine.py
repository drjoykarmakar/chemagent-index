"""Auditable typed-field scoring; no language model judges."""

import json
import math
from typing import Any

from pydantic import ValidationError

from chemagent.benchmarks.schema import Answer, Task
from chemagent.chemistry.rdkit_service import validate_smiles


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> None:
    raise ValueError(f"Nonfinite JSON value: {value}")


def parse_response(raw: str) -> Answer:
    if len(raw.encode()) > 128000:
        raise ValueError("Response exceeds size limit")
    value = json.loads(raw, object_pairs_hook=_no_duplicates, parse_constant=_reject_constant)
    return Answer.model_validate(value)


def score_task(task: Task, raw: str, reliability_weights: dict[str, float]) -> dict[str, Any]:
    try:
        response = parse_response(raw)
        if set(response.answer) - set(task.rubric):
            raise ValueError("Unexpected answer fields")
    except (ValueError, ValidationError, RecursionError):
        return {
            "score": 0.0,
            "cri": 0.0,
            "reproducibility": 0.0,
            "error_rate": 1.0,
            "calibration_error": 1.0,
            "parse_valid": False,
            "fields": [],
            "errors": ["invalid_json_or_schema"],
            "citations": [],
            "chemistry": None,
        }
    fields = []
    numerator = denominator = severity_error = severity_total = 0.0
    for key, rule in task.rubric.items():
        expected = task.reference_answer[key]
        observed = response.answer.get(key)
        difference = None
        credit = 0.0
        if (
            rule.kind == "number"
            and type(observed) in (int, float)
            and observed is not None
            and math.isfinite(observed)
        ):
            difference = abs(observed - expected)
            credit = max(0.0, 1.0 - max(0.0, difference - rule.tolerance) / (5 * rule.tolerance))
        elif type(observed) is type(expected) and observed == expected:
            credit = 1.0
        fields.append(
            {
                "field": key,
                "expected": expected,
                "observed": observed,
                "absolute_error": difference,
                "credit": credit,
                "severity": rule.severity,
            }
        )
        numerator += rule.weight * credit
        denominator += rule.weight
        severity_error += rule.severity * (1 - credit)
        severity_total += rule.severity
    citations = [
        {
            "identifier": c,
            "status": "in_fixture" if c in task.allowed_citations else "unsupported_in_fixture",
        }
        for c in response.citations
    ]
    unsupported = sum(c["status"] == "unsupported_in_fixture" for c in citations)
    severity_error += 5 * unsupported
    error_rate = min(1.0, severity_error / severity_total)
    correct = float(all(f["credit"] == 1 for f in fields) and not unsupported)
    calibration = (response.confidence - correct) ** 2
    cri = 100 * (
        1
        - reliability_weights["error_weight"] * error_rate
        - reliability_weights["calibration_weight"] * calibration
    )
    units_ok = (
        "unit" not in task.rubric or response.answer.get("unit") == task.reference_answer["unit"]
    )
    repro = 40 + 20 * bool(response.reasoning_summary.strip()) + 20 + 20 * units_ok
    chemistry = validate_smiles(task.inputs["smiles"]) if "smiles" in task.inputs else None
    return {
        "score": 100 * numerator / denominator,
        "cri": max(0.0, cri),
        "reproducibility": repro,
        "error_rate": error_rate,
        "calibration_error": calibration,
        "parse_valid": True,
        "fields": fields,
        "errors": [f["field"] for f in fields if f["credit"] < 1],
        "citations": citations,
        "chemistry": chemistry,
    }
