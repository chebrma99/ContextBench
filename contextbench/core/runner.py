from __future__ import annotations

import csv
import json
import platform
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from contextbench import __version__
from contextbench.core.context_assembler import ContextAssembler
from contextbench.core.models import BenchmarkPaths, Condition, GoldLabel, PredictionRecord, ProviderResponse, TicketTask
from contextbench.core.schema_validator import parse_provider_output
from contextbench.evaluators import (
    compute_classification_metrics,
    compute_context_reliability_metrics,
    compute_instruction_following_metrics,
    compute_schema_metrics,
)
from contextbench.providers.base import BaseProvider


def run_condition(
    condition: Condition,
    provider: BaseProvider,
    paths: BenchmarkPaths,
    run_id: str | None = None,
    run_dir: Path | None = None,
    limit: int | None = None,
    write_aggregate_outputs: bool = True,
) -> tuple[list[PredictionRecord], dict[str, Any]]:
    tasks = _apply_limit(load_tasks(paths.tasks_path), limit)
    gold = load_gold_labels(paths.gold_path)
    assembler = ContextAssembler(paths.project_root)
    run_id = run_id or _timestamp()
    run_dir = run_dir or paths.output_root / f"run_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    predictions: list[PredictionRecord] = []
    allowed_evidence_by_task: dict[str, set[str]] = {}

    for task in tasks:
        prompt, documents = assembler.assemble(task, condition)
        _write_prompt(run_dir, condition, task, prompt)
        allowed_evidence_by_task[task.task_id] = assembler.allowed_evidence_ids(documents)
        predictions.append(_classify_task(run_id, condition, task, prompt, provider))

    metrics = compute_metrics(predictions, gold, allowed_evidence_by_task, condition.uses_rag)
    write_run_outputs(run_dir, predictions, metrics)

    if write_aggregate_outputs:
        tasks_by_id = {task.task_id: task for task in tasks}
        write_predictions_csv(run_dir / "predictions.csv", predictions)
        write_metrics_json(run_dir / "metrics.json", {"run_id": run_id, "conditions": {condition.value: metrics}})
        write_condition_summary_csv(run_dir / "condition_summary.csv", [{"condition": condition.value, **_summary_metrics(metrics)}])
        write_errors_csv(run_dir / "errors.csv", predictions)
        write_error_analysis_csv(run_dir / "error_analysis.csv", predictions, gold, tasks_by_id)
        write_run_config(run_dir, provider, [condition], len(tasks), limit)
        write_paper_results_summary(
            run_dir,
            provider,
            tasks,
            gold,
            [{"condition": condition.value, **_summary_metrics(metrics)}],
        )

    return predictions, metrics


def run_all_conditions(
    provider: BaseProvider,
    paths: BenchmarkPaths,
    limit: int | None = None,
) -> tuple[Path, list[dict[str, Any]]]:
    run_id = _timestamp()
    run_dir = paths.output_root / f"run_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    tasks = _apply_limit(load_tasks(paths.tasks_path), limit)
    gold = load_gold_labels(paths.gold_path)
    all_predictions: list[PredictionRecord] = []
    summaries: list[dict[str, Any]] = []
    metrics_by_condition: dict[str, Any] = {}

    for condition in Condition:
        predictions, metrics = run_condition(
            condition,
            provider,
            paths,
            run_id=run_id,
            run_dir=run_dir,
            limit=limit,
            write_aggregate_outputs=False,
        )
        all_predictions.extend(predictions)
        summary = {"condition": condition.value, **_summary_metrics(metrics)}
        summaries.append(summary)
        metrics_by_condition[condition.value] = metrics

    tasks_by_id = {task.task_id: task for task in tasks}
    write_predictions_csv(run_dir / "predictions.csv", all_predictions)
    write_metrics_json(run_dir / "metrics.json", {"run_id": run_id, "conditions": metrics_by_condition})
    write_condition_summary_csv(run_dir / "condition_summary.csv", summaries)
    write_errors_csv(run_dir / "errors.csv", all_predictions)
    write_error_analysis_csv(run_dir / "error_analysis.csv", all_predictions, gold, tasks_by_id)
    write_run_config(run_dir, provider, list(Condition), len(tasks), limit)
    write_paper_results_summary(run_dir, provider, tasks, gold, summaries)
    return run_dir, summaries


