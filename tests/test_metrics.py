from contextbench.core.models import GoldLabel, PredictionRecord
from contextbench.evaluators.classification_metrics import compute_classification_metrics


def test_classification_metrics_compute_accuracy_and_f1() -> None:
    predictions = [
        PredictionRecord(
            run_id="run",
            condition="C0_PROMPT_ONLY",
            task_id="T1",
            category="Customer UI Issue",
            customer_impact=True,
            priority="High",
            requires_human_review=False,
            confidence=0.9,
            reason="reason",
            evidence_ids=[],
            valid_json=True,
            schema_valid=True,
            schema_errors=[],
        ),
        PredictionRecord(
            run_id="run",
            condition="C0_PROMPT_ONLY",
            task_id="T2",
            category="Other",
            customer_impact=False,
            priority="Low",
            requires_human_review=False,
            confidence=0.7,
            reason="reason",
            evidence_ids=[],
            valid_json=True,
            schema_valid=True,
            schema_errors=[],
        ),
    ]
    gold = {
        "T1": GoldLabel("T1", "Customer UI Issue", True, "High", False),
        "T2": GoldLabel("T2", "Other", False, "Medium", True),
    }

    metrics = compute_classification_metrics(predictions, gold)

    assert metrics["category_accuracy"] == 1.0
    assert metrics["priority_accuracy"] == 0.5
    assert metrics["customer_impact_f1"] == 1.0
    assert metrics["human_review_accuracy"] == 0.5
