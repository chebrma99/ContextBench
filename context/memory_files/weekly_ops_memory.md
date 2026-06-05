# Weekly Ops Memory

Recent mobile checkout issues have affected customers. Treat mobile checkout interaction regressions as customer-impacting, and use High priority unless there is an active payment outage.

CI pipeline failures usually require human review when multiple repositories are affected, when the merge queue is blocked, or when failures are intermittent. Single-repo documentation or spellcheck failures are usually Low or Medium.

Stale metrics incidents are often Medium priority when dashboards are internal. Customer-facing reports, billing exports, or possibly missing customer records should be treated as higher risk and may require human review.

Authentication regressions are High priority when they block login or account access. Broad SSO outages, security-sensitive permission defects, or session-cookie findings should receive human review and may be Critical.

Deployment mistakes involving production traffic, canary routing, rollback, or production data deserve careful review. Staging connected to production data is a data-safety risk even if customers are not directly affected.
