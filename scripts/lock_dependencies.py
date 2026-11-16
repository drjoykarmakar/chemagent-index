"""Capture this environment's resolved transitive dependencies into exact locks.

Run after a deliberate dependency update on the supported Python 3.12 environment.
The resulting locks are reviewed artifacts, not regenerated automatically by CI.
"""

import tomllib
from importlib.metadata import distribution
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

root = Path(__file__).resolve().parents[1]
project = tomllib.loads((root / "pyproject.toml").read_text())["project"]


def lock(requirements: list[str], destination: str) -> None:
    pending = [Requirement(r) for r in requirements]
    visited: set[tuple[str, tuple[str, ...]]] = set()
    pins: dict[str, str] = {}
    while pending:
        request = pending.pop()
        name = canonicalize_name(request.name)
        extras = tuple(sorted(request.extras))
        if (name, extras) in visited:
            continue
        visited.add((name, extras))
        package = distribution(name)
        pins[name] = package.version
        for item in package.requires or []:
            dependency = Requirement(item)
            if dependency.marker is None or any(
                dependency.marker.evaluate({"extra": e}) for e in ["", *extras]
            ):
                pending.append(dependency)
    (root / destination).write_text(
        "# Resolved on Python 3.12; update deliberately and rerun all checks.\n"
        + "".join(f"{k}=={v}\n" for k, v in sorted(pins.items()))
    )


lock(project["dependencies"], "requirements.lock")
lock(project["dependencies"] + project["optional-dependencies"]["dev"], "requirements-dev.lock")
