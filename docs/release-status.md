# Phase 1 delivery and verification — v0.1.0

**Prepared:** 2026-11-16  
**Disposition:** implemented research-preview foundation; public deployment gates remain

## Completed

- Architecture, phased plan, explicit assumptions and database/scoring specifications were written before substantive application implementation.
- FastAPI backend, Next.js/TypeScript interface, SQLAlchemy persistence and explicit Alembic migration.
- Separate model, agent and benchmark registries; 17 application tables covering the requested storage entities.
- 60 original synthetic tasks: ten per starter category, with provenance, typed rubrics, cluster IDs and contamination/review labels.
- Mock provider boundary that excludes references; deterministic public-input rule solving with controlled errors.
- RDKit validation and descriptors, graded typed-field scoring, experimental CRI and a separately labeled reproducibility checklist.
- Category-stratified cluster bootstrap and paired comparisons with strict cohort compatibility.
- Checkpointed/resumable runs, bounded transport retries, usage/timing records, software/data/policy hashes and single-writer locks.
- Stored task responses and diagnostics, computed leaderboard, immutable snapshot interface, model profiles and public task explorer.
- CLI and OpenAPI; optional token-protected submission intake is disabled by default.
- Institutional web design, sortable/filterable rankings, two-system comparison, methodology and honest submission-status page.
- Docker/Compose configuration, GitHub Actions quality gates, pinned dependency files, governance, contribution policy, data license and citation metadata.

## Files created / modified

This was a new project; no existing repository files were modified. The supplied brief was read without alteration. Major source groups are `chemagent/`, `backend/`, `frontend/`, `benchmarks/`, `configs/`, `migrations/`, `scripts/`, `tests/`, `docs/` and `.github/workflows/`. The archive includes a complete `MANIFEST.sha256` inventory of delivered files. Dependencies, caches, local databases and credentials are excluded.

## Verification performed

| Check | Observed result |
|---|---|
| pytest on migrated SQLite | **51 passed** |
| Same pytest suite on PostgreSQL 16.2 | **51 passed** |
| Core benchmark/chemistry/scoring/statistics coverage | **98.76%** (241 statements; 3 uncovered defensive branches) |
| Required core coverage threshold | 80%; passed |
| Alembic upgrade/downgrade/upgrade | Passed in SQLite and PostgreSQL suite |
| Interrupted-run resume and checkpoint retention | Passed |
| Concurrent-writer lock exclusion | Passed in SQLite and PostgreSQL suite |
| Hidden-result public API isolation and mock/private rejection | Passed |
| Rubric typing, malformed JSON, duplicate JSON keys, nonfinite constants | Passed |
| Citation flooding cannot dilute field errors | Passed |
| Paired cohort mismatch and bootstrap edge cases | Passed |
| Python Ruff lint and format check | Passed |
| mypy on `chemagent` and `backend` | Passed; 27 source files |
| Public data integrity guard | Passed; all 60 tasks synthetic, public, CC0; no asserted DOI |
| Frontend ESLint | Passed |
| Frontend TypeScript | Passed |
| Next.js production build | Passed; Next.js 16.4.6 |
| Live backend + standalone frontend HTTP smoke | Passed |
| Rendered homepage, rankings, model profile, comparison, methodology, submission-status, benchmark listing/detail | Passed |
| Encoded and plain benchmark-version URLs | Passed after correcting double-encoding |
| Same-origin API proxy, 60 paired task outcomes, three generated demo systems, CSS assets | Passed |
| Python pinned runtime dependency audit | No known vulnerabilities found at check time |
| npm dependency audit | Zero reported vulnerabilities after patched development dependency override |

Runtime tested: Python 3.12.14, Node 24.22.1, PostgreSQL 16.2. Docker targets Python 3.12, Node 22 and PostgreSQL 16; container images were not executed here. One upstream Starlette TestClient deprecation warning remains; it did not fail tests. There are no known failing automated checks among those completed above.

## Checks not completed

- **Docker execution:** Docker was not installed in the build environment. Compose configuration and a container CI job are supplied; do not describe that job as having passed remotely.
- **Browser interaction and visual QA:** Chromium could not launch because the environment prohibited a required Unix socket. Browser clicks, hydration behavior, rendered chart alignment, responsive overflow and accessibility interaction were therefore not verified. HTTP smoke tests establish server rendering and API integration, not browser behavior.
- **Remote GitHub Actions:** workflow files were created but no external repository or CI run was created.
- **Scientific validation:** no independent expert panel, blinded human scoring, real-model evaluation or experimental validation was conducted.

## Known limitations

This is the first infrastructure milestone, not all seven product phases. Real provider adapters are named extension points. The benchmark has no hidden items, no advanced/expert tasks and no spectroscopy. CRI is a provisional observable-error/calibration proxy; it is not comprehensive hallucination detection. Reproducibility is a metadata checklist. Small cluster counts and synthetic fixtures limit statistical generalization.

Full accounts/RBAC, expert review, arena voting/Elo, live DOI verification, unrestricted uploads, repeated stochastic-run inference, enterprise isolation, cryptographic external audit custody and payment processing are not implemented. The optional submission token is not a replacement for those systems. No public site or repository has been deployed.

## Next recommended step

Run the supplied Docker workflow and browser interaction/visual checks on a normal development host. Then independently review the tasks, rubrics, category weights and CRI before implementing one real provider and repeated evaluations under a frozen benchmark version. Keep demonstration results visibly separate from future independently evaluated model results.
