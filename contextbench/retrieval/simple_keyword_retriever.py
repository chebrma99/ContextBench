from __future__ import annotations

import re
from collections import Counter

from contextbench.core.models import ContextDocument, TicketTask


class SimpleKeywordRetriever:
    """Small deterministic keyword retriever for local JSON/Markdown corpora."""

    def __init__(self, documents: list[ContextDocument], top_k: int = 2) -> None:
        self.documents = documents
        self.top_k = top_k

    def retrieve(self, task: TicketTask) -> list[ContextDocument]:
        query_terms = _tokens(" ".join([task.title, task.description, " ".join(task.labels)]))
        if not query_terms:
            return []

        scored: list[tuple[int, str, ContextDocument]] = []
        for document in self.documents:
            doc_terms = Counter(_tokens(document.text))
            score = sum(doc_terms[term] for term in query_terms)
            scored.append((score, document.doc_id, document))

        ranked = sorted(scored, key=lambda item: (-item[0], item[1]))
        return [document for score, _, document in ranked[: self.top_k] if score > 0]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())
