from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.ingestion.pdf_loader import PageText


@dataclass(frozen=True)
class TextChunk:
    text: str
    metadata: dict[str, Any]


def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving Vietnamese characters and accents."""
    return re.sub(r"\s+", " ", text).strip()


def chunk_pages(
    pages: list[PageText],
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    """Split page text into overlapping character chunks with required metadata."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size")

    chunks: list[TextChunk] = []
    for page in pages:
        text = normalize_text(page.text)
        if not text:
            continue

        start = 0
        local_index = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_id = f"{page.doc_id}-p{page.page}-c{local_index}"
                source = f"{page.file_name}#page={page.page}"
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        metadata={
                            "doc_id": page.doc_id,
                            "file_name": page.file_name,
                            "page": page.page,
                            "chunk_id": chunk_id,
                            "source": source,
                        },
                    )
                )
            if end == len(text):
                break
            start = end - chunk_overlap
            local_index += 1
    return chunks
