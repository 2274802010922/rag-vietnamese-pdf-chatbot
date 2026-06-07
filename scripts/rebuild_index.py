from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.chunker import chunk_pages
from app.ingestion.pdf_loader import load_pdf_pages
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

    total = 0
    for pdf_path in pdfs:
        pages = load_pdf_pages(pdf_path)
        chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
        total += store.add_chunks(chunks)
        logger.info("Indexed %s", pdf_path.name)
    logger.info("Indexed %s chunks from %s PDFs", total, len(pdfs))
    return total


if __name__ == "__main__":
    rebuild_index()
