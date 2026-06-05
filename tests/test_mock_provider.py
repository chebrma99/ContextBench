from contextbench.core.schema_validator import parse_provider_output
from contextbench.providers.mock_provider import MockProvider


def test_mock_provider_returns_valid_schema() -> None:
    prompt = """Benchmark condition: C0_PROMPT_ONLY

Ticket:
task_id: TICKET-001
source: github
title: Checkout button is not clickable on mobile
description: Users report that the checkout CTA does not respond on mobile Safari.
labels: bug, ui, mobile
metadata: repo=demo/shop-web, status=open

Context documents:
No external context documents provided.
"""
    output = MockProvider().classify_ticket(prompt)
    result = parse_provider_output(output)

    assert result.schema_valid is True
    assert result.output["category"] == "Customer UI Issue"
