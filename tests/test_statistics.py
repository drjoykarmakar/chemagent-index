import pytest

from chemagent.statistics.bootstrap import compare_paired, public_summary, summarize


def rows(offset=0):
    return [
        dict(
            task_id=f"{category}{i}",
            category=category,
            cluster_id=f"{category}{i // 2}",
            score=value + offset,
        )
        for category in ["a", "b"]
        for i, value in enumerate([10, 20, 40, 80])
    ]


def test_reproducible_stratified_statistics():
    first = summarize(rows(), {"a": 1, "b": 1})
    assert first == summarize(rows(), {"a": 1, "b": 1})
    assert first["mean"] == 37.5
    assert first["ci95"][0] <= first["mean"] <= first["ci95"][1]
    assert first["categories"]["a"]["clusters"] == 2
    assert first["standard_error"] > 0
    assert "_draws" not in public_summary(first)


def test_insufficient_independent_clusters():
    data = rows()
    for row in data:
        row["cluster_id"] = "one"
    result = summarize(data, {"a": 1, "b": 1})
    assert result["ci95"] is None
    assert result["standard_error"] is None


def test_paired_exact_shift_and_ties():
    result = compare_paired(rows(10), rows(), {"a": 1, "b": 1})
    assert result["difference"] == 10
    assert result["ci95"] == [10, 10]
    assert result["wins"] == 8
    assert result["standardized_paired_effect"] is None
    tied = compare_paired(rows(), rows(), {"a": 1, "b": 1})
    assert tied["ties"] == 8 and tied["conclusion"] == "inconclusive"


def test_weighted_mean_does_not_pool_unequal_categories():
    data = [dict(task_id="a", category="a", cluster_id="1", score=0)] + [
        dict(task_id=f"b{i}", category="b", cluster_id=str(i), score=100) for i in range(8)
    ]
    assert summarize(data, {"a": 1, "b": 1})["mean"] == 50


@pytest.mark.parametrize(
    "data,weights",
    [
        ([], {"a": 1}),
        (rows(), {"a": 1}),
        (rows(), {"a": 0, "b": 1}),
        (rows() + [rows()[0]], {"a": 1, "b": 1}),
    ],
)
def test_reject_invalid_coverage(data, weights):
    with pytest.raises(ValueError):
        summarize(data, weights)


def test_pairing_rejects_missing_and_changed_group():
    with pytest.raises(ValueError):
        compare_paired(rows(), rows()[:-1], {"a": 1, "b": 1})
    other = rows()
    other[0]["cluster_id"] = "different"
    with pytest.raises(ValueError):
        compare_paired(rows(), other, {"a": 1, "b": 1})
    other = rows()
    other[0]["score"] = float("nan")
    with pytest.raises(ValueError, match="Nonfinite"):
        summarize(other, {"a": 1, "b": 1})
