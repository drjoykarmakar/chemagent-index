"""Portable, checksummed artifacts for public evaluation runs."""

import csv
import hashlib
import io
import json
import zipfile
from typing import Any

from sqlalchemy.orm import Session

from chemagent.database.queries import run_detail


def _json(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, default=str, allow_nan=False) + "\n"
    ).encode()


def artifact_files(session: Session, run_id: str) -> dict[str, bytes]:
    detail = run_detail(session, run_id)
    if detail is None:
        raise ValueError("Public evaluation not found")
    tasks = detail.pop("tasks")
    files = {
        "run.json": _json(detail),
        "config.json": _json(detail["provenance"]["config"]),
        "summary.json": _json(detail["summary"]),
        "responses.jsonl": b"".join(
            (
                json.dumps({k: t[k] for k in ["task_id", "response", "usage"]}, sort_keys=True)
                + "\n"
            ).encode()
            for t in tasks
        ),
        "validations.jsonl": b"".join(
            (
                json.dumps({"task_id": t["task_id"], "validation": t["validation"]}, sort_keys=True)
                + "\n"
            ).encode()
            for t in tasks
        ),
    }
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "task_id",
            "category",
            "cluster_id",
            "score",
            "cri",
            "reproducibility",
            "error_rate",
            "calibration_error",
        ],
    )
    writer.writeheader()
    for task in tasks:
        if task["score"]:
            writer.writerow(task["score"])
    files["scores.csv"] = buffer.getvalue().encode()
    files["manifest.json"] = _json(
        {
            "format_version": "1.0",
            "run_id": run_id,
            "status": detail["status"],
            "task_count": len(tasks),
            "notice": detail["notice"],
            "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
        }
    )
    return files


def export_zip(session: Session, run_id: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in artifact_files(session, run_id).items():
            archive.writestr(name, data)
    return buffer.getvalue()
