from __future__ import annotations

from contextbench.core.models import PredictionRecord


def compute_context_reliability_metrics(
    predictions: list[PredictionRecord],
    allowed_evidence_by_task: dict[str, set[str]],
    rag_used: bool,
    low_confidence_threshold: float = 0.6,
) -> dict[str, float | int]:
    total = len(predictions)
    schema_valid = [prediction for prediction in predictions if prediction.schema_valid]
    unsupported = 0
    evidence_present = 0

    for prediction in schema_valid:
        allowed = allowed_evidence_by_task.get(prediction.task_id, set())
        if prediction.evidence_ids:
            evidence_present += 1
        unsupported += sum(1 for evidence_id in prediction.evidence_ids if evidence_id not in allowed)

    low_confidence = sum(
        1
        for prediction in schema_valid
        if prediction.confidence is not None and prediction.confidence < low_confidence_threshold
    )
    human_review = sum(1 for prediction in schema_valid if prediction.requires_human_review is True)

    denominator = len(schema_valid)
    return {
        "evidence_coverage": evidence_present / denominator if rag_used and denominator else 0.0,
        "unsupported_evidence_count": unsupported,
        "low_confidence_rate": low_confidence / denominator if denominator else 0.0,
        "human_review_burden": human_review / denominator if denominator else 0.0,
        "context_reliability_total": total,
    }
