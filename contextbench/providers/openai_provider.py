from __future__ import annotations

import json
import os
import time
from typing import Any

from contextbench.core.models import ProviderResponse
from contextbench.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI provider using JSON-only structured output."""

    provider_name = "openai"

    def __init__(self, model: str | None = None, temperature: float = 0.0, max_output_tokens: int = 500) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to your environment before using --provider openai.")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install OpenAI support with: pip install -e .[openai]") from exc

        self._client = OpenAI(api_key=api_key)
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.model_name = self._model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def classify_ticket(self, prompt: str) -> ProviderResponse:
        first = self._call(prompt)
        parsed = _parse_json_object(first.raw_response or "")
        if parsed is not None:
            first.output = parsed
            return first

        retry_prompt = (
            f"{prompt}\n\nYour previous response was not valid JSON. Return only one JSON object with the required "
            "fields and no Markdown, prose, or code fences."
        )
        second = self._call(retry_prompt)
        parsed = _parse_json_object(second.raw_response or "")
        if parsed is not None:
            second.output = parsed
            return second

        second.output = second.raw_response or ""
        second.provider_error = "OpenAI response was not valid JSON after one retry."
        return second

    def _call(self, prompt: str) -> ProviderResponse:
        started = time.perf_counter()
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
        )
        latency_ms = (time.perf_counter() - started) * 1000
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        return ProviderResponse(
            output=content,
            raw_response=content,
            latency_ms=latency_ms,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
        )


_SYSTEM_PROMPT = """You classify software tickets for ContextBench.
Return strict JSON only. Do not include Markdown or prose.
The JSON object must contain exactly these fields:
- category: one of Customer UI Issue, Pipeline Blocked, Data / Metrics Issue, Performance Issue, Dependency Failure, Deployment Issue, Auth / Access Issue, Other
- customer_impact: boolean
- priority: one of Critical, High, Medium, Low
- requires_human_review: boolean
- confidence: number between 0 and 1
- reason: short non-empty string
- evidence_ids: array of document id strings, such as ticket_taxonomy.md, or [] when no evidence was used
"""


def _parse_json_object(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
