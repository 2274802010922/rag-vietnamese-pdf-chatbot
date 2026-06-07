from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.documents.registry import DocumentRegistry
from app.ingestion.chunker import chunk_pages
from app.ingestion.pdf_loader import get_pdf_page_count, load_pdf_pages
from app.utils.config import settings
from app.utils.logging import configure_logging
from app.vectorstore.chroma_store import ChromaStore


def rebuild_index() -> int:
    """Rebuild the local ChromaDB index from all PDFs in data/raw_pdfs."""
    configure_logging()
    logger = logging.getLogger(__name__)
    raw_dir = settings.resolve_path(settings.raw_pdf_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(raw_dir.glob("*.pdf"))
    store = ChromaStore(settings.resolve_path(settings.chroma_db_dir), settings.embedding_model)
    registry = DocumentRegistry(settings.resolve_path(settings.document_registry_path))

    total = 0
    for pdf_path in pdfs:
        store.delete_document(pdf_path.name)
        pages = load_pdf_pages(pdf_path)
        chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
        added = store.add_chunks(chunks)
        total += added
        registry.upsert_upload(pdf_path, mark_unindexed=False)
        methods = {str(chunk.metadata.get("page_text_method", "unknown")) for chunk in chunks}
        registry.mark_indexed(
            file_name=pdf_path.name,
            page_count=get_pdf_page_count(pdf_path),
            chunk_count=len(chunks),
            ocr_used=any(chunk.metadata.get("ocr_used") for chunk in chunks),
            text_extraction_method="mixed" if len(methods) > 1 else next(iter(methods), "unknown"),
        )
        logger.info("Indexed %s", pdf_path.name)
    logger.info("Indexed %s chunks from %s PDFs", total, len(pdfs))
    return total


if __name__ == "__main__":
    rebuild_index()
