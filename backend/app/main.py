"""Public, read-first API. Evaluations execute through trusted CLI workers."""

import hmac
import os
import time
from collections import defaultdict, deque
from collections.abc import Generator
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from chemagent.database.models import (
    Agent,
    BenchmarkTask,
    BenchmarkVersion,
    EvaluationRun,
    LeaderboardSnapshot,
    Model,
    Submission,
)
from chemagent.database.queries import comparison, leaderboard, run_detail
from chemagent.database.session import make_engine, sessions


class SubmissionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["model", "agent", "benchmark", "evaluation"]
    name: str = Field(min_length=2, max_length=120)
    organization: str = Field(min_length=2, max_length=200)
    version: str = Field(min_length=1, max_length=60)
    description: str = Field(min_length=10, max_length=4000)
    repository: HttpUrl | None = None
    paper: HttpUrl | None = None
    DOI: str | None = Field(default=None, max_length=200)
    license: str = Field(min_length=2, max_length=100)
    model_access_method: str = Field(min_length=2, max_length=200)


def create_app(url: str | None = None) -> FastAPI:
    engine = make_engine(url)
    factory = sessions(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
        yield
        engine.dispose()

    app = FastAPI(
        title="ChemAgent Index API",
        version="0.1.0",
        lifespan=lifespan,
        description="Research preview. Public synthetic demonstration results only; no real-model ranking claims.",
    )
    app.state.engine = engine
    requests: dict[str, deque[float]] = defaultdict(deque)

    def db() -> Generator[Session, None, None]:
        with factory() as session:
            yield session

    @app.middleware("http")
    async def limits(request: Request, call_next: Any) -> Any:
        try:
            content_length = int(request.headers.get("content-length", "0") or "0")
        except ValueError:
            return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
        if content_length > 32000:
            return JSONResponse({"detail": "Request too large"}, status_code=413)
        if request.url.path != "/health":
            current = time.monotonic()
            key = request.client.host if request.client else "unknown"
            if len(requests) > 10000:
                for old_key in list(requests):
                    if not requests[old_key] or requests[old_key][-1] < current - 60:
                        del requests[old_key]
                if len(requests) > 10000:
                    return JSONResponse({"detail": "Server busy"}, status_code=429)
            bucket = requests[key]
            while bucket and bucket[0] < current - 60:
                bucket.popleft()
            if len(bucket) >= 120:
                return JSONResponse(
                    {"detail": "Rate limit exceeded"},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
            bucket.append(current)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        return JSONResponse(
            {"detail": "Database unavailable; check migrations and service health"}, status_code=503
        )

    @app.get("/health")
    def health(session: Session = Depends(db)) -> dict[str, str]:
        session.execute(text("SELECT 1"))
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/api/v1/leaderboard")
    def ranking(
        cohort: str | None = Query(default=None, max_length=64), session: Session = Depends(db)
    ) -> dict[str, Any]:
        return leaderboard(session, cohort)

    @app.get("/api/v1/models")
    def models(session: Session = Depends(db)) -> list[dict[str, Any]]:
        return [m.data for m in session.scalars(select(Model))]

    @app.get("/api/v1/agents")
    def agents(session: Session = Depends(db)) -> list[dict[str, Any]]:
        return [a.data for a in session.scalars(select(Agent))]

    @app.get("/api/v1/models/{model_id}")
    def model(model_id: str, session: Session = Depends(db)) -> dict[str, Any]:
        record = session.get(Model, model_id)
        if record is None:
            raise HTTPException(404, "Model not found")
        runs = list(
            session.scalars(
                select(EvaluationRun)
                .where(EvaluationRun.model_id == model_id)
                .order_by(EvaluationRun.created_at.desc())
            )
        )
        return {
            "model": record.data,
            "runs": [
                {
                    "id": r.id,
                    "status": r.status,
                    "cohort": r.cohort,
                    "benchmark_version_id": r.version_id,
                    "created_at": r.created_at,
                    "summary": r.summary,
                }
                for r in runs
                if r.provenance["visibility"] == "public"
            ],
        }

    @app.get("/api/v1/benchmarks")
    def benchmarks(session: Session = Depends(db)) -> list[dict[str, Any]]:
        return [
            {"id": b.id, "fingerprint": b.fingerprint, **b.data}
            for b in session.scalars(select(BenchmarkVersion))
        ]

    @app.get("/api/v1/benchmarks/{version_id}")
    def benchmark(version_id: str, session: Session = Depends(db)) -> dict[str, Any]:
        record = session.get(BenchmarkVersion, version_id)
        if record is None:
            raise HTTPException(404, "Benchmark version not found")
        public = [
            t.data
            for t in session.scalars(
                select(BenchmarkTask).where(BenchmarkTask.version_id == version_id)
            )
            if t.data.get("visibility") == "public"
        ]
        return {
            "id": record.id,
            "fingerprint": record.fingerprint,
            "manifest": record.data,
            "public_tasks": public,
        }

    @app.get("/api/v1/evaluations/{run_id}")
    def evaluation(run_id: str, session: Session = Depends(db)) -> dict[str, Any]:
        result = run_detail(session, run_id)
        if result is None:
            raise HTTPException(404, "Public evaluation not found")
        return result

    @app.get("/api/v1/compare")
    def compare(left: str, right: str, session: Session = Depends(db)) -> dict[str, Any]:
        try:
            return comparison(session, left, right)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/api/v1/snapshots/{snapshot_id}")
    def snapshot(snapshot_id: str, session: Session = Depends(db)) -> dict[str, Any]:
        record = session.get(LeaderboardSnapshot, snapshot_id)
        if record is None:
            raise HTTPException(404, "Snapshot not found")
        return {
            "id": record.id,
            "created_at": record.created_at,
            "sha256": record.fingerprint,
            "data": record.data,
        }

    @app.post("/api/v1/submissions", status_code=201)
    def submit(
        payload: SubmissionInput,
        authorization: str | None = Header(default=None),
        session: Session = Depends(db),
    ) -> dict[str, str]:
        token = os.environ.get("SUBMISSION_TOKEN")
        if not token:
            raise HTTPException(503, "Submission intake is not enabled in this research preview")
        if authorization is None or not hmac.compare_digest(authorization, f"Bearer {token}"):
            raise HTTPException(401, "Valid operator-issued submission token required")
        record = Submission(data=payload.model_dump(mode="json"))
        session.add(record)
        session.commit()
        return {"id": record.id, "status": record.status}

    return app


app = create_app()
