from contextbench.core.schema_validator import parse_provider_output


def test_parse_provider_output_accepts_valid_schema() -> None:
    result = parse_provider_output(
        {
            "category": "Customer UI Issue",
            "customer_impact": True,
            "priority": "High",
            "requires_human_review": False,
            "confidence": 0.9,
            "reason": "Customer-facing checkout problem.",
            "evidence_ids": ["ticket_taxonomy.md"],
        }
    )

    assert result.valid_json is True
    assert result.schema_valid is True
    assert result.errors == []


def test_parse_provider_output_rejects_bad_confidence() -> None:
    result = parse_provider_output(
        {
            "category": "Customer UI Issue",
            "customer_impact": True,
            "priority": "High",
            "requires_human_review": False,
            "confidence": 2.0,
            "reason": "Too confident.",
            "evidence_ids": [],
        }
    )

    assert result.schema_valid is False
    assert "confidence must be between 0 and 1" in result.errors


def test_parse_provider_output_rejects_invalid_category() -> None:
    result = parse_provider_output(
        {
            "category": "Made Up Category",
            "customer_impact": True,
            "priority": "High",
            "requires_human_review": False,
            "confidence": 0.8,
            "reason": "Invalid category should fail.",
            "evidence_ids": [],
        }
    )

    assert result.schema_valid is False
    assert any("category must be one of" in error for error in result.errors)
