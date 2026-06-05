# Ticket Taxonomy

Use exactly one allowed category for each ticket.

## Customer UI Issue

Customer-facing layout, interaction, accessibility, localization, or product screen defects. Examples include broken checkout buttons, mobile overlays covering inputs, inaccessible modals, blank product carousels, and public signup page contrast failures.

## Pipeline Blocked

CI, build, test, merge queue, packaging, or workflow automation failures that block engineering delivery. Examples include failing main workflows, flaky integration tests, Docker build timeouts, lint failures across repos, and package signing failures.

## Data / Metrics Issue

Incorrect dashboards, stale reports, missing records, broken exports, analytics ingestion defects, or metric pipeline regressions. Examples include revenue double counting, stale customer usage reports, missing CRM records, empty dashboard filters, and shifted billing CSV columns.

## Performance Issue

Latency, timeout, memory, CPU, throughput, load-time, or worker-backlog problems. Examples include slow product search, account settings timeouts, excessive memory in background jobs, CDN load regressions, CPU-heavy audit queries, and delayed thumbnail generation.

## Dependency Failure

Package, SDK, library, registry, resolver, peer dependency, base image, or version conflicts. Examples include removed SDK versions, security scanner conflicts, connector response-shape changes, UI library export removals, critical CVEs, and dev-only addon incompatibilities.

## Deployment Issue

Production, staging, canary, release, rollback, environment variable, registry publication, preview environment, or feature flag rollout failures. Examples include missing production environment variables, staging pointing to production database, canary routing to old services, expired registry tokens, and failed preview deployments.

## Auth / Access Issue

Login, SSO, OAuth, password reset, permissions, tokens, roles, session security, or access-denied problems. Examples include failed SSO, billing permission denial, immediate password-reset expiry, API token creation failures, OAuth state rejection, and session cookie security findings.

## Other

Maintenance, cleanup, planning, documentation, copy updates, repository metadata, and low-risk internal tasks. Examples include issue template copy, CODEOWNERS updates, old feature flag cleanup, asset archival, planning issues, and onboarding checklist cleanup.
