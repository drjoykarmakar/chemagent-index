# Architecture

ChemAgent Index is a modular monorepo with a Python evaluation worker, FastAPI read API and Next.js interface. PostgreSQL supports shared execution; SQLite supports local and disposable workflow runs.

## Component boundaries

| Component | Responsibility |
|---|---|
| `benchmarks` | Versioned task schema, integrity checks and public/private stores |
| `providers` | Public request contracts, mock solver and digest-pinned Ollama inference |
| `chemistry` | RDKit structures, descriptors and diagnostic checks |
| `scoring` | Typed field rubrics and reliability/metadata proxies |
| `statistics` | Cluster bootstrap and compatible paired comparisons |
| `evaluation` | Checkpoints, retry, provenance, sampling and artifact exports |
| `database` | Registry, run and evidence persistence; Alembic migrations |
| `backend/app` | Public projections and optional submission intake |
| `frontend` | Rankings, run inspection, downloads and comparisons |

The CLI launches evaluation workers. The public API cannot start inference, change provider endpoints or execute model-generated code. Provider requests contain only the task prompt, inputs and output schema; references and rubrics stay inside the evaluator. Ollama performs structured local generation on the model-only track. RDKit validates answers in the evaluator and is not an inference tool in that track.

## Run identity

A run records benchmark bytes, selected task IDs, policy, configuration, model digest, provider protocol, runtime version, source hash and dependency versions. Identity mismatches prevent resume. Full runs and samples have different identities. Model registry entries cannot reuse an ID for different metadata.

Successful tasks commit atomically with responses, scores and validation results. Failures leave a partial run with completed checkpoints. POSIX locks or PostgreSQL advisory locks serialize writers. Completed results and snapshots are immutable through application interfaces; database administrators retain write authority.

## Public projections

Only completed, full, public runs enter rankings. A ranking contains one compatible execution cohort; mock and real-model runs remain separate. Smoke tests and partial runs remain inspectable through run history and artifact downloads without a full-benchmark aggregate.

Private task bodies and results are excluded from public APIs and exports. Private evaluation remains a storage abstraction, not an enterprise tenancy or access-control system.

## Scientific scope

The six-domain starter benchmark is distinct from a comprehensive chemistry index. Advanced synthesis feasibility, spectroscopy, experimental reproducibility, live literature verification and expert adjudication require separate datasets and validation. Repeated stochastic evaluations and multi-system inference are future statistical work.
