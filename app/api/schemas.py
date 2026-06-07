from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    ollama_base_url: str
    ollama_model: str


class UploadResponse(BaseModel):
    file_name: str
    saved_path: str


class IndexRequest(BaseModel):
    file_name: str | None = None


class IndexResponse(BaseModel):
    indexed_files: list[str]
    chunks_indexed: int


class DocumentInfo(BaseModel):
    file_name: str
    path: str
    size_bytes: int
    uploaded_at: str | None = None
    indexed: bool = False
    indexed_at: str | None = None
    page_count: int = 0
    chunk_count: int = 0
    ocr_used: bool = False
    text_extraction_method: str = "unknown"


class DeleteDocumentResponse(BaseModel):
    file_name: str
    deleted: bool


class SystemCheckResponse(BaseModel):
    backend: str
    ollama_base_url: str
    ollama_model: str
    ollama_available: bool
    ollama_error: str | None = None
    embedding_model: str
    chroma_db_dir: str
    raw_pdf_dir: str
    ocr: dict[str, Any]


class SearchRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int | None = None


class SourceChunk(BaseModel):
    file_name: str
    page: int
    chunk_id: str
    source: str
    text: str
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    results: list[SourceChunk]


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
