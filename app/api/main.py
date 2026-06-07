from __future__ import annotations

import logging
import shutil
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentInfo,
    HealthResponse,
    IndexRequest,
    IndexResponse,
    SearchRequest,
    SearchResponse,
    SourceChunk,
    UploadResponse,
)
from app.ingestion.chunker import chunk_pages
from app.ingestion.pdf_loader import load_pdf_pages
from app.llm.ollama_client import OllamaClient, OllamaError
from app.rag.pipeline import RagPipeline
from app.rag.retriever import Retriever
from app.utils.config import settings
from app.utils.logging import configure_logging
from app.vectorstore.chroma_store import ChromaStore

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title="Vietnamese PDF RAG Chatbot", version="0.1.0")


def _raw_pdf_dir() -> Path:
    path = settings.resolve_path(settings.raw_pdf_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_store() -> ChromaStore:
    return ChromaStore(
        persist_dir=settings.resolve_path(settings.chroma_db_dir),
        embedding_model_name=settings.embedding_model,
    )


def _to_source_chunk(row: dict) -> SourceChunk:
    metadata = row.get("metadata") or {}
    return SourceChunk(
        file_name=str(metadata.get("file_name", "")),
        page=int(metadata.get("page", 0)),
        chunk_id=str(metadata.get("chunk_id", "")),
        source=str(metadata.get("source", "")),
        text=str(row.get("text", "")),
        score=row.get("score"),
        metadata=metadata,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
    )


@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PDF.")

    target = _raw_pdf_dir() / Path(file.filename).name
    with target.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    logger.info("Saved uploaded PDF: %s", target)
    return UploadResponse(file_name=target.name, saved_path=str(target))


@app.post("/documents/index", response_model=IndexResponse)
def index_documents(request: IndexRequest) -> IndexResponse:
    raw_dir = _raw_pdf_dir()
    pdfs = [raw_dir / request.file_name] if request.file_name else sorted(raw_dir.glob("*.pdf"))
    pdfs = [path for path in pdfs if path.exists() and path.suffix.lower() == ".pdf"]
    if not pdfs:
        raise HTTPException(status_code=404, detail="Không tìm thấy PDF để index.")

    store = _get_store()
    indexed_files: list[str] = []
    total_chunks = 0
    for pdf_path in pdfs:
        pages = load_pdf_pages(pdf_path)
        chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            logger.warning("No text chunks extracted from %s. The PDF may be scanned.", pdf_path.name)
        total_chunks += store.add_chunks(chunks)
        indexed_files.append(pdf_path.name)
    return IndexResponse(indexed_files=indexed_files, chunks_indexed=total_chunks)


@app.get("/documents", response_model=list[DocumentInfo])
def list_documents() -> list[DocumentInfo]:
    raw_dir = _raw_pdf_dir()
    return [
        DocumentInfo(file_name=path.name, path=str(path), size_bytes=path.stat().st_size)
        for path in sorted(raw_dir.glob("*.pdf"))
    ]


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    retriever = Retriever(_get_store(), top_k=settings.top_k)
    rows = retriever.search(request.question, top_k=request.top_k)
    return SearchResponse(results=[_to_source_chunk(row) for row in rows])


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        retriever = Retriever(_get_store(), top_k=settings.top_k)
        client = OllamaClient(settings.ollama_base_url, settings.ollama_model)
        pipeline = RagPipeline(retriever, client)
        result = pipeline.answer(request.question, top_k=request.top_k)
    except OllamaError as exc:
        logger.exception("Ollama error")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Chat failed")
        raise HTTPException(
            status_code=500,
            detail=(
                "Không xử lý được câu hỏi. Hãy kiểm tra đã upload/index PDF, "
                "embedding model tải thành công, và Ollama đang chạy."
            ),
        ) from exc
    return ChatResponse(
        answer=result["answer"],
        sources=[_to_source_chunk(row) for row in result["sources"]],
    )
