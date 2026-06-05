from __future__ import annotations

import argparse
from pathlib import Path

from contextbench.core.dataset_validator import format_validation_report, validate_ticket_triage_dataset
from contextbench.core.models import BenchmarkPaths, Condition
from contextbench.core.runner import compare_runs, run_all_conditions, run_condition
from contextbench.providers import BaseProvider, MockProvider, OpenAIProvider


def main() -> None:
    parser = argparse.ArgumentParser(prog="contextbench", description="Run ContextBench benchmarks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_ticket = subparsers.add_parser("run-ticket-triage", help="Run one ticket triage condition.")
    _add_common_args(run_ticket)
    run_ticket.add_argument("--condition", choices=[condition.value for condition in Condition], required=True)

    run_all = subparsers.add_parser("run-all-ticket-triage", help="Run all ticket triage conditions.")
    _add_common_args(run_all)

    compare = subparsers.add_parser("compare-runs", help="Compare two ContextBench run folders.")
    compare.add_argument("--run-a", required=True)
    compare.add_argument("--run-b", required=True)

    validate = subparsers.add_parser("validate-dataset", help="Validate the ticket triage dataset.")
    validate.add_argument("--tasks", default="datasets/ticket_triage/tasks.jsonl")
    validate.add_argument("--gold", default="datasets/ticket_triage/gold_labels.csv")

    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    if args.command == "compare-runs":
        output_path = compare_runs(_resolve_path(args.run_a, project_root), _resolve_path(args.run_b, project_root))
        print(f"Wrote comparison report: {output_path}")
        return
    if args.command == "validate-dataset":
        try:
            report = validate_ticket_triage_dataset(
                _resolve_path(args.tasks, project_root),
                _resolve_path(args.gold, project_root),
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print("Dataset validation passed.")
        print(format_validation_report(report))
        return

    paths = BenchmarkPaths(
        tasks_path=_resolve_path(args.tasks, project_root),
        gold_path=_resolve_path(args.gold, project_root),
        output_root=_resolve_path(args.output, project_root),
        project_root=project_root,
    )
    provider = _build_provider(args.provider, args.model)

    if args.command == "run-ticket-triage":
        predictions, metrics = run_condition(Condition(args.condition), provider, paths, limit=args.limit)
        print(f"Completed {args.condition}: {len(predictions)} predictions")
        print(f"Category accuracy: {metrics['classification']['category_accuracy']:.3f}")
        print(f"Schema failure rate: {metrics['schema']['schema_failure_rate']:.3f}")
    elif args.command == "run-all-ticket-triage":
        run_dir, summaries = run_all_conditions(provider, paths, limit=args.limit)
        print(f"Completed all ticket triage conditions: {run_dir}")
        _print_summary(summaries)


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provider", choices=["mock", "openai"], default="mock")
    parser.add_argument("--model", default=None, help="Optional provider model name.")
    parser.add_argument("--tasks", default="datasets/ticket_triage/tasks.jsonl")
    parser.add_argument("--gold", default="datasets/ticket_triage/gold_labels.csv")
    parser.add_argument("--output", default="results/")
    parser.add_argument("--limit", type=int, default=None, help="Run only the first N tasks.")


def _build_provider(provider_name: str, model: str | None) -> BaseProvider:
    if provider_name == "mock":
        return MockProvider()
    if provider_name == "openai":
        return OpenAIProvider(model=model)
    raise ValueError(f"Unsupported provider: {provider_name}")


def _resolve_path(value: str, project_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _print_summary(summaries: list[dict[str, object]]) -> None:
    headers = ["condition", "total_tasks", "category_accuracy", "priority_accuracy", "schema_valid_rate", "human_review_burden"]
    print(",".join(headers))
    for row in summaries:
        print(",".join(str(row[header]) for header in headers))


if __name__ == "__main__":
    main()
