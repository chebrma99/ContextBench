import csv
import shutil
import subprocess
import sys
from pathlib import Path


def test_cli_limit_option_generates_limited_predictions() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_root = project_root / ".test_runs" / "cli_limit"
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "contextbench.cli",
            "run-all-ticket-triage",
            "--provider",
            "mock",
            "--limit",
            "5",
            "--output",
            str(output_root),
        ],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )

    run_line = next(line for line in completed.stdout.splitlines() if line.startswith("Completed all"))
    run_dir = Path(run_line.split(": ", 1)[1])
    with (run_dir / "predictions.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 30
    assert (run_dir / "prompts" / "C5_RAG_STEERING_MEMORY" / "TICKET-005.txt").exists()
