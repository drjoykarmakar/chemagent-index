"""GitHub Actions job summary from captured evaluation artifacts."""

import json
import os
import zipfile
from pathlib import Path

lines = ["# ChemAgent Index evaluation", ""]
archives = sorted(Path("results").glob("*.zip"))
if not archives:
    lines.append(
        "No evaluation artifact was produced. Runtime logs are available in the job artifact."
    )
for path in archives:
    with zipfile.ZipFile(path) as archive:
        run = json.loads(archive.read("run.json"))
        manifest = json.loads(archive.read("manifest.json"))
    lines.extend(
        [
            f"**{run['notice']}**",
            "",
            f"Run: `{run['id']}` · Status: **{run['status']}** · Tasks captured: **{manifest['task_count']}**",
            f"Model: `{run['model_id']}`",
            "",
        ]
    )
    summary = run["summary"]
    if summary and summary.get("score"):
        lines.append(f"Starter score: **{summary['score']['mean']:.2f} / 100**")
    lines.append(
        "Artifacts contain raw responses, validation details, scores, configuration, provenance and file checksums."
    )
    lines.append(
        "Results use public synthetic tasks pending expert review. Compute costs are not measured."
    )
Path(os.environ["GITHUB_STEP_SUMMARY"]).write_text("\n".join(lines) + "\n")
