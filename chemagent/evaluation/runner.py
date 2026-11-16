"""Checkpointed evaluations with recorded scientific and software identity."""

import importlib.metadata
import json
import logging
import platform
import subprocess
import time
from dataclasses import asdict
from typing import Any

from sqlalchemy import Engine, select

from chemagent.benchmarks.store import TaskStore, public_store
from chemagent.config import ROOT, EvaluationConfig, digest, load_policy
from chemagent.database.models import (
    AuditLog,
    Citation,
    Evaluation,
    EvaluationRun,
    Response,
    Score,
    ValidationResult,
    now,
    uid,
)
from chemagent.database.registry import register
from chemagent.database.session import sessions
from chemagent.evaluation.locking import run_lock
from chemagent.providers.base import BaseModelAdapter, PublicRequest
from chemagent.providers.mock import MockAdapter
from chemagent.scoring.engine import score_task
from chemagent.statistics.bootstrap import public_summary, summarize

logger = logging.getLogger("chemagent")


def environment() -> dict[str, Any]:
    try:
        commit = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, timeout=3
            )
            .decode()
            .strip()
        )
    except (OSError, subprocess.SubprocessError):
        commit = None
    packages = {
        name: importlib.metadata.version(name)
        for name in ["rdkit", "numpy", "pydantic", "sqlalchemy", "fastapi", "alembic"]
    }
    code = {
        str(p.relative_to(ROOT)): p.read_text() for p in sorted((ROOT / "chemagent").rglob("*.py"))
    }
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dependencies": packages,
        "git_commit": commit,
        "code_sha256": digest(code),
    }


def emit(session: Any, event: str, **data: Any) -> None:
    logger.info(json.dumps({"event": event, **data}))
    session.add(AuditLog(event=event, data=data))


