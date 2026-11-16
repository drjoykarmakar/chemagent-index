"""Guard public release data; not a substitute for repository secret scanning."""

from chemagent.benchmarks.store import public_store

manifest, tasks, _ = public_store("chemagentbench-v0.1").load()
assert manifest["private_samples"] == 0
assert all(t.visibility == "public" for t in tasks)
assert all(t.provenance.synthetic and t.provenance.license == "CC0-1.0" for t in tasks)
assert all(t.provenance.DOI is None for t in tasks)
print(
    "Public-data check passed: 60 original synthetic tasks; no hidden data or asserted citations."
)
