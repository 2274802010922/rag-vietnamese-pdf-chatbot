from pathlib import Path

from app.documents.registry import DocumentRegistry


def test_registry_tracks_index_metadata(tmp_path: Path) -> None:
    pdf = tmp_path / "tai-lieu.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    registry = DocumentRegistry(tmp_path / "documents.json")

    registry.upsert_upload(pdf)
    record = registry.mark_indexed(
        file_name=pdf.name,
        page_count=3,
        chunk_count=9,
        ocr_used=True,
        text_extraction_method="mixed",
    )

    assert record.indexed is True
    assert record.page_count == 3
    assert record.chunk_count == 9
    assert record.ocr_used is True
    assert registry.list_records()[0].file_name == "tai-lieu.pdf"


def test_registry_upload_marks_existing_document_unindexed(tmp_path: Path) -> None:
    pdf = tmp_path / "cap-nhat.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    registry = DocumentRegistry(tmp_path / "documents.json")

    registry.upsert_upload(pdf)
    registry.mark_indexed(pdf.name, page_count=1, chunk_count=2, ocr_used=False, text_extraction_method="pymupdf")
    registry.upsert_upload(pdf, mark_unindexed=True)

    record = registry.list_records()[0]
    assert record.indexed is False
    assert record.chunk_count == 0


def test_registry_remove_document(tmp_path: Path) -> None:
    pdf = tmp_path / "xoa.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    registry = DocumentRegistry(tmp_path / "documents.json")

    registry.upsert_upload(pdf)
    registry.remove(pdf.name)

    assert registry.list_records() == []
