from __future__ import annotations

from contextbench.core.models import PredictionRecord


def compute_instruction_following_metrics(predictions: list[PredictionRecord]) -> dict[str, float]:
    total = len(predictions)
    json_only_success = sum(1 for prediction in predictions if prediction.valid_json)
    schema_success = sum(1 for prediction in predictions if prediction.schema_valid)
    return {
        "json_only_success_rate": json_only_success / total if total else 0.0,
        "schema_instruction_success_rate": schema_success / total if total else 0.0,
    }
