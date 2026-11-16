# Evaluation protocol and artifact format

## Local model protocol

The default model is [Qwen2.5 0.5B Q4_K_M](https://ollama.com/library/qwen2.5:0.5b), distributed under Apache 2.0. The configured model manifest digest identifies its weights, template, system prompt and license layers. Runtime v0.40.16 is pinned in the workflow with the official release archive's SHA-256 checksum.

The adapter uses Ollama's [generate endpoint](https://docs.ollama.com/api/generate) with `stream: false`, the task's JSON Schema as `format`, a recorded system prompt, and explicit seed, temperature, context size, output limit and CPU thread count. A fixed seed does not guarantee bit-identical results across hardware or runtime versions.

Only task prompts, inputs and output schemas reach the model. Benchmark references and scoring rubrics are never sent. The scorer's RDKit computations do not give the model tool access. Responses are preserved verbatim, including malformed or token-limited output. Reported finish reason and token usage are retained. No response repair or answer extraction occurs before scoring.

## Coverage

Full evaluations use all 60 tasks. Smoke selection uses seeded category round-robin sampling, with exact IDs recorded in provenance. The default five-task smoke run cannot cover all six domains and produces no aggregate, interval or ranking entry. A sample is ineligible even if its size happens to equal the complete benchmark.

A transport interruption leaves a partial run. Completed checkpoints remain available; resume rejects changes to benchmark, model, runtime, generation settings, selected tasks or evaluator software. Failed and smoke runs cannot participate in full-benchmark paired comparisons.

## ZIP contents

| File | Contents |
|---|---|
| `run.json` | Identity, status, timestamps, scope, model metadata, provenance, summary and result label |
| `config.json` | Effective evaluation configuration |
| `summary.json` | Aggregate and usage, or null for an unfinished run; smoke aggregates are null |
| `responses.jsonl` | Task ID, verbatim response and observed usage |
| `scores.csv` | Task/category/cluster IDs and scoring metrics |
| `validations.jsonl` | Parsing, field, citation and chemical diagnostics |
| `manifest.json` | Run status, captured task count and SHA-256 of every other file |

Archives contain public run data only. Export checksums identify file integrity, not external authorship or scientific certification. The workflow additionally retains its database and execution logs so partial checkpoints can be recovered after infrastructure failures.

Mock fixtures are labeled **DEMONSTRATION DATA**. Real inference is labeled **EXPERIMENTAL MODEL RESULTS**. Smoke runs are explicitly non-ranking. All modes retain the benchmark's synthetic-data, contamination and review limitations.
