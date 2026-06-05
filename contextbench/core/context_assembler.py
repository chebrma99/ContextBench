from __future__ import annotations

from pathlib import Path

from contextbench.core.models import Condition, ContextDocument, TicketTask
from contextbench.retrieval.simple_keyword_retriever import SimpleKeywordRetriever


class ContextAssembler:
    def __init__(self, project_root: Path, rag_top_k: int = 2) -> None:
        self.project_root = project_root
        self.rag_documents = self._load_documents(project_root / "context" / "rag_docs")
        self.steering_documents = self._load_documents(project_root / "context" / "steering_docs")
        self.memory_documents = self._load_documents(project_root / "context" / "memory_files")
        self.retriever = SimpleKeywordRetriever(self.rag_documents, top_k=rag_top_k)

    def assemble(self, task: TicketTask, condition: Condition) -> tuple[str, list[ContextDocument]]:
        documents: list[ContextDocument] = []
        if condition.uses_rag:
            documents.extend(self.retriever.retrieve(task))
        if condition.uses_steering:
            documents.extend(self.steering_documents)
        if condition.uses_memory:
            documents.extend(self.memory_documents)

        prompt = self._build_prompt(task, condition, documents)
        return prompt, documents

    def allowed_evidence_ids(self, documents: list[ContextDocument]) -> set[str]:
        return {document.doc_id for document in documents}

    def _build_prompt(self, task: TicketTask, condition: Condition, documents: list[ContextDocument]) -> str:
        labels = ", ".join(task.labels)
        metadata = ", ".join(f"{key}={value}" for key, value in sorted(task.metadata.items()))
        doc_text = "\n\n".join(f"[DOC:{doc.doc_id}]\n{doc.text}" for doc in documents)
        context_block = doc_text if documents else "No external context documents provided."

        return f"""Benchmark condition: {condition.value}

Classify this software ticket. Return JSON only with:
category, customer_impact, priority, requires_human_review, confidence, reason, evidence_ids.

Allowed categories:
- Customer UI Issue
- Pipeline Blocked
- Data / Metrics Issue
- Performance Issue
- Dependency Failure
- Deployment Issue
- Auth / Access Issue
- Other

Allowed priorities: Critical, High, Medium, Low

Ticket:
task_id: {task.task_id}
source: {task.source}
title: {task.title}
description: {task.description}
labels: {labels}
metadata: {metadata}

Context documents:
{context_block}
"""

    def _load_documents(self, directory: Path) -> list[ContextDocument]:
        if not directory.exists():
            return []
        documents: list[ContextDocument] = []
        for path in sorted(directory.glob("*.md")):
            documents.append(ContextDocument(doc_id=path.name, text=path.read_text(encoding="utf-8"), source_path=path))
        return documents
