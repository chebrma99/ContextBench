from __future__ import annotations

from contextbench.core.models import GoldLabel, PredictionRecord


def compute_classification_metrics(
    predictions: list[PredictionRecord], gold: dict[str, GoldLabel]
) -> dict[str, float]:
    comparable = [prediction for prediction in predictions if prediction.schema_valid and prediction.task_id in gold]
    total = len(comparable)
    if total == 0:
        return {
            "category_accuracy": 0.0,
            "priority_accuracy": 0.0,
            "customer_impact_accuracy": 0.0,
            "customer_impact_precision": 0.0,
            "customer_impact_recall": 0.0,
            "customer_impact_f1": 0.0,
            "human_review_accuracy": 0.0,
        }

    category_correct = sum(1 for item in comparable if item.category == gold[item.task_id].gold_category)
    priority_correct = sum(1 for item in comparable if item.priority == gold[item.task_id].gold_priority)
    impact_correct = sum(1 for item in comparable if item.customer_impact == gold[item.task_id].gold_customer_impact)
    review_correct = sum(
        1 for item in comparable if item.requires_human_review == gold[item.task_id].requires_human_review
    )

    true_positive = sum(
        1 for item in comparable if item.customer_impact is True and gold[item.task_id].gold_customer_impact is True
    )
    false_positive = sum(
        1 for item in comparable if item.customer_impact is True and gold[item.task_id].gold_customer_impact is False
    )
    false_negative = sum(
        1 for item in comparable if item.customer_impact is False and gold[item.task_id].gold_customer_impact is True
    )

    precision = _safe_div(true_positive, true_positive + false_positive)
    recall = _safe_div(true_positive, true_positive + false_negative)
    f1 = _safe_div(2 * precision * recall, precision + recall)

    return {
        "category_accuracy": category_correct / total,
        "priority_accuracy": priority_correct / total,
        "customer_impact_accuracy": impact_correct / total,
        "customer_impact_precision": precision,
        "customer_impact_recall": recall,
        "customer_impact_f1": f1,
        "human_review_accuracy": review_correct / total,
    }


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
