from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from app.ingestion.chunker import TextChunk

logger = logging.getLogger(__name__)


def _as_list(value: Any) -> list:
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value)


class ChromaStore:
    """Small wrapper around local ChromaDB persistent storage."""

    def __init__(
        self,
        persist_dir: str | Path,
        embedding_model_name: str,
        collection_name: str = "vietnamese_pdf_chunks",
        embedding_model: SentenceTransformer | None = None,
    ) -> None:
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_model_name = embedding_model_name
        self.embedding_model = embedding_model or SentenceTransformer(embedding_model_name)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(self, chunks: list[TextChunk]) -> int:
        """Embed and add chunks to ChromaDB using deterministic chunk IDs."""
        if not chunks:
            return 0

        ids = [str(chunk.metadata["chunk_id"]) for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        embeddings = _as_list(self.embedding_model.encode(documents, normalize_embeddings=True))

        existing_ids = set(self.collection.get(ids=ids).get("ids", []))
        new_rows = [
            (chunk_id, doc, metadata, embedding)
            for chunk_id, doc, metadata, embedding in zip(ids, documents, metadatas, embeddings, strict=True)
            if chunk_id not in existing_ids
        ]
        if not new_rows:
            logger.info("No new chunks to add to ChromaDB")
            return 0

        new_ids, new_documents, new_metadatas, new_embeddings = zip(*new_rows, strict=True)
        self.collection.add(
            ids=list(new_ids),
            documents=list(new_documents),
            metadatas=list(new_metadatas),
            embeddings=list(new_embeddings),
        )
        logger.info("Added %s chunks to ChromaDB", len(new_ids))
        return len(new_ids)

    def delete_document(self, file_name: str) -> None:
        """Delete all vectors belonging to a PDF file."""
        self.collection.delete(where={"file_name": file_name})
        logger.info("Deleted vectors for %s", file_name)

    def count_document_chunks(self, file_name: str) -> int:
        """Count chunks stored for a PDF file."""
        result = self.collection.get(where={"file_name": file_name}, include=[])
        return len(result.get("ids", []))

    def get_document_chunks(self, file_name: str) -> list[dict[str, Any]]:
        """Return stored chunks for a PDF file."""
        result = self.collection.get(where={"file_name": file_name}, include=["documents", "metadatas"])
        rows: list[dict[str, Any]] = []
        for document, metadata in zip(result.get("documents", []), result.get("metadatas", []), strict=False):
            rows.append({"text": document, "metadata": metadata})
        return rows

    def search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Search ChromaDB and return chunks with documents, metadata, and score."""
        query_embedding = _as_list(self.embedding_model.encode([query], normalize_embeddings=True))[0]
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        rows: list[dict[str, Any]] = []
        for document, metadata, distance in zip(documents, metadatas, distances, strict=False):
            rows.append(
                {
                    "text": document,
                    "metadata": metadata,
                    "score": float(distance) if distance is not None else None,
                }
            )
        return rows
