"""Explicit engine factory: no import-time connections or automatic schema writes."""

import os

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def database_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///./chemagent.db")


def make_engine(url: str | None = None) -> Engine:
    target = url or database_url()
    engine = create_engine(
        target,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if target.startswith("sqlite") else {},
    )
    if target.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, record) -> None:  # type: ignore[no-untyped-def]
            connection.execute("PRAGMA foreign_keys=ON")

    return engine


def sessions(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)
