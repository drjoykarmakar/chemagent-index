import json

import pytest

from chemagent.config import load_policy
from chemagent.scoring.engine import parse_response, score_task

WEIGHTS = load_policy()["reliability"]


def response(answer, confidence=1, citations=None):
    return json.dumps(
        dict(
            answer=answer,
            confidence=confidence,
            citations=citations or [],
            reasoning_summary="Independent calculation.",
            uncertainties=[],
        )
    )


def test_gold_answers_and_calibration(dataset):
    for task in dataset[1]:
        result = score_task(task, response(task.reference_answer), WEIGHTS)
        assert result["score"] == 100
        assert result["cri"] == 100
        assert result["reproducibility"] == 100
        assert not result["errors"]


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        "[]",
        "{}",
        '{"answer": {}, "confidence": NaN}',
        '{"x":1,"x":2}',
        "x" * 128001,
        '{"confidence":Infinity}',
    ],
)
def test_malformed_response_scores_zero(dataset, raw):
    result = score_task(dataset[1][0], raw, WEIGHTS)
    assert result["score"] == result["cri"] == 0
    assert not result["parse_valid"]


def test_numeric_partial_credit_and_magnitude(dataset):
    task = dataset[1][0]
    answer = dict(task.reference_answer)
    answer["concentration"] += 0.035
    result = score_task(task, response(answer), WEIGHTS)
    assert result["score"] == pytest.approx(75)
    assert result["fields"][0]["absolute_error"] == pytest.approx(0.035)


def test_type_confusion_missing_and_extra(dataset):
    task = dataset[1][0]
    answer = dict(task.reference_answer)
    answer["concentration"] = True
    assert score_task(task, response(answer), WEIGHTS)["score"] == 50
    assert score_task(task, response({}), WEIGHTS)["score"] == 0
    answer["surprise"] = 42
    assert not score_task(task, response(answer), WEIGHTS)["parse_valid"]


def test_fake_citation_penalty_and_overconfidence(dataset):
    task = dataset[1][0]
    clean = score_task(task, response(task.reference_answer), WEIGHTS)
    invented = score_task(
        task, response(task.reference_answer, citations=["fabricated-fixture"]), WEIGHTS
    )
    assert invented["cri"] < clean["cri"]
    assert invented["citations"][0]["status"] == "unsupported_in_fixture"
    assert score_task(task, response({}, confidence=1), WEIGHTS)["cri"] == 0
    assert score_task(task, response({}, confidence=0), WEIGHTS)["cri"] == pytest.approx(20)


def test_response_confidence_range(dataset):
    for confidence in [-0.1, 1.1]:
        assert not score_task(dataset[1][0], response({}, confidence), WEIGHTS)["parse_valid"]
    with pytest.raises(ValueError):
        parse_response('{"answer": {}, "answer": {}}')


def test_accepted_citations_cannot_dilute_field_errors(dataset):
    task = dataset[1][0].model_copy(update={"allowed_citations": ["fixture:accepted"]})
    baseline = score_task(task, response({}), WEIGHTS)
    flooded = score_task(task, response({}, citations=["fixture:accepted"] * 50), WEIGHTS)
    assert flooded["cri"] == baseline["cri"]
