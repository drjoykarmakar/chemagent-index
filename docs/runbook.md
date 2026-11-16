# Operator runbook

## Database setup and recovery

Use PostgreSQL for shared execution. Apply `chemagent init-db` before starting workers or the web API. The initial migration creates all registry, run, artifact and reserved account tables. Before any production upgrade, take a database backup and test the migration on a copy.

`chemagent seed-demo` produces three actual runs and an immutable snapshot. `chemagent evaluate` adds a new run. It never replaces an older finished run. Historical UI values may span different cohorts; do not read them as improvement without compatibility checks.

If a provider timeout or interruption leaves a partial run, obtain its ID from structured logs or the database and rerun with `--resume ID`. Keep all inputs, software and configuration unchanged. After an unclean process termination, a running run may also be resumed once its advisory/POSIX lock is released. A completed or changed run cannot be resumed. Never manually edit a finished run to force resume.

## Configuration

`configs/evaluation.yaml` controls seed, temperature, output limit, permitted tools, timeout and retry count. CLI `--model` and `--benchmark` override those two fields. The provider is responsible for honoring its timeout; current mocks return locally and future API adapters must implement bounded network requests. The runner retries transport timeout/connection errors; invalid structured output is scored as a failure rather than retried into a better score.

`configs/scoring.yaml` defines the active category profile, reliability weights and bootstrap count. Changing it creates a different run cohort. `DATABASE_URL` is a process environment variable. API credentials belong in provider-specific environment variables when adapters are implemented. `.env.example` is a template; Python does not automatically read `.env`.

## Web operation

For development use `npm run dev`. For a production Next build use the provided frontend Dockerfile, which copies the standalone server and static assets. `API_URL` is server-side only. Rewrites are captured at build time; build with the backend destination appropriate to the deployment. The Compose image uses `http://backend:8000`.

HTTP smoke tests in `scripts/http_smoke.mjs` start a backend and the built Next standalone server locally, inspect rendered routes, request CSS assets, and exercise comparison API forwarding. They do not replace browser interaction or visual QA.

## Cost and latency

Mock cost is exactly zero and token counts are unknown/null. Performance per dollar is null when cost is zero or unknown. Wall time is observed local elapsed time including task retries; do not compare it with commercial model latency. Tool call names are captured per response and checked against permissions.

## Private evaluation

Private data must remain outside the repository. The private store requires all-private visibility and mock providers reject private data. Public APIs omit hidden task bodies and results. This path is a storage abstraction; production private evaluation additionally needs real adapters, access control, worker isolation, secrets management and explicit publication policy.

## Submission preview

The web portal shows that intake is not yet open. Operators may set `SUBMISSION_TOKEN` to accept typed submissions by bearer-authenticated POST. No files or external URLs are fetched. Input records enter submitted status. Reviewer assignment, approval/rejection transitions, accounts and RBAC are future work.

## Release checklist

Run Python tests on SQLite and a disposable PostgreSQL database, coverage, lint, formatting, typing, public-data integrity checks, dependency audits, TypeScript, frontend lint and build. Run Compose CI and browser interaction/visual QA on a host that supports them before public deployment. Record failures and unavailable checks in release status. Do not turn passing software tests into claims of scientific validation.
