from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz

from app.ingestion.ocr import OcrResult, extract_page_with_ocr, is_tesseract_available


@dataclass(frozen=True)
class PageText:
    doc_id: str
    file_name: str
    page: int
    text: str
    ocr_used: bool = False
    page_text_method: str = "pymupdf"


def load_pdf_pages(
    pdf_path: str | Path,
    use_ocr: bool = True,
    min_text_chars: int = 30,
) -> list[PageText]:
    """Extract UTF-8 text page by page from a PDF, falling back to OCR when useful."""
    path = Path(pdf_path)
    doc_id = path.stem
    pages: list[PageText] = []

    with fitz.open(path) as document:
        for index, page in enumerate(document, start=1):
            text = page.get_text("text")
            ocr_result: OcrResult | None = None
            if use_ocr and len(text.strip()) < min_text_chars:
                ocr_result = extract_page_with_ocr(page) if is_tesseract_available() else None
                if ocr_result and ocr_result.text.strip():
                    text = ocr_result.text
            pages.append(
                PageText(
                    doc_id=doc_id,
                    file_name=path.name,
                    page=index,
                    text=text,
                    ocr_used=bool(ocr_result and ocr_result.text.strip()),
                    page_text_method="ocr" if ocr_result and ocr_result.text.strip() else "pymupdf",
                )
            )
    return pages


def get_pdf_page_count(pdf_path: str | Path) -> int:
    """Return the number of pages in a PDF."""
    with fitz.open(Path(pdf_path)) as document:
        return int(document.page_count)
