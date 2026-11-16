"""Developer CLI. Run from the checkout or set CHEMAGENT_ROOT."""

import json
import logging
from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config

from chemagent.benchmarks.store import public_store
from chemagent.chemistry.rdkit_service import validate_smiles
from chemagent.config import ROOT, load_config
from chemagent.database.models import uid
from chemagent.database.queries import leaderboard as query_leaderboard
from chemagent.database.queries import run_detail, snapshot
from chemagent.database.session import make_engine, sessions
from chemagent.evaluation.export import export_zip
from chemagent.evaluation.runner import run_evaluation
from chemagent.providers.mock import DEMOS

app = typer.Typer(no_args_is_help=True)
bench_app = typer.Typer()
model_app = typer.Typer()
app.add_typer(bench_app, name="benchmark")
app.add_typer(model_app, name="model")


def output(value: object) -> None:
    typer.echo(json.dumps(value, indent=2, default=str))


@app.command()
def init_db() -> None:
    """Apply Alembic migrations; never drop existing data."""
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(cfg, "head")
    typer.echo("Database migrated")


@app.command()
def evaluate(
    model: str | None = None,
    benchmark: str | None = None,
    config: Annotated[Path | None, typer.Option()] = None,
    resume: str | None = None,
    sample_size: Annotated[int | None, typer.Option(min=1)] = None,
    output_dir: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Evaluate a registered model; prints the immutable run ID."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = load_config(config)
    if model is not None:
        settings.model = model
    if benchmark is not None:
        settings.benchmark = benchmark
    if sample_size is not None:
        settings.sample_size = sample_size
    engine = make_engine()
    run_id = resume or uid()
    try:
        output({"run_id": run_evaluation(engine, settings, resume=resume, new_run_id=run_id)})
    finally:
        try:
            if output_dir is not None:
                with sessions(engine)() as session:
                    if run_detail(session, run_id) is not None:
                        output_dir.mkdir(parents=True, exist_ok=True)
                        target = output_dir / f"{run_id}-{uid()[:8]}.zip"
                        with target.open("xb") as handle:
                            handle.write(export_zip(session, run_id))
                        output({"run_id": run_id, "artifact": str(target)})
        finally:
            engine.dispose()


@app.command("export")
def export_run(run_id: str, destination: Path) -> None:
    """Export a public run, including partial checkpoints, to a new ZIP file."""
    engine = make_engine()
    try:
        with sessions(engine)() as session:
            data = export_zip(session, run_id)
        with destination.open("xb") as handle:
            handle.write(data)
        output({"run_id": run_id, "artifact": str(destination)})
    finally:
        engine.dispose()


@app.command()
def seed_demo() -> None:
    """Generate three actual deterministic mock runs and an immutable snapshot."""
    engine = make_engine()
    try:
        runs = []
        for model in DEMOS:
            settings = load_config()
            settings.model = model
            runs.append(run_evaluation(engine, settings))
        with sessions(engine)() as session:
            output({"runs": runs, "snapshot": snapshot(session)})
    finally:
        engine.dispose()


@app.command()
def validate(smiles: str) -> None:
    """Validate a SMILES and calculate RDKit descriptors."""
    result = validate_smiles(smiles)
    output(result)
    if not result["valid"]:
        raise typer.Exit(code=1)


@app.command()
def leaderboard() -> None:
    engine = make_engine()
    with sessions(engine)() as session:
        output(query_leaderboard(session))
    engine.dispose()


@bench_app.command("list")
def benchmark_list() -> None:
    manifest, _, fingerprint = public_store("chemagentbench-v0.1").load()
    output({**manifest, "fingerprint": fingerprint})


@model_app.command("list")
def model_list() -> None:
    output(
        [{"model_id": key, "display_name": value[0], "demo": True} for key, value in DEMOS.items()]
    )


if __name__ == "__main__":
    app()
