from fastapi.testclient import TestClient

from backend.app.main import create_app
from chemagent.config import EvaluationConfig
from chemagent.database.models import EvaluationRun
from chemagent.database.session import sessions
from chemagent.evaluation.runner import run_evaluation


def test_read_api_and_private_isolation(engine, migrated_url):
    run_id = run_evaluation(engine, EvaluationConfig())
    with TestClient(create_app(migrated_url)) as client:
        assert client.get("/health").json()["status"] == "ok"
        assert client.get("/api/v1/models").status_code == 200
        assert len(client.get("/api/v1/agents").json()) == 1
        assert client.get("/api/v1/models/demo-agent").json()["runs"][0]["id"] == run_id
        assert client.get("/api/v1/models/missing").status_code == 404
        bench = client.get("/api/v1/benchmarks").json()[0]
        assert len(client.get("/api/v1/benchmarks/" + bench["id"]).json()["public_tasks"]) == 60
        assert client.get("/api/v1/benchmarks/missing").status_code == 404
        assert len(client.get("/api/v1/evaluations/" + run_id).json()["tasks"]) == 60
        assert client.get("/api/v1/evaluations/missing").status_code == 404
        assert client.get("/api/v1/compare?left=missing&right=missing").status_code == 409
        assert client.get("/api/v1/snapshots/missing").status_code == 404
        assert client.get("/openapi.json").status_code == 200
        with sessions(engine)() as session:
            run = session.get(EvaluationRun, run_id)
            run.provenance = {**run.provenance, "visibility": "private"}
            session.commit()
        assert client.get("/api/v1/evaluations/" + run_id).status_code == 404
        assert client.get("/api/v1/leaderboard").json()["rows"] == []
        assert client.get("/api/v1/models/demo-agent").json()["runs"] == []


def test_submission_is_disabled_and_token_protected(migrated_url, monkeypatch):
    payload = {
        "kind": "agent",
        "name": "Example",
        "organization": "Research Lab",
        "version": "1.0.0",
        "description": "A structured test submission.",
        "license": "Apache-2.0",
        "model_access_method": "local",
    }
    monkeypatch.delenv("SUBMISSION_TOKEN", raising=False)
    with TestClient(create_app(migrated_url)) as client:
        assert client.post("/api/v1/submissions", json=payload).status_code == 503
        assert client.post("/api/v1/submissions", json={}).status_code == 422
        monkeypatch.setenv("SUBMISSION_TOKEN", "test-token-123")
        assert client.post("/api/v1/submissions", json=payload).status_code == 401
        accepted = client.post(
            "/api/v1/submissions", json=payload, headers={"Authorization": "Bearer test-token-123"}
        )
        assert accepted.status_code == 201 and accepted.json()["status"] == "submitted"
        assert client.post("/api/v1/submissions", content="x" * 32001).status_code == 413
        assert client.get("/api/v1/models", headers={"content-length": "bad"}).status_code == 400


def test_rate_limits(migrated_url):
    with TestClient(create_app(migrated_url)) as client:
        for _ in range(120):
            assert client.get("/api/v1/models").status_code == 200
        assert client.get("/api/v1/models").status_code == 429
        assert client.get("/health").status_code == 200
