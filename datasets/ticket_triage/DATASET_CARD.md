# Dataset Card: ContextBench Ticket Triage

## Dataset

- Name: ContextBench Ticket Triage
- Version: v0.2
- Task count: 50
- Task type: Synthetic software ticket triage
- Format: JSONL tasks with CSV gold labels

## Labels

Each ticket has gold labels for:

- `gold_category`
- `gold_customer_impact`
- `gold_priority`
- `requires_human_review`

## Category Taxonomy

- Customer UI Issue: customer-facing layout, interaction, accessibility, or product screen defects
- Pipeline Blocked: CI, build, test, merge queue, packaging, or workflow failures
- Data / Metrics Issue: dashboards, analytics, reports, exports, missing records, or metric pipeline issues
- Performance Issue: latency, timeouts, high memory, CPU saturation, throughput, or worker backlog
- Dependency Failure: package, SDK, library, registry, resolver, base image, or version conflicts
- Deployment Issue: production, staging, canary, release, rollback, preview, or environment rollout failures
- Auth / Access Issue: login, SSO, OAuth, password reset, permissions, tokens, roles, and session security
- Other: cleanup, maintenance, docs, planning, and low-risk internal work

## Intended Use

This dataset is intended for evaluating how context strategies affect LLM ticket-triage reliability. It supports controlled comparison of prompt-only, RAG-only, steering-document-only, memory-file-only, and combined-context conditions.

## Limitations

The dataset is synthetic and intentionally small compared with production support or engineering issue trackers. It is useful for pilot evaluation and reproducibility checks, but results should not be generalized without larger and more diverse datasets.

## Ethics And Privacy

The dataset contains no real private user data, no real customer names, no credentials, and no proprietary system names. Repository names use generic `demo/*` examples. The tickets are realistic but synthetic.

## Recommended Citation

Citation placeholder:

```text
ContextBench Contributors. ContextBench Ticket Triage Dataset v0.2. 2026.
```
