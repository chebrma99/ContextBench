from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


ALLOWED_CATEGORIES = {
    "Customer UI Issue",
    "Pipeline Blocked",
    "Data / Metrics Issue",
    "Performance Issue",
    "Dependency Failure",
    "Deployment Issue",
    "Auth / Access Issue",
    "Other",
}

ALLOWED_PRIORITIES = {"Critical", "High", "Medium", "Low"}


class Condition(str, Enum):
    C0_PROMPT_ONLY = "C0_PROMPT_ONLY"
    C1_RAG_ONLY = "C1_RAG_ONLY"
    C2_STEERING_ONLY = "C2_STEERING_ONLY"
    C3_MEMORY_ONLY = "C3_MEMORY_ONLY"
    C4_RAG_STEERING = "C4_RAG_STEERING"
    C5_RAG_STEERING_MEMORY = "C5_RAG_STEERING_MEMORY"

    @property
    def uses_rag(self) -> bool:
        return self in {
            Condition.C1_RAG_ONLY,
            Condition.C4_RAG_STEERING,
            Condition.C5_RAG_STEERING_MEMORY,
        }

    @property
    def uses_steering(self) -> bool:
        return self in {
            Condition.C2_STEERING_ONLY,
            Condition.C4_RAG_STEERING,
            Condition.C5_RAG_STEERING_MEMORY,
        }

    @property
    def uses_memory(self) -> bool:
        return self in {
            Condition.C3_MEMORY_ONLY,
            Condition.C5_RAG_STEERING_MEMORY,
        }


@dataclass(frozen=True)
class TicketTask:
    task_id: str
    source: str
    title: str
    description: str
    labels: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "TicketTask":
        return cls(
            task_id=str(row["task_id"]),
            source=str(row.get("source", "")),
            title=str(row["title"]),
            description=str(row["description"]),
            labels=[str(label) for label in row.get("labels", [])],
            metadata=dict(row.get("metadata", {})),
        )


@dataclass(frozen=True)
class GoldLabel:
    task_id: str
    gold_category: str
    gold_customer_impact: bool
    gold_priority: str
    requires_human_review: bool


@dataclass(frozen=True)
class ContextDocument:
    doc_id: str
    text: str
    source_path: Path


@dataclass
class ValidationResult:
    valid_json: bool
    schema_valid: bool
    output: dict[str, Any] | None
    errors: list[str]


@dataclass
class PredictionRecord:
    run_id: str
    condition: str
    task_id: str
    category: str | None
    customer_impact: bool | None
    priority: str | None
    requires_human_review: bool | None
    confidence: float | None
    reason: str | None
    evidence_ids: list[str]
    valid_json: bool
    schema_valid: bool
    schema_errors: list[str]
    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    provider_error: str | None = None
    raw_response: str | None = None


@dataclass
class ProviderResponse:
    output: dict[str, Any] | str
    raw_response: str | None = None
    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    provider_error: str | None = None


@dataclass(frozen=True)
class BenchmarkPaths:
    tasks_path: Path
    gold_path: Path
    output_root: Path
    project_root: Path
