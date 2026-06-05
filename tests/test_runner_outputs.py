import csv
import shutil
from pathlib import Path

from contextbench.core.models import BenchmarkPaths
from contextbench.core.runner import run_all_conditions
from contextbench.providers.mock_provider import MockProvider


def test_limit_and_error_analysis_generation() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_root = project_root / ".test_runs" / "runner_outputs"
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    paths = BenchmarkPaths(
        tasks_path=project_root / "datasets" / "ticket_triage" / "tasks.jsonl",
        gold_path=project_root / "datasets" / "ticket_triage" / "gold_labels.csv",
        output_root=output_root,
        project_root=project_root,
    )

    run_dir, summaries = run_all_conditions(MockProvider(), paths, limit=5)

    assert all(row["total_tasks"] == 5 for row in summaries)
    assert (run_dir / "predictions.csv").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "condition_summary.csv").exists()
    assert (run_dir / "errors.csv").exists()
    assert (run_dir / "error_analysis.csv").exists()
    assert (run_dir / "run_config.json").exists()
    assert (run_dir / "paper_results_summary.md").exists()
    assert (run_dir / "prompts" / "C0_PROMPT_ONLY" / "TICKET-001.txt").exists()

    with (run_dir / "predictions.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 30
    assert "Dataset Distribution" in (run_dir / "paper_results_summary.md").read_text(encoding="utf-8")
