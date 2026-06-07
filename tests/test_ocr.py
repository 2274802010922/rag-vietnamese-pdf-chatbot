from app.ingestion.chunker import chunk_pages
from app.ingestion.ocr import get_ocr_status
from app.ingestion.pdf_loader import PageText


def test_ocr_status_shape() -> None:
    status = get_ocr_status()

    assert status["engine"] == "tesseract"
    assert "available" in status
    assert "install_hint" in status


def test_chunk_metadata_includes_ocr_fields() -> None:
    chunks = chunk_pages(
        [
            PageText(
                doc_id="scan",
                file_name="scan.pdf",
                page=1,
                text="Nội dung OCR tiếng Việt.",
                ocr_used=True,
                page_text_method="ocr",
            )
        ],
        chunk_size=100,
        chunk_overlap=10,
    )

    assert chunks[0].metadata["ocr_used"] is True
    assert chunks[0].metadata["page_text_method"] == "ocr"
