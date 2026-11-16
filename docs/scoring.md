# Scoring specification v0.1.0

## Task scores
Each task declares typed fields with positive weights. Numeric answers use `max(0, 1 - |answer-reference| / (5*tolerance))`, with full credit within absolute tolerance; the interval immediately outside tolerance starts from 1 using excess error above tolerance. Non-numeric fields require exact typed equality (ordered lists are meaningful). Booleans are never accepted as numbers. Missing, nonfinite or mistyped fields score zero. Unrecognized fields inside `answer` are rejected. Concise reasoning is recorded but never scored for fluency. Molecule tasks independently recompute reference properties with RDKit during dataset QC. Invalid JSON/schema scores zero and is counted as a format failure, not a provider transport failure.

Task = 100 × weighted mean of field correctness. Each discrepancy stores expected/observed values, magnitude and credit. Confidence must be in [0,1]. All tasks require explicit confidence, citation list and uncertainty list.

## Chemistry Reliability Index: experimental operationalization
For each field, error is 1-credit; severity is a preregistered positive rubric weight separate from capability weight. Unsupported citation entries are additional severity-5 errors, checked against the task's closed evidence fixture. Citation acceptance means membership in supplied evidence, not live DOI resolution or entailment.

For task i, E_i=min(1, [sum(severity × field error) + 5 × unsupported citation count] / sum(field severity)). The denominator is fixed by the rubric, so citation flooding cannot dilute errors. C_i is a binary fully-correct indicator (all fields full credit and no unsupported citations). B_i=(confidence_i-C_i)^2; malformed responses have E_i=B_i=1. CRI=100×[1 - 0.8 mean(E_i) - 0.2 mean(B_i)]. Report the error and calibration terms separately. Missing fields are errors, so blanket abstention cannot receive a high score. This is a bounded, continuous starter reliability proxy; it does not measure every hallucination or source misrepresentation. The severity and calibration weights are normative and must be independently reviewed before official rankings. No validated clinical or safety claim follows from CRI.

## Reproducibility checklist
Report a distinct 0–100 metadata-completeness checklist: valid structured response (40), nonempty concise reasoning summary (20), explicit uncertainties list (20), required units present and correct (20). Presence alone does not establish scientific reproducibility. Run provenance completeness is recorded separately. Neither CRI nor this checklist is included in the starter composite to avoid double-counting the same task outcomes.

## Category profile and missingness
`configs/scoring.yaml` contains the aspirational full profile and the actual six-category starter profile. The latter gives equal weight to reasoning, medicinal chemistry, molecular validation, synthesis reasoning, literature reliability and stress tests. All six must be present; no silent reweighting. The UI calls this a starter index, not the full ChemAgent Index. Category means include all completed responses including parsing failures. Transport-failed runs remain partial and are ineligible until resumed successfully. Demo scores are measured mock behavior, never estimates of real-model performance.

## Uncertainty
Use a seeded percentile bootstrap with 2,000 resamples. Resample independent `cluster_id` groups within each category, preserving correlated task families, then calculate category means and the fixed-weight composite. Report 2.5th/97.5th percentiles, task-level sample variance, bootstrap standard error, task and cluster counts. Intervals describe variation over this synthetic task collection, not population validity or run-to-run nondeterminism. Fewer than two clusters is insufficient and returns no CI. Repeated stochastic runs are a future hierarchical level.

## Comparison
Compare complete paired task IDs only, with identical benchmark bytes, scoring policy, execution configuration and track. Bootstrap paired differences using the same cluster draw, report 95% CI, mean paired effect, standardized paired effect when variance is nonzero, and win/loss/tie counts. A CI spanning zero is inconclusive. The bootstrap sign probability is descriptive, not a calibrated null-hypothesis p-value. No multiple-comparison-adjusted winner claim is made. Never infer significance from independent interval overlap alone.

## Versioning
Benchmark changes, rubric changes and policy changes alter fingerprints. A different hash is a different cohort even if a human mistakenly reuses a version string. Finished runs and snapshots are append-only through the application. Database administrators retain physical write authority; use backups and external signed snapshots for stronger guarantees.

Smoke samples retain task-level scores only. They have no composite, bootstrap interval or ranking eligibility, including samples whose size equals the full benchmark.
