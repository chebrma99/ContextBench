from __future__ import annotations

import re
from typing import Any

from contextbench.providers.base import BaseProvider


class MockProvider(BaseProvider):
    """Deterministic local classifier used for reproducible smoke tests."""

    provider_name = "mock"
    model_name = "deterministic-rules"
    temperature = 0.0
    max_output_tokens = None

    def classify_ticket(self, prompt: str) -> dict[str, Any]:
        ticket_text = self._ticket_text(prompt).lower()
        full_text = prompt.lower()
        condition = self._condition(prompt)
        category = self._category(ticket_text)
        customer_impact = self._customer_impact(ticket_text, category, full_text)
        priority = self._priority(ticket_text, category, customer_impact, full_text)
        human_review = self._requires_human_review(ticket_text, full_text, condition)
        confidence = self._confidence(ticket_text, category)
        evidence_ids = self._evidence_ids(prompt)

        return {
            "category": category,
            "customer_impact": customer_impact,
            "priority": priority,
            "requires_human_review": human_review,
            "confidence": confidence,
            "reason": self._reason(category, priority, customer_impact),
            "evidence_ids": evidence_ids,
        }

    def _category(self, text: str) -> str:
        rules = [
            ("Customer UI Issue", ["button", "ui", "css", "mobile", "safari", "modal", "page", "form", "checkout"]),
            ("Pipeline Blocked", ["ci", "pipeline", "build", "test suite", "merge blocked", "workflow"]),
            ("Data / Metrics Issue", ["dashboard", "metric", "analytics", "report", "data", "count", "chart"]),
            ("Performance Issue", ["slow", "latency", "timeout", "performance", "memory", "cpu", "load time"]),
            ("Dependency Failure", ["dependency", "package", "library", "sdk", "version", "npm", "pypi"]),
            ("Deployment Issue", ["deploy", "release", "rollback", "environment", "staging", "production"]),
            ("Auth / Access Issue", ["login", "auth", "permission", "access", "token", "sso", "oauth"]),
        ]
        scores = [(sum(1 for keyword in keywords if _contains(text, keyword)), category) for category, keywords in rules]
        best_score, best_category = max(scores, key=lambda item: item[0])
        return best_category if best_score > 0 else "Other"

    def _customer_impact(self, text: str, category: str, full_text: str) -> bool:
        impact_terms = ["customer", "user", "checkout", "production", "login", "mobile", "payment", "public"]
        if "missing customer records should be treated as customer-impacting" in full_text and "missing customer" in text:
            return True
        return category in {"Customer UI Issue", "Auth / Access Issue", "Performance Issue"} or _contains_any(
            text, impact_terms
        )

    def _priority(self, text: str, category: str, customer_impact: bool, full_text: str) -> str:
        if _contains_any(text, ["outage", "security", "payment", "cannot login", "production down"]):
            return "Critical"
        if "missing customer records should be treated as customer-impacting" in full_text and "missing customer" in text:
            return "High"
        if _contains_any(text, ["blocked", "checkout", "release", "rollback", "sso"]) or (
            customer_impact and category in {"Customer UI Issue", "Auth / Access Issue"}
        ):
            return "High"
        if category in {"Pipeline Blocked", "Performance Issue", "Dependency Failure", "Data / Metrics Issue"}:
            return "Medium"
        return "Low"

    def _requires_human_review(self, text: str, full_text: str, condition: str) -> bool:
        if _contains_any(text, ["unclear", "security", "legal", "ambiguous", "unknown"]):
            return True
        if "intermittent" in text:
            return condition in {"C3_MEMORY_ONLY", "C5_RAG_STEERING_MEMORY"}
        if "staging" in text and "wrong database" in text:
            return "staging database configuration mistakes should be reviewed" in full_text
        return False

    def _confidence(self, text: str, category: str) -> float:
        if category == "Other":
            return 0.55
        keyword_hits = len(set(re.findall(r"[a-z]+", text)))
        return min(0.93, 0.72 + (keyword_hits % 9) / 100)

    def _evidence_ids(self, prompt: str) -> list[str]:
        ids: list[str] = []
        for line in prompt.splitlines():
            stripped = line.strip()
            if stripped.startswith("[DOC:") and "]" in stripped:
                ids.append(stripped.removeprefix("[DOC:").split("]", 1)[0])
        return ids[:3]

    def _reason(self, category: str, priority: str, customer_impact: bool) -> str:
        impact = "customer-facing impact" if customer_impact else "limited direct customer impact"
        return f"Classified as {category} with {priority} priority because the ticket indicates {impact}."

    def _ticket_text(self, prompt: str) -> str:
        if "Ticket:" not in prompt:
            return prompt
        ticket_block = prompt.split("Ticket:", 1)[1]
        return ticket_block.split("Context documents:", 1)[0]

    def _condition(self, prompt: str) -> str:
        for line in prompt.splitlines():
            if line.startswith("Benchmark condition:"):
                return line.split(":", 1)[1].strip()
        return ""


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(_contains(text, keyword) for keyword in keywords)


def _contains(text: str, keyword: str) -> bool:
    return bool(re.search(rf"\b{re.escape(keyword)}\b", text))
