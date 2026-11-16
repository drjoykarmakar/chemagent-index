from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from chemagent.config import ROOT
from chemagent.database.models import Base
from chemagent.database.session import make_engine


def test_migration_upgrade_downgrade_roundtrip(migrated_url):
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    command.downgrade(config, "base")
    engine = make_engine(migrated_url)
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    command.upgrade(config, "head")
    assert set(Base.metadata.tables).issubset(inspect(engine).get_table_names())
    engine.dispose()
