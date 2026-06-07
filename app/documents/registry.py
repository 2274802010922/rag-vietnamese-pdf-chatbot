from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DocumentRecord:
    file_name: str
    path: str
    size_bytes: int
    uploaded_at: str
    indexed: bool = False
    indexed_at: str | None = None
    page_count: int = 0
    chunk_count: int = 0
    ocr_used: bool = False
    text_extraction_method: str = "unknown"


class DocumentRegistry:
    """JSON-backed registry for uploaded and indexed PDFs."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, DocumentRecord]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {name: DocumentRecord(**record) for name, record in raw.items()}

    def save(self, records: dict[str, DocumentRecord]) -> None:
        payload: dict[str, dict[str, Any]] = {name: asdict(record) for name, record in records.items()}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert_upload(self, file_path: Path, mark_unindexed: bool = True) -> DocumentRecord:
        records = self.load()
        existing = records.get(file_path.name)
        if mark_unindexed or not existing:
            indexed = False
            indexed_at = None
            page_count = 0
            chunk_count = 0
            ocr_used = False
            text_extraction_method = "unknown"
        else:
            indexed = existing.indexed
            indexed_at = existing.indexed_at
            page_count = existing.page_count
            chunk_count = existing.chunk_count
            ocr_used = existing.ocr_used
            text_extraction_method = existing.text_extraction_method

        record = DocumentRecord(
            file_name=file_path.name,
            path=str(file_path),
            size_bytes=file_path.stat().st_size,
            uploaded_at=existing.uploaded_at if existing else utc_now_iso(),
            indexed=indexed,
            indexed_at=indexed_at,
            page_count=page_count,
            chunk_count=chunk_count,
            ocr_used=ocr_used,
            text_extraction_method=text_extraction_method,
        )
        records[file_path.name] = record
        self.save(records)
        return record

    def mark_indexed(
        self,
        file_name: str,
        page_count: int,
        chunk_count: int,
        ocr_used: bool,
        text_extraction_method: str,
    ) -> DocumentRecord:
        records = self.load()
        record = records[file_name]
        record.indexed = chunk_count > 0
        record.indexed_at = utc_now_iso()
        record.page_count = page_count
        record.chunk_count = chunk_count
        record.ocr_used = ocr_used
        record.text_extraction_method = text_extraction_method
        records[file_name] = record
        self.save(records)
        return record

    def remove(self, file_name: str) -> None:
        records = self.load()
        records.pop(file_name, None)
        self.save(records)

    def list_records(self) -> list[DocumentRecord]:
        return sorted(self.load().values(), key=lambda item: item.file_name.lower())
