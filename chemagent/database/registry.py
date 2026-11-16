"""Idempotent registry ingestion with immutable version fingerprints."""

from typing import Any

from sqlalchemy.orm import Session

from chemagent.benchmarks.schema import Task
from chemagent.database.models import Agent, Benchmark, BenchmarkTask, BenchmarkVersion, Model
from chemagent.providers.mock import DEMOS


def register(
    session: Session, manifest: dict[str, Any], tasks: list[Task], fingerprint: str
) -> str:
    benchmark_id = manifest["benchmark_id"]
    version_id = f"{benchmark_id}:{manifest['benchmark_version']}:{fingerprint[:12]}"
    if session.get(Benchmark, benchmark_id) is None:
        session.add(Benchmark(id=benchmark_id, name=manifest["benchmark_name"]))
        session.flush()
    if session.get(BenchmarkVersion, version_id) is None:
        session.add(
            BenchmarkVersion(
                id=version_id,
                benchmark_id=benchmark_id,
                version=manifest["benchmark_version"],
                fingerprint=fingerprint,
                data=manifest,
            )
        )
        session.flush()
        for task in tasks:
            data = (
                task.model_dump(mode="json")
                if task.visibility == "public"
                else {"task_id": task.task_id, "category": task.category, "visibility": "private"}
            )
            session.add(
                BenchmarkTask(
                    id=f"{version_id}:{task.task_id}",
                    version_id=version_id,
                    task_id=task.task_id,
                    data=data,
                )
            )
    for model_id, (name, _) in DEMOS.items():
        if session.get(Model, model_id) is None:
            session.add(
                Model(
                    id=model_id,
                    data={
                        "model_id": model_id,
                        "display_name": name,
                        "organization": "ChemAgent Index demonstration fixtures",
                        "provider": "mock",
                        "model_version": "0.1.0",
                        "release_date": "2026-11-16",
                        "access_type": "local",
                        "open_source": True,
                        "commercial": False,
                        "parameter_count": None,
                        "context_window": None,
                        "tool_support": True,
                        "vision_support": False,
                        "code_execution_support": False,
                        "internet_support": False,
                        "API_available": False,
                        "estimated_cost": 0,
                        "evaluation_date": None,
                        "demo": True,
                        "system_type": "rule_solver",
                    },
                )
            )
    session.flush()
    if session.get(Agent, "demo-rule-agent") is None:
        session.add(
            Agent(
                id="demo-rule-agent",
                base_model_id="demo-agent",
                data={
                    "agent_id": "demo-rule-agent",
                    "agent_name": "Demo rule workflow",
                    "developer": "ChemAgent Index maintainers",
                    "version": "0.1.0",
                    "base_model": "demo-agent",
                    "tool_stack": ["RDKit"],
                    "retrieval_enabled": False,
                    "code_execution": False,
                    "cheminformatics_tools": ["RDKit"],
                    "literature_tools": [],
                    "database_access": [],
                    "memory": False,
                    "workflow_type": "deterministic",
                    "open_source": True,
                    "repository": None,
                    "license": "MIT",
                    "demo": True,
                },
            )
        )
    session.commit()
    return version_id
