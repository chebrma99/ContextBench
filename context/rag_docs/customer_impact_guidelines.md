# Customer Impact Guidelines

Set `customer_impact` to true when external users, shoppers, public visitors, enterprise customers, customer admins, billing users, login users, or customer-facing reports are affected.

Common true cases:

- checkout, payment, signup, login, account settings, billing settings, public pages, or customer reports
- customer-visible performance regressions
- production deployment failures that affect customer traffic
- missing or possibly missing customer records
- accessibility problems in customer-facing flows

Set `customer_impact` to false for purely internal engineering workflows, staging-only issues, internal dashboards, maintenance, cleanup, docs, dev-only tooling, and internal planning unless the ticket states a direct customer-facing effect.

If customer impact is plausible but unclear, set `requires_human_review` to true rather than guessing with high confidence.
