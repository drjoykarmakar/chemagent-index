"""Public file stores and fail-closed private server-side stores."""

import hashlib
import json
from pathlib import Path
from typing import Any, Protocol

from chemagent.benchmarks.schema import Task
from chemagent.config import ROOT, digest


class TaskStore(Protocol):
    def load(self) -> tuple[dict[str, Any], list[Task], str]: ...


class FileTaskStore:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()

    def load(self) -> tuple[dict[str, Any], list[Task], str]:
        manifest = json.loads((self.directory / "manifest.json").read_text())
        raw = (self.directory / "tasks.jsonl").read_bytes()
        tasks = [Task.model_validate_json(line) for line in raw.splitlines() if line.strip()]
        ids = [t.task_id for t in tasks]
        prompts = [digest({"prompt": t.prompt, "inputs": t.inputs}) for t in tasks]
        if len(set(ids)) != len(ids) or len(set(prompts)) != len(prompts):
            raise ValueError("Duplicate task ID or prompt/inputs")
        if len(tasks) != manifest["sample_count"] or not tasks:
            raise ValueError("Manifest sample count mismatch")
        if manifest["tasks_sha256"] != hashlib.sha256(raw).hexdigest():
            raise ValueError("Dataset checksum mismatch")
        if manifest["benchmark_version"] != "0.1.0":
            raise ValueError("Unsupported benchmark version")
        return manifest, tasks, digest({"manifest": manifest, "task_bytes": raw.hex()})


class PrivateTaskStore(FileTaskStore):
    def __init__(self, directory: Path):
        super().__init__(directory)
        if self.directory.is_relative_to(ROOT.resolve()):
            raise ValueError("Private data must be outside the repository")

    def load(self) -> tuple[dict[str, Any], list[Task], str]:
        manifest, tasks, fingerprint = super().load()
        if any(t.visibility != "private" for t in tasks):
            raise ValueError("Private store requires private visibility")
        return manifest, tasks, fingerprint


def public_store(benchmark: str) -> FileTaskStore:
    if benchmark != "chemagentbench-v0.1":
        raise ValueError("Unknown benchmark; register a versioned store first")
    return FileTaskStore(ROOT / "benchmarks" / benchmark)
