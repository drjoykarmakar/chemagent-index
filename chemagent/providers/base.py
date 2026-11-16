"""Provider boundary: strictly public prompt data, never reference answers."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from chemagent.benchmarks.schema import Task


@dataclass(frozen=True)
class PublicRequest:
    task_id: str
    prompt: str
    inputs: dict[str, Any]
    output_schema: dict[str, Any]

    @classmethod
    def from_task(cls, task: Task) -> "PublicRequest":
        return cls(task.task_id, task.prompt, task.inputs, task.expected_output_schema)


@dataclass
class ProviderResponse:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    tool_calls: list[str] = field(default_factory=list)
    finish_reason: str | None = None


class BaseModelAdapter(Protocol):
    def generate(
        self, request: PublicRequest, *, seed: int, timeout: float
    ) -> ProviderResponse: ...
    def generate_structured(
        self, request: PublicRequest, *, seed: int, timeout: float
    ) -> ProviderResponse: ...
    def health_check(self) -> bool: ...
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float | None: ...
    def metadata(self) -> dict[str, Any]: ...
