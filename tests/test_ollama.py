import hashlib
import io
import json
import zipfile

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select
from typer.testing import CliRunner

from backend.app.main import create_app
from chemagent.cli import app
from chemagent.config import EvaluationConfig, load_config
from chemagent.database.models import BenchmarkTask, EvaluationRun, Response
from chemagent.database.queries import comparison, leaderboard, run_detail
from chemagent.database.session import sessions
from chemagent.evaluation.export import export_zip
from chemagent.evaluation.runner import run_evaluation
from chemagent.providers.base import PublicRequest
from chemagent.providers.ollama import OllamaAdapter

DIGEST = "a" * 64


def settings(**kwargs):
    return EvaluationConfig.model_validate(
        {
            "model": "contract-test-model",
            "provider": "ollama",
            "ollama_digest": DIGEST,
            "tools": [],
            "track": "model_only",
            "max_tokens": 128,
            **kwargs,
        }
    )


def adapter_for(config, handler=None):
    calls = []

    def transport(request):
        calls.append(request)
        if request.url.path == "/api/tags":
            return httpx.Response(
                200, json={"models": [{"name": "qwen2.5:0.5b", "digest": DIGEST}]}
            )
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "contract-fixture"})
        if handler:
            return handler(request)
        return httpx.Response(
            200,
            json={
                "done": True,
                "response": "{invalid-model-json",
                "prompt_eval_count": 120,
                "eval_count": 12,
                "done_reason": "length",
            },
        )

    return OllamaAdapter(
        config,
        client=httpx.Client(
            base_url="http://ollama.test", transport=httpx.MockTransport(transport)
        ),
    ), calls


def test_structured_contract_has_no_references(dataset):
    config = settings(temperature=0.2, context_window=8192, cpu_threads=3)
    adapter, calls = adapter_for(config)
    try:
        assert adapter.health_check()
        request = PublicRequest.from_task(dataset[1][0])
        response = adapter.generate_structured(request, seed=42, timeout=4)
        payload = json.loads(calls[-1].content)
        prompt = json.loads(payload["prompt"])
        assert set(prompt) == {"task", "inputs", "output_schema"}
        assert prompt["inputs"] == request.inputs
        assert "reference_answer" not in payload["prompt"] and "rubric" not in payload["prompt"]
        assert payload["format"] == request.output_schema and payload["stream"] is False
        assert payload["options"] == {
            "seed": 42,
            "temperature": 0.2,
            "num_predict": 128,
            "num_ctx": 8192,
            "num_thread": 3,
        }
        assert calls[-1].extensions["timeout"]["read"] == 4
        assert response.text == "{invalid-model-json" and response.finish_reason == "length"
        assert response.input_tokens == 120 and response.output_tokens == 12
        assert response.cost_usd is None and response.tool_calls == []
        assert adapter.metadata()["model_version"] == DIGEST
    finally:
        adapter.close()


@pytest.mark.parametrize("kind", ["missing", "changed"])
def test_missing_or_changed_model_fails_closed(kind, dataset):
    def handler(request):
        return httpx.Response(
            200,
            json={
                "models": []
                if kind == "missing"
                else [{"name": "qwen2.5:0.5b", "digest": "b" * 64}]
            },
        )

    adapter = OllamaAdapter(
        settings(),
        client=httpx.Client(base_url="http://ollama.test", transport=httpx.MockTransport(handler)),
    )
    assert not adapter.health_check()
    with pytest.raises(ValueError):
        adapter.generate(PublicRequest.from_task(dataset[1][0]), seed=1, timeout=1)
    adapter.close()


def test_digest_rechecked_after_metadata(dataset):
    adapter, _ = adapter_for(settings())
    adapter.metadata()
    adapter.client.close()
    adapter.client = httpx.Client(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, json={"models": [{"name": "qwen2.5:0.5b", "digest": "b" * 64}]}
            )
        ),
    )
    with pytest.raises(ValueError, match="digest"):
        adapter.generate(PublicRequest.from_task(dataset[1][0]), seed=1, timeout=1)
    adapter.close()


