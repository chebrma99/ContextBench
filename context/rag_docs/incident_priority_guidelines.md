# Incident Priority Guidelines

Use exactly one allowed priority value.

## Critical

Use Critical for active production outages, payment failures, broad login failures, security exposure, major data safety risk, or deployment mistakes that could affect production data. Examples include SSO outages, production checkout misrouting, staging connected to production data, critical CVEs, and permission flaws exposing sensitive actions.

## High

Use High for customer-facing regressions, blocked releases, serious workflow interruptions, production deployment failures, or important business processes that are degraded but not fully down. Examples include broken checkout UI, stale customer-facing reports, blocked merge queues, failed production rollback, and customer admin permission denial.

## Medium

Use Medium for meaningful defects that need planned remediation but are not broad outages. Examples include internal dashboard inaccuracies, single-repo CI issues, worker backlogs, non-critical dependency conflicts, admin performance issues, and partial UI defects.

## Low

Use Low for cleanup, documentation, copy, planning, internal maintenance, dev-only tooling, and low-risk repository updates.

When scope is unclear, do not inflate priority solely because a severe outcome is possible. Prefer `requires_human_review: true` when the ticket lacks enough detail.
