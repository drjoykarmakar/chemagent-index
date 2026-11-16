"""Relational identities and immutable scientific artifacts."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def uid() -> str:
    return str(uuid4())


def now() -> str:
    return datetime.now(UTC).isoformat()


class Base(DeclarativeBase):
    pass


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(200))


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"))
    role: Mapped[str] = mapped_column(String(30), default="researcher")
    external_subject: Mapped[str] = mapped_column(String(200), unique=True)


class Model(Base):
    __tablename__ = "models"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    base_model_id: Mapped[str | None] = mapped_column(ForeignKey("models.id"))
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class Benchmark(Base):
    __tablename__ = "benchmarks"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))


class BenchmarkVersion(Base):
    __tablename__ = "benchmark_versions"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    benchmark_id: Mapped[str] = mapped_column(ForeignKey("benchmarks.id"))
    version: Mapped[str] = mapped_column(String(30))
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class BenchmarkTask(Base):
    __tablename__ = "benchmark_tasks"
    __table_args__ = (UniqueConstraint("version_id", "task_id"),)
    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("benchmark_versions.id"))
    task_id: Mapped[str] = mapped_column(String(100))
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class Evaluation(Base):
    __tablename__ = "evaluations"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"))
    version_id: Mapped[str] = mapped_column(ForeignKey("benchmark_versions.id"))


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    evaluation_id: Mapped[str] = mapped_column(ForeignKey("evaluations.id"))
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"), index=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("benchmark_versions.id"))
    status: Mapped[str] = mapped_column(String(30), default="running")
    cohort: Mapped[str] = mapped_column(String(64), index=True)
    identity: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    completed_at: Mapped[str | None] = mapped_column(String(40))
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON)
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Response(Base):
    __tablename__ = "responses"
    __table_args__ = (UniqueConstraint("run_id", "task_id"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id"), index=True)
    task_id: Mapped[str] = mapped_column(String(100))
    raw: Mapped[str] = mapped_column(String)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class Score(Base):
    __tablename__ = "scores"
    id: Mapped[str] = mapped_column(ForeignKey("responses.id"), primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class ValidationResult(Base):
    __tablename__ = "validation_results"
    id: Mapped[str] = mapped_column(ForeignKey("responses.id"), primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class Citation(Base):
    __tablename__ = "citations"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    response_id: Mapped[str] = mapped_column(ForeignKey("responses.id"))
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class LeaderboardSnapshot(Base):
    __tablename__ = "leaderboard_snapshots"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    cohort: Mapped[str] = mapped_column(String(64))
    fingerprint: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    status: Mapped[str] = mapped_column(String(30), default="submitted")
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class APIKey(Base):
    __tablename__ = "api_keys"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    key_hash: Mapped[str] = mapped_column(String(128))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    event: Mapped[str] = mapped_column(String(80))
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