def test_smoke_exports_no_aggregate_and_registers_entire_benchmark(engine, migrated_url):
    config = settings(sample_size=5)
    adapter, _ = adapter_for(config)
    run_id = run_evaluation(engine, config, adapter=adapter)
    adapter.close()
    with sessions(engine)() as session:
        detail = run_detail(session, run_id)
        assert detail["status"] == "completed" and len(detail["tasks"]) == 5
        assert detail["summary"]["score"] is None and not detail["summary"]["rank_eligible"]
        assert len({t["score"]["category"] for t in detail["tasks"]}) == 5
        assert not leaderboard(session)["rows"]
        assert session.scalar(select(func.count()).select_from(BenchmarkTask)) == 60
        with pytest.raises(ValueError, match="Smoke"):
            comparison(session, run_id, run_id)
        data = export_zip(session, run_id)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["task_count"] == 5 and manifest["status"] == "completed"
        for name, fingerprint in manifest["sha256"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == fingerprint
        raw = [json.loads(line) for line in archive.read("responses.jsonl").splitlines()]
        assert all(r["response"] == "{invalid-model-json" for r in raw)
        assert len(archive.read("scores.csv").splitlines()) == 6
    with TestClient(create_app(migrated_url)) as client:
        assert client.get(f"/api/v1/evaluations/{run_id}/download").status_code == 200
        assert client.get("/api/v1/evaluations").json()[0]["scope"] == "smoke"
    with sessions(engine)() as session:
        run = session.get(EvaluationRun, run_id)
        run.provenance = {**run.provenance, "visibility": "private"}
        session.commit()
        with pytest.raises(ValueError, match="Public"):
            export_zip(session, run_id)
    with TestClient(create_app(migrated_url)) as client:
        assert client.get(f"/api/v1/evaluations/{run_id}/download").status_code == 404
        assert client.get("/api/v1/evaluations").json() == []


def test_full_contract_run_label_and_smoke_identity(engine):
    config = settings()
    adapter, _ = adapter_for(config)
    full = run_evaluation(engine, config, adapter=adapter)
    adapter.close()
    with sessions(engine)() as session:
        board = leaderboard(session)
        assert len(board["rows"]) == 1 and "EXPERIMENTAL MODEL" in board["notice"]
        assert board["rows"][0]["summary"]["score"]["mean"] == 0
        assert board["rows"][0]["summary"]["usage"]["cost_usd"] is None
    sample = settings(sample_size=60)
    adapter, _ = adapter_for(sample)
    sample_id = run_evaluation(engine, sample, adapter=adapter)
    adapter.close()
    with sessions(engine)() as session:
        assert leaderboard(session)["rows"][0]["run_id"] == full
        assert run_detail(session, sample_id)["summary"]["score"] is None
        assert run_detail(session, sample_id)["cohort"] != run_detail(session, full)["cohort"]


def test_timeout_checkpoint_resume_and_runtime_identity(engine):
    count = 0

    def handler(request):
        nonlocal count
        count += 1
        if count == 2:
            raise httpx.ReadTimeout("contract interruption", request=request)
        return httpx.Response(200, json={"done": True, "response": "{}"})

    config = settings(sample_size=5, retries=0)
    adapter, _ = adapter_for(config, handler)
    with pytest.raises(TimeoutError):
        run_evaluation(engine, config, adapter=adapter)
    with sessions(engine)() as session:
        run = session.scalar(select(EvaluationRun))
        run_id = run.id
        assert run.status == "partial"
        first = session.scalar(select(Response)).id
        assert len(run_detail(session, run_id)["tasks"]) == 1
        with zipfile.ZipFile(io.BytesIO(export_zip(session, run_id))) as archive:
            assert json.loads(archive.read("manifest.json"))["status"] == "partial"
    original = adapter._metadata.copy()
    adapter._metadata["protocol"] = {"name": "ollama-structured-v1", "runtime_version": "changed"}
    with pytest.raises(ValueError, match="changed"):
        run_evaluation(engine, config, adapter=adapter, resume=run_id)
    adapter._metadata = original
    run_evaluation(engine, config, adapter=adapter, resume=run_id)
    with sessions(engine)() as session:
        assert session.get(Response, first) is not None
        assert len(run_detail(session, run_id)["tasks"]) == 5
    adapter.close()


@pytest.mark.parametrize("error", [httpx.ConnectError, httpx.ReadTimeout])
def test_transport_retries_are_bounded(engine, error):
    calls = 0

    def fail(request):
        nonlocal calls
        calls += 1
        raise error("transport fixture", request=request)

    config = settings(sample_size=1, retries=1)
    adapter, _ = adapter_for(config, fail)
    with pytest.raises((ConnectionError, TimeoutError)):
        run_evaluation(engine, config, adapter=adapter)
    assert calls == 2
    adapter.close()


def test_config_rejects_missing_identity_and_tools():
    with pytest.raises(ValidationError, match="digest"):
        settings(ollama_digest=None)
    with pytest.raises(ValidationError, match="model_only"):
        settings(tools=["rdkit"], track="model_plus_tools")
    config = load_config(__import__("pathlib").Path("configs/ollama.yaml"))
    assert config.provider == "ollama" and config.model.startswith("qwen2.5")


def test_cli_respects_config_model_and_exports(migrated_url, tmp_path):
    import yaml

    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump(EvaluationConfig(model="demo-b", sample_size=5).model_dump()))
    result = CliRunner().invoke(
        app, ["evaluate", "--config", str(config), "--output-dir", str(tmp_path / "results")]
    )
    assert result.exit_code == 0, result.output
    archives = list((tmp_path / "results").glob("*.zip"))
    assert len(archives) == 1
    with zipfile.ZipFile(archives[0]) as archive:
        assert json.loads(archive.read("run.json"))["model_id"] == "demo-b"
        assert json.loads(archive.read("manifest.json"))["task_count"] == 5


@pytest.mark.parametrize(
    "status,payload",
    [
        (503, {"error": "fixture server failure"}),
        (200, {"done": False, "response": "{}"}),
        (200, {"done": True, "response": 7}),
        (200, {"error": "fixture protocol failure"}),
    ],
)
def test_protocol_failures_do_not_become_ranked_runs(engine, status, payload):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(status, json=payload)

    config = settings(sample_size=1, retries=2)
    adapter, _ = adapter_for(config, handler)
    with pytest.raises((ValueError, httpx.HTTPStatusError)):
        run_evaluation(engine, config, adapter=adapter)
    assert calls == 1
    with sessions(engine)() as session:
        assert session.scalar(select(EvaluationRun)).status == "partial"
        assert not leaderboard(session)["rows"]
    adapter.close()


def test_registered_model_identity_cannot_be_replaced(engine):
    config = settings(sample_size=1)
    adapter, _ = adapter_for(config)
    run_evaluation(engine, config, adapter=adapter)
    adapter.metadata()
    adapter._metadata["model_version"] = "b" * 64
    with pytest.raises(ValueError, match="different metadata"):
        run_evaluation(engine, config, adapter=adapter)
    adapter.close()


def test_sample_size_larger_than_benchmark_rejected(engine):
    with pytest.raises(ValueError, match="exceeds benchmark"):
        run_evaluation(engine, EvaluationConfig(sample_size=61))