def run_evaluation(
    engine: Engine,
    config: EvaluationConfig,
    *,
    adapter: BaseModelAdapter | None = None,
    store: TaskStore | None = None,
    resume: str | None = None,
) -> str:
    adapter = adapter or MockAdapter(config.model)
    metadata = adapter.metadata()
    if metadata.get("model_id") != config.model:
        raise ValueError("Adapter/model registry mismatch")
    if not set(metadata.get("required_tools", [])).issubset(config.tools):
        raise ValueError("Adapter requires unpermitted tools")
    manifest, tasks, benchmark_hash = (store or public_store(config.benchmark)).load()
    if metadata.get("demo") and any(t.visibility == "private" for t in tasks):
        raise ValueError("Mock evaluation is public-development-only")
    policy = load_policy()
    env = environment()
    cohort_config = config.model_dump(exclude={"model"})
    cohort = digest(
        {
            "benchmark": benchmark_hash,
            "policy": policy,
            "config": cohort_config,
            "code": env["code_sha256"],
            "dependencies": env["dependencies"],
            "python": env["python"],
            "demo": metadata.get("demo", False),
        }
    )
    identity = digest({"cohort": cohort, "adapter": metadata})
    run_id = resume or uid()
    factory = sessions(engine)
    with run_lock(engine, run_id), factory() as session:
        version_id = register(session, manifest, tasks, benchmark_hash)
        if resume:
            run = session.get(EvaluationRun, resume)
            if run is None or run.status == "completed" or run.identity != identity:
                raise ValueError("Cannot resume: missing, finished, or changed run inputs")
            run.status = "running"
        else:
            campaign = Evaluation(model_id=config.model, version_id=version_id)
            session.add(campaign)
            session.flush()
            run = EvaluationRun(
                id=run_id,
                evaluation_id=campaign.id,
                model_id=config.model,
                version_id=version_id,
                cohort=cohort,
                identity=identity,
                status="running",
                provenance={
                    "config": config.model_dump(),
                    "provider": metadata,
                    "environment": env,
                    "benchmark_hash": benchmark_hash,
                    "scoring_hash": digest(policy),
                    "policy": policy,
                    "visibility": "public"
                    if all(t.visibility == "public" for t in tasks)
                    else "private",
                },
            )
            session.add(run)
        emit(session, "evaluation_started", run_id=run_id, resume=bool(resume))
        session.commit()
        completed = {
            r.task_id for r in session.scalars(select(Response).where(Response.run_id == run_id))
        }
        try:
            for task in tasks:
                if task.task_id in completed:
                    continue
                emit(session, "task_started", run_id=run_id, task_id=task.task_id)
                result = None
                start = time.perf_counter()
                for attempt in range(config.retries + 1):
                    try:
                        result = adapter.generate_structured(
                            PublicRequest.from_task(task), seed=config.seed, timeout=config.timeout
                        )
                        if not set(result.tool_calls).issubset(config.tools):
                            raise ValueError("Provider used unpermitted tools")
                        break
                    except (TimeoutError, ConnectionError):
                        if attempt == config.retries:
                            raise
                        time.sleep(min(0.1 * 2**attempt, 1))
                if result is None:
                    raise RuntimeError("Provider returned no result")
                elapsed = time.perf_counter() - start
                score = score_task(task, result.text, policy["reliability"])
                response = Response(
                    run_id=run_id,
                    task_id=task.task_id,
                    raw=result.text,
                    data={
                        **{k: v for k, v in asdict(result).items() if k != "text"},
                        "wall_seconds": elapsed,
                        "response_hash": digest(result.text),
                        "attempts": attempt + 1,
                    },
                )
                session.add(response)
                session.flush()
                row = {
                    "task_id": task.task_id,
                    "category": task.category,
                    "cluster_id": task.cluster_id,
                    **{
                        k: score[k]
                        for k in [
                            "score",
                            "cri",
                            "reproducibility",
                            "error_rate",
                            "calibration_error",
                        ]
                    },
                }
                session.add(Score(id=response.id, data=row))
                session.add(ValidationResult(id=response.id, data=score))
                for citation in score["citations"]:
                    session.add(Citation(response_id=response.id, data=citation))
                for event in ["provider_response", "validation_completed", "score_computed"]:
                    emit(session, event, run_id=run_id, task_id=task.task_id)
                session.commit()
            rows = list(
                session.scalars(
                    select(Score)
                    .join(Response, Score.id == Response.id)
                    .where(Response.run_id == run_id)
                )
            )
            stats = {
                metric: public_summary(
                    summarize(
                        [r.data for r in rows],
                        policy["weights"],
                        seed=config.seed,
                        resamples=policy["bootstrap_resamples"],
                        metric=metric,
                    )
                )
                for metric in ["score", "cri", "reproducibility"]
            }
            responses = list(session.scalars(select(Response).where(Response.run_id == run_id)))
            costs = [r.data["cost_usd"] for r in responses]
            cost = sum(costs) if all(c is not None for c in costs) else None
            stats["usage"] = {
                "cost_usd": cost,
                "wall_seconds": sum(r.data["wall_seconds"] for r in responses),
                "input_tokens": sum(r.data["input_tokens"] for r in responses)
                if all(r.data["input_tokens"] is not None for r in responses)
                else None,
                "output_tokens": sum(r.data["output_tokens"] for r in responses)
                if all(r.data["output_tokens"] is not None for r in responses)
                else None,
                "performance_per_dollar": stats["score"]["mean"] / cost
                if cost is not None and cost > 0
                else None,
                "tool_calls": sum(len(r.data["tool_calls"]) for r in responses),
            }
            run.summary = stats
            run.status = "completed"
            run.completed_at = now()
            emit(session, "evaluation_completed", run_id=run_id)
            session.commit()
        except BaseException as exc:
            session.rollback()
            run = session.get(EvaluationRun, run_id)
            if run is not None:
                run.status = "partial"
                emit(session, "evaluation_failed", run_id=run_id, error_type=type(exc).__name__)
                session.commit()
            raise
    return run_id
