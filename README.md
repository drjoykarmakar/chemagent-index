# ChemAgent Index

**Independent Benchmarking and Ranking of AI Agents for Chemistry**

ChemAgent Index v0.1.0 is an open research infrastructure foundation: versioned chemistry tasks, independent structured scoring, RDKit checks, reproducible runs, uncertainty estimates, a CLI/API and a public-style web interface.

> **DEMONSTRATION DATA — NOT REAL BENCHMARK RESULTS.** DemoChem-A/B/C are deterministic rule solvers with controlled errors. Their scores are computed by the evaluation engine, never embedded in the website. The 60 public synthetic tasks are pending independent expert review and are not evidence of real-world scientific validity.

## Why ChemAgent Index

Scientific fluency is not chemical correctness. Every ranking should expose the tasks, conditions, validation failures, scoring rules, versions and uncertainty behind it. This project creates those audit boundaries before adding commercial models or institutional claims.

## Quick start — Docker

Install Docker Desktop with Compose, unzip this repository and enter its directory:

```bash
docker compose up --build
```

Open http://localhost:3000 for the website, http://localhost:8000/docs for OpenAPI. Compose starts PostgreSQL, applies migrations, executes three real mock evaluations, saves a leaderboard snapshot and starts both application services. No API keys are required. First build downloads dependencies. PostgreSQL data persists in a named volume.

```bash
docker compose exec backend chemagent evaluate --model demo-agent --benchmark chemagentbench-v0.1
docker compose exec backend chemagent leaderboard
docker compose down
```

The default password and localhost bindings are for local development. Do not expose this configuration publicly. Restarting the initialization service creates new retained runs, not overwrites. `docker compose down -v` deletes the development database; use only intentionally.

**Verification boundary:** PostgreSQL 16.2 and SQLite tests passed in the build environment. Docker itself was unavailable there; the included Compose CI job is the first container-level validation gate.

## Quick start — local checkout

Reference environment: Python **3.12**, Node **22+**. Exact Python locks were resolved on Python 3.12; Python 3.11+ is allowed by the package, but those other versions were not release-tested.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.lock
pip install -e . --no-deps
chemagent init-db
chemagent seed-demo
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Local Python development uses `sqlite:///./chemagent.db` by default. To use PostgreSQL, set `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE` **before** migrations, evaluations and API startup. Operate from the repository root or set `CHEMAGENT_ROOT` explicitly. Keep credentials in environment variables; `.env` is not automatically loaded by the Python process.

## Architecture

```text
chemagent/       benchmark contracts, providers, RDKit, scoring, statistics, runner, database
backend/app/     FastAPI public projections and optional token-protected intake
frontend/        Next.js, TypeScript, React, Tailwind and institutional CSS
benchmarks/      original synthetic tasks, manifest, JSON Schema and data license
configs/         versioned evaluation settings and scoring weights
migrations/      explicit Alembic migration history
scripts/         dataset rebuild, integrity checks, dependency locks, smoke tests
tests/          core, API, persistence, retry and comparison tests
docs/           architecture, schema, methods, scoring, runbook and release evidence
```

See [architecture](docs/architecture.md), [database schema](docs/database.md) and [benchmark contract](benchmarks/schemas/task.schema.json). Provider requests contain public inputs and schema only. Reference answers remain inside the trusted evaluation layer.

## Benchmark categories

| Starter domain | Tasks | Actual measurement |
|---|---:|---|
| Chemistry reasoning | 10 | Dilution, concentration, yield, pH, equilibrium, Gibbs energy |
| Medicinal chemistry | 10 | pIC50, efficiency proxy, selectivity and supplied property constraints |
| Molecular validation | 10 | SMILES validity, formula, heavy atoms, donor counts |
| Synthesis reasoning | 10 | Route yield, atom accounting, redox labels, limiting reagent |
| Literature reliability | 10 | Closed-catalog matching, discrepancy and evidence-limit checks |
| Stress tests | 10 | Valence, salt, false premise, unit and stereochemistry traps |

All are authored synthetic examples, openly released under CC0-1.0. All are introductory/intermediate, have high contamination risk, and await independent expert review. There are **zero private evaluation items**. This is not spectroscopy, molecular generation, retrosynthesis feasibility, clinical judgment or online literature benchmarking.

## Running evaluations

```bash
chemagent benchmark list
chemagent model list
chemagent validate 'C[C@H](O)C(=O)O'
chemagent evaluate --model demo-agent --benchmark chemagentbench-v0.1
chemagent evaluate --model demo-b --benchmark chemagentbench-v0.1
chemagent leaderboard
```

