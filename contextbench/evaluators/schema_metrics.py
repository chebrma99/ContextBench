from __future__ import annotations

from contextbench.core.models import PredictionRecord


def compute_schema_metrics(predictions: list[PredictionRecord]) -> dict[str, float | int]:
    total = len(predictions)
    valid_json_count = sum(1 for item in predictions if item.valid_json)
    schema_valid_count = sum(1 for item in predictions if item.schema_valid)
    schema_failure_count = total - schema_valid_count
    return {
        "total_outputs": total,
        "valid_json_count": valid_json_count,
        "schema_valid_count": schema_valid_count,
        "schema_failure_count": schema_failure_count,
        "schema_failure_rate": schema_failure_count / total if total else 0.0,
    }
