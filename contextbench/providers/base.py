from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from contextbench.core.models import ProviderResponse


class BaseProvider(ABC):
    """Provider interface for ticket classification."""

    provider_name = "base"
    model_name: str | None = None
    temperature: float | None = None
    max_output_tokens: int | None = None

    @abstractmethod
    def classify_ticket(self, prompt: str) -> dict[str, Any] | str | ProviderResponse:
        """Return a JSON-compatible dict or JSON string for a ticket prompt."""
