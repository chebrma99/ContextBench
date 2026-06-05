from __future__ import annotations

import json
from typing import Any

from contextbench.core.models import ALLOWED_CATEGORIES, ALLOWED_PRIORITIES, ValidationResult


def parse_provider_output(raw_output: dict[str, Any] | str) -> ValidationResult:
    errors: list[str] = []
    output: dict[str, Any] | None

    if isinstance(raw_output, str):
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            return ValidationResult(
                valid_json=False,
                schema_valid=False,
                output=None,
                errors=[f"Invalid JSON: {exc.msg}"],
            )
        output = parsed if isinstance(parsed, dict) else None
        if output is None:
            errors.append("JSON output must be an object")
    elif isinstance(raw_output, dict):
        output = raw_output
    else:
        return ValidationResult(
            valid_json=False,
            schema_valid=False,
            output=None,
            errors=["Provider output must be a dict or JSON string"],
        )

    if output is not None:
        errors.extend(validate_output_schema(output))

    return ValidationResult(
        valid_json=True,
        schema_valid=not errors,
        output=output,
        errors=errors,
    )


def validate_output_schema(output: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_keys = {
        "category",
        "customer_impact",
        "priority",
        "requires_human_review",
        "confidence",
        "reason",
        "evidence_ids",
    }
    missing = sorted(required_keys - set(output))
    for key in missing:
        errors.append(f"Missing required field: {key}")

    category = output.get("category")
    if category not in ALLOWED_CATEGORIES:
        errors.append(f"category must be one of {sorted(ALLOWED_CATEGORIES)}")

    priority = output.get("priority")
    if priority not in ALLOWED_PRIORITIES:
        errors.append(f"priority must be one of {sorted(ALLOWED_PRIORITIES)}")

    if not isinstance(output.get("customer_impact"), bool):
        errors.append("customer_impact must be boolean")

    if not isinstance(output.get("requires_human_review"), bool):
        errors.append("requires_human_review must be boolean")

    confidence = output.get("confidence")
    if not isinstance(confidence, int | float) or isinstance(confidence, bool):
        errors.append("confidence must be numeric")
    elif not 0 <= float(confidence) <= 1:
        errors.append("confidence must be between 0 and 1")

    reason = output.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append("reason must be a non-empty string")

    evidence_ids = output.get("evidence_ids")
    if not isinstance(evidence_ids, list) or not all(isinstance(item, str) for item in evidence_ids):
        errors.append("evidence_ids must be a list of strings")

    return errors
