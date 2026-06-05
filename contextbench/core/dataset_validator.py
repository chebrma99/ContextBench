from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from contextbench.core.models import ALLOWED_CATEGORIES, ALLOWED_PRIORITIES, GoldLabel, TicketTask
from contextbench.core.runner import load_gold_labels, load_tasks


EXPECTED_TASK_COUNT = 50
CATEGORY_MINIMUMS = {
    "Customer UI Issue": 7,
    "Pipeline Blocked": 6,
    "Data / Metrics Issue": 6,
    "Performance Issue": 6,
    "Dependency Failure": 6,
    "Deployment Issue": 6,
    "Auth / Access Issue": 6,
    "Other": 5,
}
PRIORITY_MINIMUMS = {"Critical": 5, "High": 12, "Medium": 20, "Low": 8}
CUSTOMER_IMPACT_MINIMUMS = {"true": 20, "false": 20}
HUMAN_REVIEW_MINIMUMS = {"true": 12, "false": 30}


@dataclass(frozen=True)
class DatasetValidationReport:
    task_count: int
    category_distribution: dict[str, int]
    priority_distribution: dict[str, int]
    customer_impact_distribution: dict[str, int]
    human_review_distribution: dict[str, int]


def validate_ticket_triage_dataset(
    tasks_path: Path,
    gold_path: Path,
    expected_count: int = EXPECTED_TASK_COUNT,
) -> DatasetValidationReport:
    tasks = load_tasks(tasks_path)
    gold = load_gold_labels(gold_path)
    errors = _dataset_errors(tasks, gold, expected_count)
    if errors:
        raise ValueError("Dataset validation failed:\n- " + "\n- ".join(errors))
    return summarize_dataset(tasks, gold)


def summarize_dataset(tasks: list[TicketTask], gold: dict[str, GoldLabel]) -> DatasetValidationReport:
    task_ids = [task.task_id for task in tasks]
    labels = [gold[task_id] for task_id in task_ids if task_id in gold]
    return DatasetValidationReport(
        task_count=len(tasks),
        category_distribution=dict(Counter(label.gold_category for label in labels)),
        priority_distribution=dict(Counter(label.gold_priority for label in labels)),
        customer_impact_distribution=dict(Counter(str(label.gold_customer_impact).lower() for label in labels)),
        human_review_distribution=dict(Counter(str(label.requires_human_review).lower() for label in labels)),
    )


def format_validation_report(report: DatasetValidationReport) -> str:
    lines = [
        f"Task count: {report.task_count}",
        "Category distribution:",
        *_format_distribution(report.category_distribution),
        "Priority distribution:",
        *_format_distribution(report.priority_distribution),
        "Customer impact distribution:",
        *_format_distribution(report.customer_impact_distribution),
        "Human review distribution:",
        *_format_distribution(report.human_review_distribution),
    ]
    return "\n".join(lines)


def _dataset_errors(tasks: list[TicketTask], gold: dict[str, GoldLabel], expected_count: int) -> list[str]:
    errors: list[str] = []
    task_ids = [task.task_id for task in tasks]
    task_id_counts = Counter(task_ids)
    duplicate_ids = sorted(task_id for task_id, count in task_id_counts.items() if count > 1)
    task_id_set = set(task_ids)
    gold_id_set = set(gold)

    if len(tasks) != expected_count:
        errors.append(f"Expected exactly {expected_count} tasks, found {len(tasks)}")
    if duplicate_ids:
        errors.append(f"Duplicate task_id values: {', '.join(duplicate_ids)}")

    missing_gold = sorted(task_id_set - gold_id_set)
    extra_gold = sorted(gold_id_set - task_id_set)
    if missing_gold:
        errors.append(f"Tasks missing gold labels: {', '.join(missing_gold)}")
    if extra_gold:
        errors.append(f"Gold labels without tasks: {', '.join(extra_gold)}")

    for label in gold.values():
        if label.gold_category not in ALLOWED_CATEGORIES:
            errors.append(f"{label.task_id}: invalid gold_category {label.gold_category!r}")
        if label.gold_priority not in ALLOWED_PRIORITIES:
            errors.append(f"{label.task_id}: invalid gold_priority {label.gold_priority!r}")
        if not isinstance(label.gold_customer_impact, bool):
            errors.append(f"{label.task_id}: gold_customer_impact must be boolean-compatible")
        if not isinstance(label.requires_human_review, bool):
            errors.append(f"{label.task_id}: requires_human_review must be boolean-compatible")

    if not errors:
        report = summarize_dataset(tasks, gold)
        errors.extend(_minimum_errors("category", report.category_distribution, CATEGORY_MINIMUMS))
        errors.extend(_minimum_errors("priority", report.priority_distribution, PRIORITY_MINIMUMS))
        errors.extend(_minimum_errors("customer impact", report.customer_impact_distribution, CUSTOMER_IMPACT_MINIMUMS))
        errors.extend(_minimum_errors("human review", report.human_review_distribution, HUMAN_REVIEW_MINIMUMS))

    return errors


def _format_distribution(distribution: dict[str, int]) -> list[str]:
    return [f"- {key}: {value}" for key, value in sorted(distribution.items())]


def _minimum_errors(name: str, actual: dict[str, int], minimums: dict[str, int]) -> list[str]:
    errors: list[str] = []
    for key, minimum in minimums.items():
        count = actual.get(key, 0)
        if count < minimum:
            errors.append(f"{name} distribution requires at least {minimum} {key!r}, found {count}")
    return errors
