# Database schema and ownership

PostgreSQL 16+ is the reference database. JSON columns hold versioned scientific artifacts; primary identities and relationships use relational keys. All timestamps are UTC ISO-8601 strings for consistent SQLite test parity.

| Table | Identity / purpose |
|---|---|
| organizations, users, api_keys | Reserved account and hashed-credential metadata; no authentication service shipped |
| models | Stable opaque model ID plus versioned provider/model metadata |
| agents | Separate agent ID, base-model relationship and tool/workflow metadata |
| benchmarks, benchmark_versions | Dataset identity, semantic version, content hash and provenance manifest |
| benchmark_tasks | Task identity scoped to benchmark version; public metadata only for hidden sets |
| evaluations | Campaign identity and model/benchmark references |
| evaluation_runs | Run identity, status, fingerprints, environment, summary and timestamps |
| responses | Unique run/task checkpoint with raw response, parse status, usage and timing |
| scores | One rubric outcome per response |
| validation_results | Structured diagnostics for each response |
| citations | Observed citations and fixture-verification results |
| leaderboard_snapshots | Immutable cohort snapshot payload and content hash |
| submissions | Intake metadata and review status; disabled unless operator enables it |
| audit_logs | Append-only event records; secrets excluded |

Only a running/partial run can acquire new responses. Successful task checkpoints are not overwritten on resume. A finished run cannot be resumed. Public API responses are explicit projections rather than raw ORM serialization. Hidden task bodies, answers, response text and validation expectations are not returned. Alembic upgrade/downgrade is tested with SQLite and PostgreSQL in CI. Server startup never calls `create_all`.
