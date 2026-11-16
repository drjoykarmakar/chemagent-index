"""Named extension points; no untested commercial API implementation is implied."""

from typing import Any

from chemagent.providers.base import ProviderResponse, PublicRequest


class UnconfiguredAdapter:
    provider = "unconfigured"

    def generate(self, request: PublicRequest, *, seed: int, timeout: float) -> ProviderResponse:
        raise NotImplementedError(f"{self.provider} adapter is a Phase 2 extension point")

    generate_structured = generate

    def health_check(self) -> bool:
        return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> None:
        return None

    def metadata(self) -> dict[str, Any]:
        return {"provider": self.provider, "implemented": False}


class OpenAIAdapter(UnconfiguredAdapter):
    provider = "openai"


class AnthropicAdapter(UnconfiguredAdapter):
    provider = "anthropic"


class GeminiAdapter(UnconfiguredAdapter):
    provider = "gemini"


class OpenRouterAdapter(UnconfiguredAdapter):
    provider = "openrouter"


class LocalModelAdapter(UnconfiguredAdapter):
    provider = "local"
