from app.ingestion.chunker import chunk_pages
from app.ingestion.pdf_loader import PageText


def test_chunking_keeps_required_metadata() -> None:
    pages = [
        PageText(
            doc_id="tai-lieu",
            file_name="tai-lieu.pdf",
            page=2,
            text="Tiếng Việt có dấu. " * 80,
        )
    ]

    chunks = chunk_pages(pages, chunk_size=120, chunk_overlap=20)

    assert chunks
    metadata = chunks[0].metadata
    assert metadata["doc_id"] == "tai-lieu"
    assert metadata["file_name"] == "tai-lieu.pdf"
    assert metadata["page"] == 2
    assert metadata["chunk_id"].startswith("tai-lieu-p2-c")
    assert metadata["source"] == "tai-lieu.pdf#page=2"
    assert "Tiếng Việt có dấu" in chunks[0].text


def test_source_format() -> None:
    chunks = chunk_pages(
        [PageText(doc_id="a", file_name="file.pdf", page=1, text="Nội dung thử nghiệm dài.")],
        chunk_size=50,
        chunk_overlap=10,
    )

    assert chunks[0].metadata["source"] == "file.pdf#page=1"
