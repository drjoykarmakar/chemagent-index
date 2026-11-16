# ChemAgent Index

Open evaluation infrastructure for AI systems in chemistry. Version **0.2.0** supports local open-model inference, versioned tasks, independent scoring, uncertainty estimates and downloadable evidence for every run.

ChemAgentBench v0.1.0 contains **60 public synthetic development tasks** across six domains. Tasks have high contamination risk and await independent expert review. Results describe this collection; they do not establish general chemistry competence or experimental validity. Demonstration systems and model inference results are labeled separately and never share a ranking cohort.

## Evaluation

The **Run benchmark** GitHub Actions workflow evaluates Qwen2.5 0.5B through a pinned Ollama runtime. It requires no provider API key. The workflow has two scopes:

| Scope | Tasks | Output | Ranking eligibility |
|---|---:|---|---|
| `smoke` | 5 | Responses, task scores, validation and provenance | Excluded |
| `full` | 60 | Task evidence and six-category aggregate with intervals | Complete runs only |

Workflow runs retain artifacts for 30 days. Each run archive contains `run.json`, `config.json`, `summary.json`, `responses.jsonl`, `scores.csv`, `validations.jsonl` and a checksum manifest. Partial evaluations retain completed checkpoints. The workflow also retains its evaluation database and logs. Artifacts are not automatically published to a website. GitHub Actions compute availability and billing depend on the repository's plan.

Model identity is pinned by its complete manifest digest in [`configs/ollama.yaml`](configs/ollama.yaml). A changed model tag fails verification. Runtime version, model digest, generation parameters, task selection, software identity and scoring policy are recorded with each run. Local inference costs are unknown, not assumed to be zero.

## Local application

Requirements: Docker with Compose, or Python 3.12 and Node 22+.

```bash
docker compose up --build
```

The application is available at [localhost:3000](http://localhost:3000), with API documentation at [localhost:8000/docs](http://localhost:8000/docs). Compose initializes PostgreSQL and three clearly labeled demonstration evaluations. Data persists in a named volume. The default Compose configuration binds local ports and uses development credentials.

A Python checkout uses SQLite by default:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.lock
pip install -e . --no-deps
chemagent init-db
chemagent seed-demo
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

The frontend development server starts with `npm ci` and `npm run dev` in `frontend/`. `DATABASE_URL` selects another database; `API_URL` selects the backend for the Next.js server. Configuration variables are listed in [the operations reference](docs/runbook.md).

## Local model evaluation

The Ollama server must expose the model specified by the configuration at `http://127.0.0.1:11434` (or `OLLAMA_BASE_URL`).

```bash
ollama pull qwen2.5:0.5b
chemagent evaluate --config configs/ollama.yaml --sample-size 5 --output-dir results
chemagent evaluate --config configs/ollama.yaml --output-dir results
chemagent export RUN_ID evaluation.zip
```

The first evaluation is a smoke test; the second covers the full benchmark. `--resume RUN_ID` retains successful checkpoints and requires unchanged scientific and software inputs. Completed runs cannot be resumed or overwritten. Invalid model JSON is captured and scored; it is not retried into a better answer. Only transport failures trigger bounded retries.

`MockAdapter` remains available for software tests and demonstrations. `OllamaAdapter` performs local model inference without tool execution. Other named provider classes are unsupported extension contracts.

## Benchmark coverage

| Domain | Tasks | Measurement |
|---|---:|---|
| Chemistry reasoning | 10 | Concentration, yield, pH and energy calculations |
| Medicinal chemistry | 10 | Property constraints, pIC50 and supplied tradeoffs |
| Molecular validation | 10 | SMILES validity and molecular descriptors |
| Synthesis reasoning | 10 | Route arithmetic and structured consistency |
| Literature reliability | 10 | Closed-catalog matching and evidence limits |
| Stress tests | 10 | Unit, structure, stereochemistry and premise traps |

The dataset is original synthetic material under CC0-1.0. There are no private items in this release. The complete task schema, provenance and limitations are retained in [`benchmarks/`](benchmarks/).

## Scoring and evidence

The starter index is the equal-weight mean of six category scores. Full coverage is required; smoke results receive no composite score. Typed field rubrics and independent RDKit checks determine credit. Category-stratified cluster bootstrap uses 2,000 seeded resamples. Paired comparisons require compatible complete runs. The experimental reliability proxy and metadata completeness checklist are reported separately.

Detailed specifications: [scoring](docs/scoring.md), [methods](docs/methodology.md), [architecture](docs/architecture.md), [database](docs/database.md), and [evaluation artifacts](docs/evaluation.md).

## API

| Endpoint | Resource |
|---|---|
| `GET /health` | Database health and software version |
| `GET /api/v1/leaderboard` | Complete results in one compatible cohort |
| `GET /api/v1/models`, `/models/{id}` | Registry and run history |
| `GET /api/v1/agents` | Agent registry |
| `GET /api/v1/benchmarks`, `/benchmarks/{id}` | Benchmark metadata and public tasks |
| `GET /api/v1/evaluations` | Latest 100 public runs |
| `GET /api/v1/evaluations/{id}` | Captured task evidence and provenance |
| `GET /api/v1/evaluations/{id}/download` | Checksummed ZIP artifact |
| `GET /api/v1/compare?left=ID&right=ID` | Compatible paired comparison |
| `GET /api/v1/snapshots/{id}` | Retained leaderboard snapshot |

Private results are omitted from public projections and exports. Optional token-protected submission intake is disabled by default; accounts and review workflows are not implemented.

## Development

```bash
ruff check .
ruff format --check .
mypy chemagent backend
pytest --cov --cov-report=term-missing
python scripts/check_public_data.py
```

Frontend checks are `npm run lint`, `npm run typecheck`, and `npm run build`. The quality workflow also runs PostgreSQL tests, dependency audits, Compose startup and live HTTP integration checks. `TEST_DATABASE_URL` must reference a disposable test database: database fixtures clear application tables.

Contribution and project policies: [contributing](CONTRIBUTING.md), [governance](GOVERNANCE.md), [conflicts of interest](CONFLICT_OF_INTEREST.md), [security](SECURITY.md), [code of conduct](CODE_OF_CONDUCT.md). Citation metadata is in [CITATION.cff](CITATION.cff). Source code and documentation are MIT licensed.
