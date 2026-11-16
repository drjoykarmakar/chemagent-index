"""All database tests run on a migrated isolated database."""

import os

import pytest
from alembic import command
from alembic.config import Config

from chemagent.config import ROOT
from chemagent.database.models import Base
from chemagent.database.session import make_engine


@pytest.fixture
def migrated_url(tmp_path, monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(cfg, "head")
    engine = make_engine(url)
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    engine.dispose()
    yield url


@pytest.fixture
def engine(migrated_url):
    instance = make_engine(migrated_url)
    yield instance
    instance.dispose()


@pytest.fixture
def dataset():
    from chemagent.benchmarks.store import public_store

    return public_store("chemagentbench-v0.1").load()
