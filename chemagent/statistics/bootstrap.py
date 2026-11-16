"""Seeded cluster bootstrap with explicit paired-cohort checks."""

from collections import defaultdict
from typing import Any

import numpy as np


def _draws(
    rows: list[dict[str, Any]], metric: str, resamples: int, rng: np.random.Generator
) -> tuple[np.ndarray, int]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        value = float(row[metric])
        if not np.isfinite(value):
            raise ValueError("Nonfinite score")
        groups[row["cluster_id"]].append(value)
    values = list(groups.values())
    sums = np.array([sum(v) for v in values])
    counts = np.array([len(v) for v in values])
    indices = rng.integers(0, len(values), size=(resamples, len(values)))
    return sums[indices].sum(axis=1) / counts[indices].sum(axis=1), len(values)


def summarize(
    rows: list[dict[str, Any]],
    weights: dict[str, float],
    *,
    seed: int = 2026,
    resamples: int = 2000,
    metric: str = "score",
) -> dict[str, Any]:
    if not rows or resamples < 100 or any(w <= 0 for w in weights.values()):
        raise ValueError("Need scores, positive weights and at least 100 resamples")
    if {r["category"] for r in rows} != set(weights):
        raise ValueError("Category coverage does not match the preregistered profile")
    if len({r["task_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate paired task IDs")
    rng = np.random.default_rng(seed)
    categories = {}
    draws = np.zeros(resamples)
    overall = 0.0
    adequate = True
    for category, weight in weights.items():
        selected = [r for r in rows if r["category"] == category]
        vals = np.array([float(r[metric]) for r in selected])
        samples, clusters = _draws(selected, metric, resamples, rng)
        sufficient = clusters >= 2
        adequate &= sufficient
        ci = np.quantile(samples, [0.025, 0.975]).tolist() if sufficient else None
        mean = float(vals.mean())
        categories[category] = {
            "mean": mean,
            "ci95": ci,
            "standard_error": float(samples.std(ddof=1)) if sufficient else None,
            "sample_variance": float(vals.var(ddof=1)) if len(vals) > 1 else None,
            "n": len(vals),
            "clusters": clusters,
        }
        proportion = weight / sum(weights.values())
        overall += mean * proportion
        draws += samples * proportion
    return {
        "mean": overall,
        "ci95": np.quantile(draws, [0.025, 0.975]).tolist() if adequate else None,
        "standard_error": float(draws.std(ddof=1)) if adequate else None,
        "categories": categories,
        "n": len(rows),
        "bootstrap_resamples": resamples,
        "seed": seed,
        "method": "category-stratified cluster percentile bootstrap",
        "_draws": draws.tolist(),
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in result.items() if k != "_draws"}


def compare_paired(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
    weights: dict[str, float],
    *,
    seed: int = 2026,
    resamples: int = 2000,
) -> dict[str, Any]:
    indexed = {r["task_id"]: r for r in right}
    if len(indexed) != len(right) or {r["task_id"] for r in left} != set(indexed):
        raise ValueError("Comparison requires identical complete task pairs")
    differences = []
    for row in left:
        other = indexed[row["task_id"]]
        if (row["category"], row["cluster_id"]) != (other["category"], other["cluster_id"]):
            raise ValueError("Task group mismatch")
        differences.append({**row, "score": row["score"] - other["score"]})
    stats = summarize(differences, weights, seed=seed, resamples=resamples)
    delta = np.array([r["score"] for r in differences])
    draws = np.array(stats.pop("_draws"))
    ci = stats["ci95"]
    return {
        "difference": stats["mean"],
        "ci95": ci,
        "standard_error": stats["standard_error"],
        "standardized_paired_effect": float(delta.mean() / delta.std(ddof=1))
        if len(delta) > 1 and delta.std(ddof=1) > 0
        else None,
        "wins": int((delta > 1e-9).sum()),
        "losses": int((delta < -1e-9).sum()),
        "ties": int((abs(delta) <= 1e-9).sum()),
        "bootstrap_probability_left_better": float((draws > 0).mean()),
        "conclusion": "inconclusive"
        if ci is None or ci[0] <= 0 <= ci[1]
        else "difference_detected",
        "note": "Exploratory paired interval; no multiplicity correction. Synthetic demo only.",
    }
