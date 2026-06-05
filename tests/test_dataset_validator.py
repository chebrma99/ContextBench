import csv
import json
import shutil
from pathlib import Path

import pytest

from contextbench.core.dataset_validator import validate_ticket_triage_dataset


def test_dataset_validation_passes_for_50_task_dataset() -> None:
    project_root = Path(__file__).resolve().parents[1]
    report = validate_ticket_triage_dataset(
        project_root / "datasets" / "ticket_triage" / "tasks.jsonl",
        project_root / "datasets" / "ticket_triage" / "gold_labels.csv",
    )

    assert report.task_count == 50
    assert report.category_distribution["Customer UI Issue"] == 7
    assert report.priority_distribution["Medium"] >= 20


def test_dataset_validation_fails_on_invalid_category() -> None:
    project_root = Path(__file__).resolve().parents[1]
    test_root = _fresh_test_dir(project_root / ".test_runs" / "invalid_category")
    tasks_path = test_root / "tasks.jsonl"
    gold_path = test_root / "gold_labels.csv"
    shutil.copyfile(project_root / "datasets" / "ticket_triage" / "tasks.jsonl", tasks_path)
    _copy_gold_with_override(
        project_root / "datasets" / "ticket_triage" / "gold_labels.csv",
        gold_path,
        "TICKET-001",
        {"gold_category": "Invalid Category"},
    )

    with pytest.raises(ValueError, match="invalid gold_category"):
        validate_ticket_triage_dataset(tasks_path, gold_path)


def test_dataset_validation_fails_on_duplicate_task_id() -> None:
    project_root = Path(__file__).resolve().parents[1]
    test_root = _fresh_test_dir(project_root / ".test_runs" / "duplicate_task_id")
    tasks_path = test_root / "tasks.jsonl"
    gold_path = test_root / "gold_labels.csv"
    shutil.copyfile(project_root / "datasets" / "ticket_triage" / "gold_labels.csv", gold_path)

    rows = []
    for line in (project_root / "datasets" / "ticket_triage" / "tasks.jsonl").read_text(encoding="utf-8").splitlines():
        rows.append(json.loads(line))
    rows[0]["task_id"] = "TICKET-002"
    tasks_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate task_id"):
        validate_ticket_triage_dataset(tasks_path, gold_path)


def _fresh_test_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def _copy_gold_with_override(source: Path, destination: Path, task_id: str, updates: dict[str, str]) -> None:
    with source.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = handle.readline()
    if not rows:
        raise AssertionError("Expected gold labels fixture rows")
    for row in rows:
        if row["task_id"] == task_id:
            row.update(updates)

    fields = ["task_id", "gold_category", "gold_customer_impact", "gold_priority", "requires_human_review"]
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
