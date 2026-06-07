from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_env_file(env_file: str | Path | None) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_file:
        return values

    path = Path(env_file)
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _get_value(key: str, default: str, env_values: dict[str, str]) -> str:
    return os.getenv(key) or env_values.get(key) or default


@dataclass(frozen=True)
class Settings:
    embedding_model: str = "BAAI/bge-m3"
    ollama_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"
    chroma_db_dir: str = "data/chroma_db"
    raw_pdf_dir: str = "data/raw_pdfs"
    top_k: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 150
    backend_base_url: str = "http://localhost:8000"

    @classmethod
    def from_env(cls, env_file: str | Path | None = None) -> "Settings":
        """Load settings from environment variables and an optional .env file."""
        env_values = _load_env_file(env_file or PROJECT_ROOT / ".env")
        return cls(
            embedding_model=_get_value("EMBEDDING_MODEL", cls.embedding_model, env_values),
            ollama_model=_get_value("OLLAMA_MODEL", cls.ollama_model, env_values),
            ollama_base_url=_get_value("OLLAMA_BASE_URL", cls.ollama_base_url, env_values).rstrip("/"),
            chroma_db_dir=_get_value("CHROMA_DB_DIR", cls.chroma_db_dir, env_values),
            raw_pdf_dir=_get_value("RAW_PDF_DIR", cls.raw_pdf_dir, env_values),
            top_k=int(_get_value("TOP_K", str(cls.top_k), env_values)),
            chunk_size=int(_get_value("CHUNK_SIZE", str(cls.chunk_size), env_values)),
            chunk_overlap=int(_get_value("CHUNK_OVERLAP", str(cls.chunk_overlap), env_values)),
            backend_base_url=_get_value("BACKEND_BASE_URL", cls.backend_base_url, env_values).rstrip("/"),
        )

    def resolve_path(self, path_value: str) -> Path:
        """Resolve a configured relative path from the project root."""
        path = Path(path_value)
        return path if path.is_absolute() else PROJECT_ROOT / path


settings = Settings.from_env()