def compare_runs(run_a: Path, run_b: Path) -> Path:
    metrics_a = _load_run_metrics(run_a)
    metrics_b = _load_run_metrics(run_b)
    rows: list[dict[str, Any]] = []

    for condition in sorted(set(metrics_a) | set(metrics_b)):
        flat_a = _flatten_metrics(metrics_a.get(condition, {}))
        flat_b = _flatten_metrics(metrics_b.get(condition, {}))
        for metric in sorted(set(flat_a) | set(flat_b)):
            value_a = flat_a.get(metric)
            value_b = flat_b.get(metric)
            rows.append(
                {
                    "condition": condition,
                    "metric": metric,
                    "run_a_value": value_a,
                    "run_b_value": value_b,
                    "difference": _difference(value_a, value_b),
                }
            )

    output_path = run_b / "comparison_report.csv"
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["condition", "metric", "run_a_value", "run_b_value", "difference"]
        )
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def compute_metrics(
    predictions: list[PredictionRecord],
    gold: dict[str, GoldLabel],
    allowed_evidence_by_task: dict[str, set[str]],
    rag_used: bool,
) -> dict[str, Any]:
    operational = _operational_metrics(predictions)
    return {
        "classification": compute_classification_metrics(predictions, gold),
        "schema": compute_schema_metrics(predictions),
        "context_reliability": compute_context_reliability_metrics(predictions, allowed_evidence_by_task, rag_used),
        "instruction_following": compute_instruction_following_metrics(predictions),
        "operational": operational,
    }


def load_tasks(path: Path) -> list[TicketTask]:
    if not path.exists():
        raise FileNotFoundError(f"Tasks file not found: {path}")
    tasks: list[TicketTask] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    tasks.append(TicketTask.from_dict(json.loads(line)))
                except (KeyError, json.JSONDecodeError, TypeError) as exc:
                    raise ValueError(f"Invalid task row at {path}:{line_number}: {exc}") from exc
    return tasks


def load_gold_labels(path: Path) -> dict[str, GoldLabel]:
    if not path.exists():
        raise FileNotFoundError(f"Gold labels file not found: {path}")
    labels: dict[str, GoldLabel] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            task_id = row["task_id"]
            labels[task_id] = GoldLabel(
                task_id=task_id,
                gold_category=row["gold_category"],
                gold_customer_impact=_parse_bool(row["gold_customer_impact"]),
                gold_priority=row["gold_priority"],
                requires_human_review=_parse_bool(row["requires_human_review"]),
            )
    return labels


def write_run_outputs(run_dir: Path, predictions: list[PredictionRecord], metrics: dict[str, Any]) -> None:
    condition = predictions[0].condition if predictions else "unknown"
    write_predictions_csv(run_dir / f"predictions_{condition}.csv", predictions)
    write_metrics_json(run_dir / f"metrics_{condition}.json", metrics)
    write_errors_csv(run_dir / f"errors_{condition}.csv", predictions)


