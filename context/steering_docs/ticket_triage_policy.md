# Ticket Triage Policy

Return JSON only. Do not include Markdown, prose outside JSON, or invented fields.

Use only these categories:

- Customer UI Issue
- Pipeline Blocked
- Data / Metrics Issue
- Performance Issue
- Dependency Failure
- Deployment Issue
- Auth / Access Issue
- Other

Use only these priority values:

- Critical
- High
- Medium
- Low

Do not invent category names or priority names. If a ticket has multiple signals, choose the category for the primary operational risk.

Set `requires_human_review` to true when the report is ambiguous, intermittent, security-sensitive, data-safety-sensitive, multi-repo, contradictory, or lacks enough scope for confident automation.

When RAG documents are present in the prompt, cite relevant document IDs in `evidence_ids`. Do not cite document IDs that were not present in the prompt.

When no RAG documents are present, `evidence_ids` may be empty unless another provided context document directly supports the decision.
