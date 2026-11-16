import hashlib
import json
import shutil
from collections import Counter

import pytest

from chemagent.benchmarks.schema import Task
from chemagent.benchmarks.store import FileTaskStore, PrivateTaskStore, public_store
from chemagent.config import ROOT, EvaluationConfig, load_policy
from chemagent.providers.base import PublicRequest
from chemagent.providers.mock import solve


def test_dataset_contract_and_independent_reference_check(dataset):
    manifest, tasks, fingerprint = dataset
    assert manifest["sample_count"] == 60
    assert set(Counter(t.category for t in tasks).values()) == {10}
    assert len(fingerprint) == 64
    for task in tasks:
        computed = solve(task.inputs)
        for key, expected in task.reference_answer.items():
            assert computed[key] == (
                pytest.approx(expected, abs=0.00001) if type(expected) in (int, float) else expected
            )
        assert task.provenance.synthetic
        assert task.provenance.DOI is None
        request = PublicRequest.from_task(task)
        assert not hasattr(request, "reference_answer")
        assert not hasattr(request, "rubric")


def test_file_integrity_and_duplicates(tmp_path):
    shutil.copytree(ROOT / "benchmarks/chemagentbench-v0.1", tmp_path / "data")
    folder = tmp_path / "data"
    with (folder / "tasks.jsonl").open("a") as handle:
        handle.write((folder / "tasks.jsonl").read_text().splitlines()[0] + "\n")
    with pytest.raises(ValueError, match="Duplicate"):
        FileTaskStore(folder).load()
    (folder / "tasks.jsonl").write_text(
        (ROOT / "benchmarks/chemagentbench-v0.1/tasks.jsonl")
        .read_text()
        .replace("synthetic fixture", "altered fixture", 1)
        + "\n"
    )
    with pytest.raises(ValueError, match="checksum"):
        FileTaskStore(folder).load()


def test_bad_count_and_version(tmp_path):
    shutil.copytree(ROOT / "benchmarks/chemagentbench-v0.1", tmp_path / "data")
    path = tmp_path / "data/manifest.json"
    manifest = json.loads(path.read_text())
    manifest["sample_count"] = 59
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="count"):
        FileTaskStore(path.parent).load()
    manifest["sample_count"] = 60
    manifest["benchmark_version"] = "2.0.0"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="version"):
        FileTaskStore(path.parent).load()


def test_private_store_boundary(tmp_path):
    with pytest.raises(ValueError, match="outside"):
        PrivateTaskStore(ROOT / "private")
    shutil.copytree(ROOT / "benchmarks/chemagentbench-v0.1", tmp_path / "private")
    with pytest.raises(ValueError, match="private visibility"):
        PrivateTaskStore(tmp_path / "private").load()
    path = tmp_path / "private/tasks.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    for record in records:
        record["visibility"] = "private"
    raw = "".join(json.dumps(r) + "\n" for r in records).encode()
    path.write_bytes(raw)
    manifest_path = path.parent / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["tasks_sha256"] = hashlib.sha256(raw).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    assert len(PrivateTaskStore(path.parent).load()[1]) == 60


def test_schema_rejects_invalid_rubric(dataset):
    value = dataset[1][0].model_dump(mode="json")
    value["reference_answer"]["unexpected"] = 1
    with pytest.raises(ValueError, match="match exactly"):
        Task.model_validate(value)
    value.pop("reference_answer")
    with pytest.raises(ValueError):
        Task.model_validate(value)


def test_unknown_benchmark_and_config():
    with pytest.raises(ValueError):
        public_store("../private")
    with pytest.raises(ValueError):
        EvaluationConfig(track="model_only", tools=["rdkit"])
    assert EvaluationConfig(track="model_only", tools=[]).track == "model_only"
    assert sum(load_policy()["weights"].values()) == 6
