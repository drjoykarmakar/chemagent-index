"""Single-writer run locks: PostgreSQL advisory locks, POSIX locks for local SQLite."""

import hashlib
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, text


@contextmanager
def run_lock(engine: Engine, run_id: str) -> Iterator[None]:
    key = int(hashlib.sha256(run_id.encode()).hexdigest()[:15], 16)
    if engine.dialect.name == "postgresql":
        with engine.connect() as conn:
            acquired = conn.execute(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
            ).scalar()
            if not acquired:
                raise ValueError("Run is already active")
            try:
                yield
            finally:
                conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
    else:
        import fcntl

        with (Path(tempfile.gettempdir()) / f"chemagent-{key}.lock").open("w") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("Run is already active") from exc
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)
