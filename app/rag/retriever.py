from __future__ import annotations

from typing import Any

from app.vectorstore.chroma_store import ChromaStore


class Retriever:
    def __init__(self, store: ChromaStore, top_k: int) -> None:
        self.store = store
        self.top_k = top_k

    def search(self, question: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """Return the most relevant chunks for a question."""
        return self.store.search(question, top_k or self.top_k)
