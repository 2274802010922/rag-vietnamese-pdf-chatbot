from __future__ import annotations

import logging
import shutil
from dataclasses import asdict
from pathlib import Path
from urllib import request as url_request
from urllib.error import URLError

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    DeleteDocumentResponse,
    DocumentInfo,
    HealthResponse,
    IndexRequest,
    IndexResponse,
    SearchRequest,
    SearchResponse,
    SourceChunk,
    SystemCheckResponse,
    UploadResponse,
)
from app.documents.registry import DocumentRecord, DocumentRegistry
from app.ingestion.chunker import chunk_pages
from app.ingestion.ocr import get_ocr_status
from app.ingestion.pdf_loader import get_pdf_page_count, load_pdf_pages
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


def _registry() -> DocumentRegistry:
    return DocumentRegistry(settings.resolve_path(settings.document_registry_path))


def _get_store() -> ChromaStore:
    return ChromaStore(
        persist_dir=settings.resolve_path(settings.chroma_db_dir),
        embedding_model_name=settings.embedding_model,
    )


def _record_to_info(record: DocumentRecord) -> DocumentInfo:
    return DocumentInfo(**asdict(record))


def _sync_registry_with_disk() -> list[DocumentRecord]:
    registry = _registry()
    raw_dir = _raw_pdf_dir()
    records = registry.load()

    for path in sorted(raw_dir.glob("*.pdf")):
        if path.name not in records:
            registry.upsert_upload(path)

    records = registry.load()
    missing = [name for name, record in records.items() if not Path(record.path).exists()]
    for name in missing:
        records.pop(name, None)
    registry.save(records)
    return registry.list_records()


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


@app.get("/system/check", response_model=SystemCheckResponse)
def system_check() -> SystemCheckResponse:
    ollama_available = False
    ollama_error = None
    try:
        with url_request.urlopen(f"{settings.ollama_base_url}/api/tags", timeout=5) as response:
            ollama_available = response.status == 200
    except URLError as exc:
        ollama_error = str(exc)

    return SystemCheckResponse(
        backend="ok",
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        ollama_available=ollama_available,
        ollama_error=ollama_error,
        embedding_model=settings.embedding_model,
        chroma_db_dir=str(settings.resolve_path(settings.chroma_db_dir)),
        raw_pdf_dir=str(settings.resolve_path(settings.raw_pdf_dir)),
        ocr=get_ocr_status(),
    )


@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PDF.")

    target = _raw_pdf_dir() / Path(file.filename).name
    with target.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    _registry().upsert_upload(target)
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
        store.delete_document(pdf_path.name)
        pages = load_pdf_pages(pdf_path)
        chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            logger.warning("No text chunks extracted from %s. The PDF may be scanned.", pdf_path.name)
        added = store.add_chunks(chunks)
        total_chunks += added
        ocr_used = any(chunk.metadata.get("ocr_used") for chunk in chunks)
        methods = {str(chunk.metadata.get("page_text_method", "unknown")) for chunk in chunks}
        method = "mixed" if len(methods) > 1 else next(iter(methods), "unknown")
        _registry().upsert_upload(pdf_path)
        _registry().mark_indexed(
            file_name=pdf_path.name,
            page_count=get_pdf_page_count(pdf_path),
            chunk_count=len(chunks),
            ocr_used=ocr_used,
            text_extraction_method=method,
        )
        indexed_files.append(pdf_path.name)
    return IndexResponse(indexed_files=indexed_files, chunks_indexed=total_chunks)


@app.get("/documents", response_model=list[DocumentInfo])
def list_documents() -> list[DocumentInfo]:
    return [_record_to_info(record) for record in _sync_registry_with_disk()]


@app.delete("/documents/{file_name}", response_model=DeleteDocumentResponse)
def delete_document(file_name: str) -> DeleteDocumentResponse:
    raw_dir = _raw_pdf_dir()
    target = raw_dir / Path(file_name).name
    if not target.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy PDF để xóa.")

    _get_store().delete_document(target.name)
    target.unlink()
    _registry().remove(target.name)
    return DeleteDocumentResponse(file_name=target.name, deleted=True)


@app.post("/documents/{file_name}/reindex", response_model=IndexResponse)
def reindex_document(file_name: str) -> IndexResponse:
    return index_documents(IndexRequest(file_name=Path(file_name).name))


@app.get("/documents/{file_name}/chunks", response_model=SearchResponse)
def document_chunks(file_name: str) -> SearchResponse:
    rows = _get_store().get_document_chunks(Path(file_name).name)
    return SearchResponse(results=[_to_source_chunk(row) for row in rows])


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
