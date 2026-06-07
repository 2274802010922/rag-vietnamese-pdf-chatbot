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
