from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class PageText:
    doc_id: str
    file_name: str
    page: int
    text: str


def load_pdf_pages(pdf_path: str | Path) -> list[PageText]:
    """Extract UTF-8 text page by page from a PDF using PyMuPDF."""
    path = Path(pdf_path)
    doc_id = path.stem
    pages: list[PageText] = []

    with fitz.open(path) as document:
        for index, page in enumerate(document, start=1):
            text = page.get_text("text")
            pages.append(
                PageText(
                    doc_id=doc_id,
                    file_name=path.name,
                    page=index,
                    text=text,
                )
            )
    return pages
