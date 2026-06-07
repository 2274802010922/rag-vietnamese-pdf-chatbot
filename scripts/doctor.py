from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from urllib import request
from urllib.error import URLError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.ocr import get_ocr_status
from app.utils.config import Settings


def _module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def run_doctor() -> dict:
    """Check local runtime prerequisites for the project."""
    settings = Settings.from_env(PROJECT_ROOT / ".env")
    ollama_available = False
    ollama_error = None
    try:
        with request.urlopen(f"{settings.ollama_base_url}/api/tags", timeout=5) as response:
            ollama_available = response.status == 200
    except URLError as exc:
        ollama_error = str(exc)

    checks = {
        "python": sys.version,
        "project_root": str(PROJECT_ROOT),
        "config": {
            "embedding_model": settings.embedding_model,
            "ollama_model": settings.ollama_model,
            "ollama_base_url": settings.ollama_base_url,
            "raw_pdf_dir": str(settings.resolve_path(settings.raw_pdf_dir)),
            "chroma_db_dir": str(settings.resolve_path(settings.chroma_db_dir)),
            "document_registry_path": str(settings.resolve_path(settings.document_registry_path)),
        },
        "modules": {
            "fastapi": _module_available("fastapi"),
            "streamlit": _module_available("streamlit"),
            "fitz": _module_available("fitz"),
            "chromadb": _module_available("chromadb"),
            "sentence_transformers": _module_available("sentence_transformers"),
            "pytesseract": _module_available("pytesseract"),
        },
        "executables": {
            "git": shutil.which("git"),
            "ollama": shutil.which("ollama"),
            "tesseract": shutil.which("tesseract"),
        },
        "ollama": {
            "available": ollama_available,
            "error": ollama_error,
            "hint": f"Nếu chưa có model, chạy: ollama pull {settings.ollama_model}",
        },
        "ocr": get_ocr_status(),
    }
    return checks


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(run_doctor(), ensure_ascii=False, indent=2))