def write_predictions_csv(path: Path, predictions: list[PredictionRecord]) -> None:
    fieldnames = [
        "run_id",
        "condition",
        "task_id",
        "category",
        "customer_impact",
        "priority",
        "requires_human_review",
        "confidence",
        "reason",
        "evidence_ids",
        "valid_json",
        "schema_valid",
        "schema_errors",
        "latency_ms",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "provider_error",
        "raw_response",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for prediction in predictions:
            row = prediction.__dict__.copy()
            row["evidence_ids"] = json.dumps(prediction.evidence_ids)
            row["schema_errors"] = json.dumps(prediction.schema_errors)
            writer.writerow(row)


def write_metrics_json(path: Path, metrics: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, sort_keys=True)


def write_condition_summary_csv(path: Path, summaries: list[dict[str, Any]]) -> None:
    if not summaries:
        return
    fieldnames = [
        "condition",
        "total_tasks",
        "category_accuracy",
        "priority_accuracy",
        "customer_impact_accuracy",
        "customer_impact_precision",
        "customer_impact_recall",
        "customer_impact_f1",
        "human_review_accuracy",
        "schema_valid_rate",
        "evidence_coverage",
        "unsupported_evidence_count",
        "low_confidence_rate",
        "human_review_burden",
        "avg_confidence",
        "avg_latency_ms",
        "total_tokens",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summaries)


def write_errors_csv(path: Path, predictions: list[PredictionRecord]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["run_id", "condition", "task_id", "provider_error", "errors"])
        writer.writeheader()
        for prediction in predictions:
            if prediction.schema_errors or prediction.provider_error:
                writer.writerow(
                    {
                        "run_id": prediction.run_id,
                        "condition": prediction.condition,
                        "task_id": prediction.task_id,
                        "provider_error": prediction.provider_error,
                        "errors": json.dumps(prediction.schema_errors),
                    }
                )


def write_error_analysis_csv(
    path: Path,
    predictions: list[PredictionRecord],
    gold: dict[str, GoldLabel],
    tasks_by_id: dict[str, TicketTask],
) -> None:
    rows: list[dict[str, Any]] = []
    for prediction in predictions:
        label = gold.get(prediction.task_id)
        task = tasks_by_id.get(prediction.task_id)
        if label is None:
            continue
        error_types = _prediction_error_types(prediction, label)
        if error_types:
            rows.append(
                {
                    "task_id": prediction.task_id,
                    "condition": prediction.condition,
                    "title": task.title if task else "",
                    "gold_category": label.gold_category,
                    "pred_category": prediction.category,
                    "gold_priority": label.gold_priority,
                    "pred_priority": prediction.priority,
                    "gold_customer_impact": label.gold_customer_impact,
                    "pred_customer_impact": prediction.customer_impact,
                    "gold_requires_human_review": label.requires_human_review,
                    "pred_requires_human_review": prediction.requires_human_review,
                    "confidence": prediction.confidence,
                    "reason": prediction.reason,
                    "error_type": ";".join(error_types),
                    "context_condition": prediction.condition,
                }
            )

    fieldnames = [
        "task_id",
        "condition",
        "title",
        "gold_category",
        "pred_category",
        "gold_priority",
        "pred_priority",
        "gold_customer_impact",
        "pred_customer_impact",
        "gold_requires_human_review",
        "pred_requires_human_review",
        "confidence",
        "reason",
        "error_type",
        "context_condition",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_run_config(
    run_dir: Path,
    provider: BaseProvider,
    conditions: list[Condition],
    number_of_tasks: int,
    limit: int | None,
) -> None:
    config = {
        "provider": provider.provider_name,
        "model": provider.model_name,
        "timestamp": run_dir.name.removeprefix("run_"),
        "conditions_executed": [condition.value for condition in conditions],
        "number_of_tasks": number_of_tasks,
        "limit": limit,
        "temperature": provider.temperature,
        "max_output_tokens": provider.max_output_tokens,
        "repo_version": _repo_version(run_dir),
        "package_version": __version__,
        "python_version": platform.python_version(),
    }
    write_metrics_json(run_dir / "run_config.json", config)


def write_paper_results_summary(
    run_dir: Path,
    provider: BaseProvider,
    tasks: list[TicketTask],
    gold: dict[str, GoldLabel],
    summaries: list[dict[str, Any]],
) -> None:
    failure_counts = _top_failure_types(run_dir / "error_analysis.csv")
    provider_note = (
        "This run uses a deterministic mock provider and should be interpreted only as a pipeline sanity check, "
        "not as empirical LLM performance."
        if provider.provider_name == "mock"
        else "This run uses the OpenAI provider and should be interpreted as a pilot evaluation on the selected benchmark tasks. Results should not be generalized beyond the benchmark without larger and more diverse datasets."
    )
    distributions = _dataset_distributions(tasks, gold)
    lines = [
        "# Paper Results Summary",
        "",
        "## Run Config",
        "",
        f"- Provider: `{provider.provider_name}`",
        f"- Model: `{provider.model_name}`",
        f"- Dataset size: {len(tasks)}",
        f"- Temperature: {provider.temperature}",
        f"- Max output tokens: {provider.max_output_tokens}",
        "",
        "## Dataset Distribution",
        "",
        "Category distribution:",
        _distribution_markdown(distributions["category"]),
        "",
        "Priority distribution:",
        _distribution_markdown(distributions["priority"]),
        "",
        "Customer impact distribution:",
        _distribution_markdown(distributions["customer_impact"]),
        "",
        "Human review distribution:",
        _distribution_markdown(distributions["human_review"]),
        "",
        "## Interpretation Note",
        "",
        provider_note,
        "",
        "## Condition Summary",
        "",
        _markdown_table(summaries),
        "",
        "## Top Failure Types",
        "",
        _failure_markdown(failure_counts),
        "",
        "## Schema Failures",
        "",
        _schema_failure_note(summaries),
        "",
        "## Evidence Coverage",
        "",
        _evidence_note(summaries),
        "",
        "## Best Conditions",
        "",
        _best_conditions_markdown(summaries),
        "",
        "## Recommended Paper Text",
        "",
        (
            "We executed ContextBench on the ticket-triage benchmark across six context conditions. "
            f"{provider_note} The run produced per-condition classification, schema-validity, evidence, "
            "confidence, latency, and human-review metrics, enabling direct comparison of context strategies."
        ),
        "",
    ]
    (run_dir / "paper_results_summary.md").write_text("\n".join(lines), encoding="utf-8")


def _classify_task(
    run_id: str,
    condition: Condition,
    task: TicketTask,
    prompt: str,
    provider: BaseProvider,
) -> PredictionRecord:
    try:
        raw_output = provider.classify_ticket(prompt)
        response = _normalize_provider_response(raw_output)
        validation = parse_provider_output(response.output)
        return _prediction_from_validation(run_id, condition, task.task_id, validation.output, validation, response)
    except Exception as exc:
        return PredictionRecord(
            run_id=run_id,
            condition=condition.value,
            task_id=task.task_id,
            category=None,
            customer_impact=None,
            priority=None,
            requires_human_review=None,
            confidence=None,
            reason=None,
            evidence_ids=[],
            valid_json=False,
            schema_valid=False,
            schema_errors=[f"Provider error: {exc}"],
            provider_error=str(exc),
        )


def _normalize_provider_response(raw_output: dict[str, Any] | str | ProviderResponse) -> ProviderResponse:
    if isinstance(raw_output, ProviderResponse):
        return raw_output
    return ProviderResponse(output=raw_output, raw_response=json.dumps(raw_output) if isinstance(raw_output, dict) else raw_output)


def _prediction_from_validation(
    run_id: str,
    condition: Condition,
    task_id: str,
    output: dict[str, Any] | None,
    validation: Any,
    response: ProviderResponse,
) -> PredictionRecord:
    output = output or {}
    confidence = output.get("confidence")
    provider_error = response.provider_error
    if validation.errors and provider_error is None:
        provider_error = None
    return PredictionRecord(
        run_id=run_id,
        condition=condition.value,
        task_id=task_id,
        category=output.get("category") if isinstance(output.get("category"), str) else None,
        customer_impact=output.get("customer_impact") if isinstance(output.get("customer_impact"), bool) else None,
        priority=output.get("priority") if isinstance(output.get("priority"), str) else None,
        requires_human_review=(
            output.get("requires_human_review") if isinstance(output.get("requires_human_review"), bool) else None
        ),
        confidence=float(confidence) if isinstance(confidence, int | float) and not isinstance(confidence, bool) else None,
        reason=output.get("reason") if isinstance(output.get("reason"), str) else None,
        evidence_ids=output.get("evidence_ids") if isinstance(output.get("evidence_ids"), list) else [],
        valid_json=validation.valid_json,
        schema_valid=validation.schema_valid,
        schema_errors=validation.errors,
        latency_ms=response.latency_ms,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        total_tokens=response.total_tokens,
        provider_error=provider_error,
        raw_response=response.raw_response,
    )


def _prediction_error_types(prediction: PredictionRecord, label: GoldLabel) -> list[str]:
    if prediction.provider_error:
        return ["provider_error"]
    if not prediction.schema_valid:
        return ["schema_failure"]
    errors: list[str] = []
    if prediction.category != label.gold_category:
        errors.append("category_mismatch")
    if prediction.priority != label.gold_priority:
        errors.append("priority_mismatch")
    if prediction.customer_impact != label.gold_customer_impact:
        errors.append("impact_mismatch")
    if prediction.requires_human_review != label.requires_human_review:
        errors.append("human_review_mismatch")
    return errors


def _operational_metrics(predictions: list[PredictionRecord]) -> dict[str, float | int]:
    confidences = [prediction.confidence for prediction in predictions if prediction.confidence is not None]
    latencies = [prediction.latency_ms for prediction in predictions if prediction.latency_ms is not None]
    token_counts = [prediction.total_tokens for prediction in predictions if prediction.total_tokens is not None]
    return {
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
        "total_tokens": sum(token_counts) if token_counts else 0,
    }


def _summary_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    schema = metrics["schema"]
    classification = metrics["classification"]
    reliability = metrics["context_reliability"]
    operational = metrics["operational"]
    total = int(schema["total_outputs"])
    return {
        "total_tasks": total,
        "category_accuracy": classification["category_accuracy"],
        "priority_accuracy": classification["priority_accuracy"],
        "customer_impact_accuracy": classification["customer_impact_accuracy"],
        "customer_impact_precision": classification["customer_impact_precision"],
        "customer_impact_recall": classification["customer_impact_recall"],
        "customer_impact_f1": classification["customer_impact_f1"],
        "human_review_accuracy": classification["human_review_accuracy"],
        "schema_valid_rate": schema["schema_valid_count"] / total if total else 0.0,
        "evidence_coverage": reliability["evidence_coverage"],
        "unsupported_evidence_count": reliability["unsupported_evidence_count"],
        "low_confidence_rate": reliability["low_confidence_rate"],
        "human_review_burden": reliability["human_review_burden"],
        "avg_confidence": operational["avg_confidence"],
        "avg_latency_ms": operational["avg_latency_ms"],
        "total_tokens": operational["total_tokens"],
    }


def _write_prompt(run_dir: Path, condition: Condition, task: TicketTask, prompt: str) -> None:
    prompt_dir = run_dir / "prompts" / condition.value
    prompt_dir.mkdir(parents=True, exist_ok=True)
    (prompt_dir / f"{task.task_id}.txt").write_text(prompt, encoding="utf-8")


def _apply_limit(tasks: list[TicketTask], limit: int | None) -> list[TicketTask]:
    if limit is None:
        return tasks
    if limit < 1:
        raise ValueError("--limit must be greater than zero.")
    return tasks[:limit]


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"Expected true or false, got {value!r}")


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _repo_version(path: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=path,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    return completed.stdout.strip() or None


def _load_run_metrics(run_dir: Path) -> dict[str, Any]:
    metrics_path = run_dir / "metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"metrics.json not found in {run_dir}")
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    return payload.get("conditions", {})


def _flatten_metrics(metrics: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in metrics.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten_metrics(value, name))
        else:
            flat[name] = value
    return flat


def _difference(value_a: Any, value_b: Any) -> float | str:
    if isinstance(value_a, int | float) and isinstance(value_b, int | float):
        return value_b - value_a
    return ""


def _markdown_table(rows: list[dict[str, Any]]) -> str:
    headers = [
        "condition",
        "total_tasks",
        "category_accuracy",
        "priority_accuracy",
        "customer_impact_f1",
        "schema_valid_rate",
        "evidence_coverage",
        "human_review_burden",
    ]
    lines = ["|" + "|".join(headers) + "|", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("|" + "|".join(_format_cell(row.get(header, "")) for header in headers) + "|")
    return "\n".join(lines)


def _format_cell(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _top_failure_types(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    counts: dict[str, int] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            error_type = row.get("error_type", "")
            if error_type:
                for item in error_type.split(";"):
                    if item:
                        counts[item] = counts.get(item, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _failure_markdown(counts: dict[str, int]) -> str:
    if not counts:
        return "No prediction errors were recorded."
    return "\n".join(f"- `{key}`: {value}" for key, value in counts.items())


def _schema_failure_note(summaries: list[dict[str, Any]]) -> str:
    failed = [row for row in summaries if row.get("schema_valid_rate") != 1.0]
    if not failed:
        return "All outputs passed strict schema validation."
    return "Some conditions had schema failures; inspect `errors.csv` and `error_analysis.csv` for details."


def _evidence_note(summaries: list[dict[str, Any]]) -> str:
    rag_rows = [row for row in summaries if str(row["condition"]) in {c.value for c in Condition if c.uses_rag}]
    if not rag_rows:
        return "No RAG conditions were executed."
    best = max(rag_rows, key=lambda row: float(row.get("evidence_coverage", 0.0)))
    return f"Highest RAG evidence coverage was `{best['condition']}` at {_format_cell(best['evidence_coverage'])}."


def _dataset_distributions(tasks: list[TicketTask], gold: dict[str, GoldLabel]) -> dict[str, dict[str, int]]:
    labels = [gold[task.task_id] for task in tasks if task.task_id in gold]
    return {
        "category": dict(Counter(label.gold_category for label in labels)),
        "priority": dict(Counter(label.gold_priority for label in labels)),
        "customer_impact": dict(Counter(str(label.gold_customer_impact).lower() for label in labels)),
        "human_review": dict(Counter(str(label.requires_human_review).lower() for label in labels)),
    }


def _distribution_markdown(distribution: dict[str, int]) -> str:
    return "\n".join(f"- `{key}`: {value}" for key, value in sorted(distribution.items()))


def _best_conditions_markdown(summaries: list[dict[str, Any]]) -> str:
    if not summaries:
        return "No condition summaries were available."
    best_category = max(summaries, key=lambda row: float(row.get("category_accuracy", 0.0)))
    best_impact = max(summaries, key=lambda row: float(row.get("customer_impact_f1", 0.0)))
    best_schema = max(summaries, key=lambda row: float(row.get("schema_valid_rate", 0.0)))
    best_review = min(summaries, key=lambda row: float(row.get("human_review_burden", 0.0)))
    return "\n".join(
        [
            f"- Best category accuracy: `{best_category['condition']}` ({_format_cell(best_category['category_accuracy'])})",
            f"- Best customer-impact F1: `{best_impact['condition']}` ({_format_cell(best_impact['customer_impact_f1'])})",
            f"- Best schema validity: `{best_schema['condition']}` ({_format_cell(best_schema['schema_valid_rate'])})",
            f"- Lowest human-review burden: `{best_review['condition']}` ({_format_cell(best_review['human_review_burden'])})",
        ]
    )
