# Contributing

Start with an issue describing the scientific problem, intended behavior and reproducible example. Small changes should include focused checks; scorer and dataset changes must include independent gold-answer validation and explicit versioning.

Use Python 3.12 and Node 22+. Install the exact lockfiles, run the checks in README, and do not update dependency locks incidentally. Keep providers, task data, validation, scoring, statistics and presentation separate. Do not expose references to adapters or request hidden chain-of-thought. Use concise reasoning summaries and evidence fields.

For new tasks, supply source/license, curator, curation method, synthetic status, publication date, validation and review status, difficulty, ambiguity, contamination risk, reference answer, typed rubric, severity and cluster ID. Never add proprietary datasets, API secrets, private tests or invented citations. Expert scientific review is distinct from passing software tests.

For provider integration, mock external network contracts in tests and make optional credentials explicit. Preserve unknown usage/cost as null. Before real rankings, independently validate version identities, timeout semantics, retry behavior, tool accounting and provider configuration capture.

Open a pull request with the concrete behavior change, scientific implications, tests run, and limitations. Do not claim tests or external validation that did not occur. Follow CODE_OF_CONDUCT.md.
