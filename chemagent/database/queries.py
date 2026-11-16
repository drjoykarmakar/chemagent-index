"""Public projections and strict comparison cohorts."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from chemagent.config import digest
from chemagent.database.models import (
    EvaluationRun,
    LeaderboardSnapshot,
    Model,
    Response,
    Score,
    ValidationResult,
)
from chemagent.statistics.bootstrap import compare_paired

DEMO_NOTICE = "DEMONSTRATION DATA — NOT REAL BENCHMARK RESULTS"
REAL_NOTICE = "EXPERIMENTAL MODEL RESULTS — PUBLIC SYNTHETIC DEVELOPMENT SET"


def result_notice(provenance: dict[str, Any]) -> str:
    if provenance.get("scope") == "smoke":
        return "SMOKE TEST — INCOMPLETE BENCHMARK COVERAGE; NOT RANKED"
    return DEMO_NOTICE if provenance["provider"].get("demo") else REAL_NOTICE


def leaderboard(session: Session, cohort: str | None = None) -> dict[str, Any]:
    runs = list(
        session.scalars(
            select(EvaluationRun)
            .where(EvaluationRun.status == "completed")
            .order_by(EvaluationRun.completed_at.desc())
        )
    )
    runs = [
        r
        for r in runs
        if r.provenance["visibility"] == "public" and r.provenance.get("rank_eligible", True)
    ]
    cohorts = list(dict.fromkeys(r.cohort for r in runs))
    selected = cohort or (cohorts[0] if cohorts else None)
    seen: set[str] = set()
    rows = []
    for run in runs:
        if run.cohort != selected or run.model_id in seen:
            continue
        seen.add(run.model_id)
        model = session.get(Model, run.model_id)
        assert model is not None
        rows.append(
            {
                "model": model.data,
                "run_id": run.id,
                "benchmark_version_id": run.version_id,
                "evaluated_at": run.completed_at,
                "summary": run.summary,
                "track": run.provenance["config"]["track"],
                "cohort": run.cohort,
            }
        )
    rows.sort(key=lambda r: r["summary"]["score"]["mean"], reverse=True)
    return {
        "notice": result_notice(next(r.provenance for r in runs if r.cohort == selected))
        if rows
        else "No completed evaluations in this cohort",
        "profile": "ChemAgentBench starter index",
        "cohort": selected,
        "available_cohorts": cohorts,
        "rows": rows,
        "ranking_note": "Order is descriptive; inspect paired intervals before interpreting differences.",
    }


def run_detail(session: Session, run_id: str) -> dict[str, Any] | None:
    run = session.get(EvaluationRun, run_id)
    if run is None or run.provenance["visibility"] != "public":
        return None
    rows = []
    for response in session.scalars(
        select(Response).where(Response.run_id == run_id).order_by(Response.task_id)
    ):
        score = session.get(Score, response.id)
        validation = session.get(ValidationResult, response.id)
        rows.append(
            {
                "task_id": response.task_id,
                "response": response.raw,
                "usage": response.data,
                "score": score.data if score else None,
                "validation": validation.data if validation else None,
            }
        )
    return {
        "id": run.id,
        "model_id": run.model_id,
        "status": run.status,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
        "cohort": run.cohort,
        "provenance": run.provenance,
        "summary": run.summary,
        "tasks": rows,
        "notice": result_notice(run.provenance),
    }


def comparison(session: Session, left_id: str, right_id: str) -> dict[str, Any]:
    left, right = session.get(EvaluationRun, left_id), session.get(EvaluationRun, right_id)
    if left is None or right is None or left.status != "completed" or right.status != "completed":
        raise ValueError("Two completed runs are required")
    if not all(r.provenance.get("rank_eligible", True) for r in [left, right]):
        raise ValueError("Smoke runs cannot be compared as full benchmark evaluations")
    if left.cohort != right.cohort or any(
        r.provenance["visibility"] != "public" for r in [left, right]
    ):
        raise ValueError("Incompatible benchmark, scoring, tools, environment or configuration")

    def rows(run_id: str) -> list[dict[str, Any]]:
        return [
            s.data
            for s in session.scalars(
                select(Score)
                .join(Response, Score.id == Response.id)
                .where(Response.run_id == run_id)
            )
        ]

    policy = left.provenance["policy"]
    return compare_paired(
        rows(left_id),
        rows(right_id),
        policy["weights"],
        seed=left.provenance["config"]["seed"],
        resamples=policy["bootstrap_resamples"],
    )


def snapshot(session: Session, cohort: str | None = None) -> str:
    data = leaderboard(session, cohort)
    if not data["rows"]:
        raise ValueError("Cannot snapshot an empty cohort")
    record = LeaderboardSnapshot(cohort=data["cohort"], fingerprint=digest(data), data=data)
    session.add(record)
    session.commit()
    return record.id
