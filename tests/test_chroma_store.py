import pytest

from app.ingestion.chunker import TextChunk


class FakeEmbeddingModel:
    def encode(self, texts, normalize_embeddings=True):
        vectors = []
        for text in texts:
            marker = 1.0 if "Việt Nam" in text else 0.0
            vectors.append([marker, 1.0 - marker, 0.0])
        return vectors


def test_chroma_search_returns_metadata(tmp_path) -> None:
    pytest.importorskip("chromadb")
    from app.vectorstore.chroma_store import ChromaStore

    store = ChromaStore(
        persist_dir=tmp_path / "chroma",
        embedding_model_name="fake",
        embedding_model=FakeEmbeddingModel(),
    )
    store.add_chunks(
        [
            TextChunk(
                text="Thông tin về Việt Nam.",
                metadata={
                    "doc_id": "doc",
                    "file_name": "doc.pdf",
                    "page": 1,
                    "chunk_id": "doc-p1-c0",
                    "source": "doc.pdf#page=1",
                },
            )
        ]
    )

    results = store.search("Việt Nam", top_k=1)

    assert results[0]["metadata"]["file_name"] == "doc.pdf"
    assert results[0]["metadata"]["source"] == "doc.pdf#page=1"
