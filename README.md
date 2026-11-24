# ContextBench — LLM Workflow Automation Evaluation

**Research record:** *ContextBench: Evaluating Context Engineering Strategies for Reliable LLM Workflow Automation*  
**DOI:** https://doi.org/10.5281/zenodo.20823546


ContextBench is an open-source benchmark framework for evaluating how context strategies affect LLM workflow reliability. v0.1 focuses on software ticket triage and compares the same task under prompt-only, RAG-only, steering-document-only, memory-file-only, and combined-context setups.

## Why context engineering matters

LLM workflow failures are not only model failures. They often come from missing context, stale context, irrelevant retrieval, conflicting guidance, weak prioritization, or context that is present but not used. ContextBench makes these effects measurable by holding the task set fixed while changing the context strategy.

The benchmark tracks classification quality, JSON/schema validity, instruction following, evidence behavior, confidence, and human-review burden.

## Compared Conditions

- `C0_PROMPT_ONLY`: ticket title, body, labels, and metadata only
- `C1_RAG_ONLY`: ticket plus retrieved RAG documents
- `C2_STEERING_ONLY`: ticket plus steering policy
- `C3_MEMORY_ONLY`: ticket plus memory file
- `C4_RAG_STEERING`: ticket plus retrieved RAG documents and steering policy
- `C5_RAG_STEERING_MEMORY`: ticket plus RAG documents, steering policy, and memory file

## Install

```bash
cd contextbench
pip install -e .
```

Optional OpenAI support:

```bash
pip install -e ".[openai]"
```

API keys must be provided through environment variables only. See `.env.example`.

## Run the mock benchmark

Validate the bundled 50-task dataset:

```bash
python -m contextbench.cli validate-dataset
```

Run all ticket-triage conditions with the deterministic local provider:

```bash
python -m contextbench.cli run-all-ticket-triage --provider mock
```

Run a small smoke test across all six conditions:

```bash
python -m contextbench.cli run-all-ticket-triage --provider mock --limit 3
```

Run one condition:

```bash
python -m contextbench.cli run-ticket-triage \
  --condition C0_PROMPT_ONLY \
  --provider mock \
  --tasks datasets/ticket_triage/tasks.jsonl \
  --gold datasets/ticket_triage/gold_labels.csv \
  --output results/
```

## Run with OpenAI

Mac/Linux:

```bash
export OPENAI_API_KEY=your_key_here
python -m contextbench.cli run-all-ticket-triage --provider openai --model gpt-4o-mini
```

PowerShell:

```powershell
$env:OPENAI_API_KEY="your_key_here"
python -m contextbench.cli run-all-ticket-triage --provider openai --model gpt-4o-mini
```

Small OpenAI smoke test:

```bash
python -m contextbench.cli run-all-ticket-triage \
  --provider openai \
  --model gpt-4o-mini \
  --limit 5
```

The OpenAI provider reads `OPENAI_API_KEY` from the environment, requests strict JSON output, retries once if the model returns malformed JSON, and records raw responses, latency, and token usage when available.

Full 50-task OpenAI run on Mac/Linux:

```bash
export OPENAI_API_KEY="your_key_here"
python -m contextbench.cli run-all-ticket-triage \
  --provider openai \
  --model gpt-4o-mini \
  --tasks datasets/ticket_triage/tasks.jsonl \
  --gold datasets/ticket_triage/gold_labels.csv \
  --output results/
```

Full 50-task OpenAI run on PowerShell:

```powershell
$env:OPENAI_API_KEY="your_key_here"
python -m contextbench.cli run-all-ticket-triage `
  --provider openai `
  --model gpt-4o-mini `
  --tasks datasets/ticket_triage/tasks.jsonl `
  --gold datasets/ticket_triage/gold_labels.csv `
  --output results/
```

## Compare Runs

Compare two run folders:

```bash
python -m contextbench.cli compare-runs \
  --run-a results/run_mock_timestamp \
  --run-b results/run_openai_timestamp
```

This writes `comparison_report.csv` into the second run folder.

## Outputs

Each run writes to `results/run_<timestamp>/`.

- `predictions.csv`: all model/provider outputs across conditions
- `metrics.json`: nested metrics by condition
- `condition_summary.csv`: compact comparison table
- `errors.csv`: invalid JSON, schema errors, or provider errors
- `error_analysis.csv`: per-task mismatch and provider/schema failure analysis
- `run_config.json`: provider, model, timestamp, executed conditions, task count, Python version, and package/repo version
- `paper_results_summary.md`: honest paper-ready summary text and tables
- `prompts/`: prompt/context package for every task and condition

Per-condition files are also written for debugging.

## Metrics

Classification metrics:

- category accuracy
- priority accuracy
- customer impact accuracy, precision, recall, and F1
- human review accuracy

Schema and instruction metrics:

- total outputs
- valid JSON count
- schema valid count
- schema failure count and rate
- JSON-only and schema-instruction success rates

Context reliability metrics:

- evidence coverage when RAG is used
- unsupported evidence count
- low confidence rate
- human review burden

Operational metrics:

- average confidence
- average latency in milliseconds when available
- total tokens when available

## Research use

ContextBench supports context-engineering research by producing reproducible comparisons across context strategies. The first dataset is intentionally small and inspectable, so researchers can audit individual failures and extend it with larger ticket corpora. The same framework can later add additional providers, vector retrieval, stale/conflicting context perturbations, and human-in-the-loop cost models.

## Data format

Tasks are JSONL rows with `task_id`, `source`, `title`, `description`, `labels`, and `metadata`. Gold labels are CSV rows with:

```text
task_id,gold_category,gold_customer_impact,gold_priority,requires_human_review
```

Provider outputs must be JSON only:

```json
{
  "category": "Customer UI Issue",
  "customer_impact": true,
  "priority": "High",
  "requires_human_review": false,
  "confidence": 0.87,
  "reason": "The issue describes a broken customer-facing mobile checkout interaction.",
  "evidence_ids": ["ticket_taxonomy.md", "customer_impact_guidelines.md"]
}
```


## Citation

If you use ContextBench or build on its benchmark design in academic work, please cite the associated research record:

> Manoja Chebrolu. *ContextBench: Evaluating Context Engineering Strategies for Reliable LLM Workflow Automation*. Zenodo, 2026. https://doi.org/10.5281/zenodo.20823546

BibTeX:

```bibtex
@misc{chebrolu2026contextbench,
  author       = {Chebrolu, Manoja},
  title        = {ContextBench: Evaluating Context Engineering Strategies for Reliable LLM Workflow Automation},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.20823546},
  url          = {https://doi.org/10.5281/zenodo.20823546}
}
```

Research site: https://chebrma99.github.io/

Google Scholar: https://scholar.google.com/citations?user=tmlAIyMAAAAJ&hl=en
