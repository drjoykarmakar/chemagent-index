"""Validated configuration and reproducible hashing."""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT = Path(os.environ.get("CHEMAGENT_ROOT", Path(__file__).resolve().parents[1]))


def digest(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


class EvaluationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str = "demo-agent"
    benchmark: str = "chemagentbench-v0.1"
    seed: int = 2026
    temperature: float = Field(default=0, ge=0, le=2)
    max_tokens: int = Field(default=2048, ge=1, le=100000)
    tools: list[str] = Field(default_factory=lambda: ["rdkit"])
    track: Literal["model_only", "model_plus_tools", "agentic_system"] = "model_plus_tools"
    timeout: float = Field(default=30, gt=0, le=300)
    retries: int = Field(default=2, ge=0, le=5)
    provider: Literal["mock", "ollama"] = "mock"
    sample_size: int | None = Field(default=None, ge=1)
    ollama_model: str = "qwen2.5:0.5b"
    ollama_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    context_window: int = Field(default=4096, ge=1024, le=32768)
    cpu_threads: int = Field(default=2, ge=1, le=64)

    @model_validator(mode="after")
    def validate_tools(self) -> "EvaluationConfig":
        if self.track == "model_only" and self.tools:
            raise ValueError("model_only track cannot permit tools")
        if self.provider == "ollama" and (self.track != "model_only" or self.tools):
            raise ValueError("Ollama evaluations require the model_only track without tools")
        if self.provider == "ollama" and not self.ollama_digest:
            raise ValueError("Ollama evaluations require a pinned model digest")
        return self


def load_config(path: Path | None = None) -> EvaluationConfig:
    return EvaluationConfig.model_validate(
        yaml.safe_load((path or ROOT / "configs/evaluation.yaml").read_text())
    )


def load_policy() -> dict[str, Any]:
    policy = yaml.safe_load((ROOT / "configs/scoring.yaml").read_text())
    if not policy["weights"] or any(v <= 0 for v in policy["weights"].values()):
        raise ValueError("Category weights must be positive")
    r = policy["reliability"]
    if abs(r["error_weight"] + r["calibration_weight"] - 1) > 1e-9:
        raise ValueError("Reliability weights must sum to one")
    return dict(policy)
