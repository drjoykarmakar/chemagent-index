"""Strict benchmark contract. Private answers never enter provider requests."""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Category = Literal[
    "chemistry_reasoning",
    "medicinal_chemistry",
    "molecular_validation",
    "synthesis_reasoning",
    "literature_reliability",
    "stress_tests",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Provenance(StrictModel):
    source: str
    license: str
    citation: str | None
    DOI: str | None
    original_dataset: str | None
    curation_method: str
    curator: str
    date_added: date
    validation_status: Literal["draft", "machine_checked", "expert_reviewed"]
    synthetic: bool


class RubricField(StrictModel):
    kind: Literal["number", "string", "boolean", "list"]
    weight: float = Field(default=1, gt=0)
    severity: float = Field(default=1, gt=0)
    tolerance: float = Field(default=0.001, gt=0)


class Task(StrictModel):
    task_id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,80}$")
    category: Category
    cluster_id: str
    difficulty: Literal["introductory", "intermediate", "advanced", "expert"]
    prompt: str = Field(min_length=20)
    inputs: dict[str, Any]
    expected_output_schema: dict[str, Any]
    reference_answer: dict[str, Any]
    rubric: dict[str, RubricField]
    provenance: Provenance
    publication_date: date
    known_public_source: bool
    training_data_risk: Literal["low", "medium", "high", "unknown"]
    contamination_risk: Literal["low", "medium", "high", "unknown"]
    review_status: Literal["pending_expert", "reviewed"]
    validity_status: Literal["machine_checked", "expert_checked"]
    evaluation_method: str
    known_ambiguity: str
    visibility: Literal["public", "private"] = "public"
    allowed_citations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def coherent_rubric(self) -> "Task":
        if not self.rubric or set(self.rubric) != set(self.reference_answer):
            raise ValueError("Reference fields and rubric fields must match exactly")
        for key, rule in self.rubric.items():
            value = self.reference_answer[key]
            valid = {
                "number": type(value) in (int, float),
                "string": type(value) is str,
                "boolean": type(value) is bool,
                "list": type(value) is list,
            }[rule.kind]
            if not valid:
                raise ValueError(f"Reference type mismatch: {key}")
        return self


class Answer(StrictModel):
    answer: dict[str, Any]
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    citations: list[str] = Field(max_length=100)
    reasoning_summary: str = Field(max_length=4000)
    uncertainties: list[str] = Field(max_length=100)