Settings are in `configs/evaluation.yaml`. For a partial run, use exactly the same settings and model with `--resume RUN_ID`. Successful task checkpoints are retained. A changed dataset, policy, model, code, dependency environment or execution configuration prevents resume. Completed runs are immutable through application interfaces. POSIX locks protect local runs; PostgreSQL advisory locks protect shared-database workers.

## Adding a model

Implement `BaseModelAdapter` and register immutable model/version metadata. The runnable provider is `MockAdapter`. Named OpenAI, Anthropic, Gemini, OpenRouter and local adapters are **explicit, fail-closed Phase 2 extension points**, not functioning integrations. No untested API compatibility is implied. Record actual token usage and cost; unknown values are `null`, never zero estimates. The mock uses RDKit and must be evaluated on the model-plus-tools track.

## Creating a benchmark

Follow the strict `Task` schema, including provenance, explicit expected fields, severity and scoring weights, a template `cluster_id`, known ambiguity, and review status. Rebuild the manifest checksum whenever bytes change. The public development loader checks content integrity, count and duplicate prompt/input pairs. Molecular reference fixtures are independently checked in tests. Add a registered versioned store and preregister the profile; never silently change a public release.

`PrivateTaskStore` requires a directory outside the repository and all-private task visibility. Mock evaluation rejects hidden tasks. The public API omits private bodies/results. This is a server-side storage boundary, not implemented encryption or enterprise tenancy.

## Scoring and uncertainty

The starter score is an equal-weight mean of six category scores, not the planned full ChemAgent Index. All categories must be present. Task rubrics reward typed, verifiable answers; prose fluency earns no score. Numerical answers receive graded credit beyond declared tolerance.

Category-stratified cluster bootstrap uses 2,000 seeded resamples and reports 95% intervals, standard errors, counts and task sample variances. Paired comparisons require identical benchmark, scoring, environment, track and configuration hashes. Small numbers of clusters limit the strength of inference. CRI is an experimental severity-and-calibration proxy; the reproducibility score is a metadata checklist. Neither is double-counted in the starter composite. See [full scoring specification](docs/scoring.md).

## Reproducibility

Runs retain provider/model versions, benchmark and policy hashes, code hash, git commit when available, Python/RDKit/dependency versions, seed, temperature, tool permissions, timestamp, raw responses, response hashes, usage, validation failures and scores. Finished runs are retained; leaderboard snapshots store a content hash. Database administrators still have write authority; production signing and audit storage are future work.

## API

- `GET /health`
- `GET /api/v1/leaderboard?cohort=...`
- `GET /api/v1/models` and `/models/{id}`
- `GET /api/v1/agents`
- `GET /api/v1/benchmarks` and `/benchmarks/{version_id}`
- `GET /api/v1/evaluations/{run_id}`
- `GET /api/v1/compare?left=RUN_ID&right=RUN_ID`
- `GET /api/v1/snapshots/{id}`
- `POST /api/v1/submissions` — disabled by default; optional operator bearer token, not full account/RBAC support

OpenAPI is available at `/docs`. The UI includes rankings, profiles with task inspection, benchmark exploration, paired comparisons, methodology and an honest submission-status page. It reads stored results; an unavailable backend produces an explicit empty state.

## Quality checks

```bash
ruff check .
ruff format --check .
mypy chemagent backend
pytest --cov --cov-report=term-missing
python scripts/check_public_data.py
pip-audit -r requirements.lock --no-deps --disable-pip
cd frontend
npm run lint
npm run typecheck
npm run build
npm audit --audit-level=moderate
```

Set `TEST_DATABASE_URL` to an **isolated disposable PostgreSQL database** to repeat the database suite there. Tests clear application tables in that database. See [release verification](docs/release-status.md) for actual outcomes, including checks that could not run locally.

## Contributing and governance

Read [CONTRIBUTING](CONTRIBUTING.md), [GOVERNANCE](GOVERNANCE.md), [conflict-of-interest policy](CONFLICT_OF_INTEREST.md) and [SECURITY](SECURITY.md). Maintainers’ systems receive no preferential treatment. No provider sponsorship may change scientific outcomes.

## Citation

Use [CITATION.cff](CITATION.cff) and cite the exact benchmark version, hashes and snapshot used. No DOI has been assigned. Add a Zenodo DOI only after a real archive exists.

## Next milestones

Phase 2: tested real-provider integration and repeated stochastic evaluations. Phase 3: live reference verification with provenance and separately evaluated claim support. Phase 4: expert-reviewed advanced chemistry, spectroscopy and route datasets. Phase 5: accounts, review workflows and production security. Phase 6: separately governed arena ratings. Phase 7: enterprise tenancy and private evaluations. No billing or institutional rankings are implemented.
