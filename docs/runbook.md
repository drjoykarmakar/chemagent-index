# Operations reference

## Configuration

| Setting | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy database connection | `sqlite:///./chemagent.db` |
| `CHEMAGENT_ROOT` | Checkout containing configuration, benchmark and migrations | Package checkout root |
| `API_URL` | Server-side frontend backend destination | `http://127.0.0.1:8000` |
| `OLLAMA_BASE_URL` | Evaluator's Ollama endpoint | `http://127.0.0.1:11434` |
| `SUBMISSION_TOKEN` | Optional bearer token for API intake | Intake disabled |

Python processes read environment variables directly; `.env` is not loaded automatically. Frontend proxy destinations are captured at build time. The Compose build uses `http://backend:8000`.

`configs/evaluation.yaml` defines mock settings. `configs/ollama.yaml` defines the pinned local model and generation budget. CLI model and benchmark flags override configuration only when supplied. `--sample-size` creates a non-ranking smoke evaluation.

## Database lifecycle

`chemagent init-db` applies Alembic migrations without dropping existing data. `chemagent seed-demo` adds three mock runs and a snapshot. Each evaluation adds a retained run. Database upgrades require normal backup and migration validation practices.

A partial run can resume with `chemagent evaluate --config CONFIG --resume RUN_ID`, using identical settings, sample size and software. A completed or incompatible run is rejected. Process termination releases the local or PostgreSQL run lock.

## Runtime and exports

Ollama health metadata is checked before a run. The installed model digest is checked before each generation. Missing or changed models fail without substituting another provider. Timeout and connection failures are retried within the configured budget. HTTP protocol errors and malformed model output are not treated as retryable generation attempts.

`chemagent evaluate --output-dir DIRECTORY` writes a ZIP in normal completion and handled failure paths. Abrupt process termination may prevent that export; committed checkpoints remain in the database. `chemagent export RUN_ID PATH.zip` exports an existing public run. Existing artifact files are not overwritten.

Raw token counts and elapsed task time are retained. Local compute cost is null; mock cost is zero. Neither produces a performance-per-dollar value.

## Deployment and intake

Compose provides local database, initializer, backend and frontend services. PostgreSQL storage persists across restarts. `docker compose down -v` removes the database volume.

Public researcher intake remains closed. The optional submission API stores typed records in submitted status and does not fetch supplied URLs. Accounts, reviewer assignment and approval transitions are not implemented.

## Quality workflows

The quality workflow checks Python and TypeScript, migrated SQLite and PostgreSQL databases, dependency audits, public task integrity, Compose startup and live application HTTP behavior. HTTP checks inspect server-rendered pages, CSS and API forwarding; browser interaction and visual review remain separate checks.

The manual benchmark workflow performs local model inference and retains logs, the SQLite database and checksummed run archives for 30 days. Its results remain downloadable artifacts until a deployment explicitly loads or publishes them.
