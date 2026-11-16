"""Digest-checked local inference with Ollama's structured-output API."""

import json
import os
from typing import Any

import httpx

from chemagent.config import EvaluationConfig
from chemagent.providers.base import ProviderResponse, PublicRequest

SYSTEM_PROMPT = (
    "Answer the chemistry task using only the supplied inputs. Return one JSON object "
    "matching the output schema. Include a brief answer summary, confidence from 0 to 1, "
    "citations (empty when no source is supplied), and uncertainties. No markdown."
)


class OllamaAdapter:
    def __init__(self, config: EvaluationConfig, *, client: httpx.Client | None = None):
        if config.provider != "ollama" or not config.ollama_digest:
            raise ValueError("A pinned Ollama configuration is required")
        self.config = config.model_copy(deep=True)
        self.client = client or httpx.Client(
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            trust_env=False,
            follow_redirects=False,
        )
        self._metadata: dict[str, Any] | None = None

    def close(self) -> None:
        self.client.close()

    def _request(
        self, method: str, path: str, timeout: float, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            response = self.client.request(method, path, json=payload, timeout=timeout)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise TimeoutError("Ollama request timed out") from exc
        except httpx.TransportError as exc:
            raise ConnectionError("Ollama transport failed") from exc
        if len(response.content) > 2_000_000:
            raise ValueError("Ollama response exceeds transport limit")
        data = response.json()
        if not isinstance(data, dict) or data.get("error"):
            raise ValueError("Ollama returned an invalid response")
        return data

    def _verify_model(self, timeout: float) -> dict[str, Any]:
        models = self._request("GET", "/api/tags", timeout).get("models", [])
        model = next((m for m in models if m.get("name") == self.config.ollama_model), None)
        if model is None:
            raise ValueError("Configured Ollama model is not installed")
        if model.get("digest", "").removeprefix("sha256:") != self.config.ollama_digest:
            raise ValueError("Installed Ollama model digest differs from the pinned configuration")
        return dict(model)

    def metadata(self) -> dict[str, Any]:
        if self._metadata is None:
            model = self._verify_model(10)
            version = self._request("GET", "/api/version", 10).get("version")
            if not isinstance(version, str) or not version:
                raise ValueError("Ollama runtime version is unavailable")
            self._metadata = {
                "model_id": self.config.model,
                "display_name": self.config.ollama_model,
                "organization": "Qwen"
                if self.config.ollama_model.startswith("qwen")
                else "Unspecified",
                "provider": "ollama",
                "model_version": self.config.ollama_digest,
                "model_tag": self.config.ollama_model,
                "details": model.get("details", {}),
                "demo": False,
                "system_type": "foundation_model",
                "access_type": "local",
                "open_source": self.config.ollama_model == "qwen2.5:0.5b",
                "commercial": False,
                "required_tools": [],
                "protocol": {"name": "ollama-structured-v1", "runtime_version": version},
                "generation": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                    "num_ctx": self.config.context_window,
                    "num_thread": self.config.cpu_threads,
                },
                "system_prompt": SYSTEM_PROMPT,
                "cost_note": "Hosting and compute costs are not measured.",
            }
        return dict(self._metadata)

    def generate(self, request: PublicRequest, *, seed: int, timeout: float) -> ProviderResponse:
        self._verify_model(min(timeout, 10))
        payload = {
            "model": self.config.ollama_model,
            "system": SYSTEM_PROMPT,
            "prompt": json.dumps(
                {
                    "task": request.prompt,
                    "inputs": request.inputs,
                    "output_schema": request.output_schema,
                },
                sort_keys=True,
            ),
            "format": request.output_schema,
            "stream": False,
            "keep_alive": "10m",
            "options": {**self.metadata()["generation"], "seed": seed},
        }
        data = self._request("POST", "/api/generate", timeout, payload)
        if data.get("done") is not True or not isinstance(data.get("response"), str):
            raise ValueError("Ollama did not return a completed response")
        # Preserve invalid/truncated JSON verbatim; the scorer decides its credit.
        return ProviderResponse(
            text=data["response"],
            input_tokens=self._tokens(data.get("prompt_eval_count")),
            output_tokens=self._tokens(data.get("eval_count")),
            finish_reason=data.get("done_reason"),
        )

    @staticmethod
    def _tokens(value: Any) -> int | None:
        return value if type(value) is int and value >= 0 else None

    def generate_structured(
        self, request: PublicRequest, *, seed: int, timeout: float
    ) -> ProviderResponse:
        return self.generate(request, seed=seed, timeout=timeout)

    def health_check(self) -> bool:
        try:
            self.metadata()
            return True
        except (httpx.HTTPError, ConnectionError, TimeoutError, ValueError):
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> None:
        return None
