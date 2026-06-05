from __future__ import annotations

from contextbench.core.models import ContextDocument, TicketTask
from contextbench.retrieval.simple_keyword_retriever import SimpleKeywordRetriever


class VectorRetriever(SimpleKeywordRetriever):
    """Placeholder-compatible retriever.

    v0.1 intentionally avoids hidden embedding dependencies. This class preserves
    the public extension point while delegating to deterministic keyword retrieval.
    """

    def __init__(self, documents: list[ContextDocument], top_k: int = 2) -> None:
        super().__init__(documents=documents, top_k=top_k)

    def retrieve(self, task: TicketTask) -> list[ContextDocument]:
        return super().retrieve(task)
