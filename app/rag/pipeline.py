from __future__ import annotations

from typing import Any

from app.llm.ollama_client import OllamaClient
from app.rag.prompt import FALLBACK_ANSWER, build_context, build_rag_prompt
from app.rag.retriever import Retriever


class RagPipeline:
    def __init__(self, retriever: Retriever, ollama_client: OllamaClient) -> None:
        self.retriever = retriever
        self.ollama_client = ollama_client

    def answer(self, question: str, top_k: int | None = None) -> dict[str, Any]:
        """Retrieve context, ask Ollama, and return answer plus source chunks."""
        chunks = self.retriever.search(question, top_k=top_k)
        if not chunks:
            return {"answer": FALLBACK_ANSWER, "sources": []}

        context = build_context(chunks)
        prompt = build_rag_prompt(question, context)
        answer = self.ollama_client.generate(prompt)
        return {"answer": answer or FALLBACK_ANSWER, "sources": chunks}
