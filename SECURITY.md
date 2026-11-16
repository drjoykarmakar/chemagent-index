# Security and deployment boundary

v0.2.0 is a local research preview, not a hardened multi-tenant hosted service. Public endpoints are read-only except optional token-protected submission intake. Evaluations run only in trusted CLI workers. No arbitrary file uploads, submitted code, user-controlled URL fetches, or model execution are exposed through HTTP.

Keep provider credentials and database URLs in environment variables, never task files, source, logs or browser bundles. The typed evaluation configuration forbids extra fields. The Ollama adapter uses a trusted operator-configured local endpoint and records model identity without credentials. Provider metadata and errors must exclude secrets.

The API has bounded per-process request counting, body-size checks and typed input validation. These are local safeguards, not distributed abuse protection. Before public deployment, add TLS, trusted reverse-proxy configuration, stream/body limits at ingress, distributed rate limiting, authenticated roles, CSRF/session design as appropriate, monitoring, secret rotation, dependency monitoring and database backups. Submission bearer tokens are operator-issued preview access, not researcher/reviewer/admin RBAC.

Use a separate disposable database for tests. They clear application tables. Migrations are explicit; no startup `create_all`. Private datasets must be stored outside the checkout with restrictive OS permissions. Hidden bodies and results are omitted from public projections, but encrypted storage, encryption-key management, secure worker isolation and enterprise tenancy are not implemented.

The application does not expose mutation endpoints for completed runs or snapshots; database administrators can still alter data. Strong audit guarantees require external append-only storage, signed artifacts and access controls.

If a security issue is found after public hosting, use the repository's private vulnerability reporting feature once enabled. Do not post secrets, private tasks or exploitable production details in public issues.
