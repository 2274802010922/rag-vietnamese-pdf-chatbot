from __future__ import annotations

from typing import Any


FALLBACK_ANSWER = "Tôi không tìm thấy thông tin này trong tài liệu."


def build_context(chunks: list[dict[str, Any]]) -> str:
    """Build a grounded context block with source labels for the LLM."""
    lines: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata") or {}
        file_name = metadata.get("file_name", "unknown.pdf")
        page = metadata.get("page", "?")
        text = chunk.get("text", "")
        lines.append(f"[{index}] Nguồn: [{file_name}, trang {page}]\n{text}")
    return "\n\n".join(lines)


def build_rag_prompt(question: str, context: str) -> str:
    """Create the Vietnamese RAG prompt with strict fallback and citation rules."""
    return f"""Bạn là trợ lý hỏi đáp tài liệu PDF tiếng Việt.

CHỈ trả lời dựa trên CONTEXT bên dưới.
Không bịa thông tin ngoài tài liệu.
Nếu CONTEXT không đủ để trả lời câu hỏi, trả lời chính xác:
{FALLBACK_ANSWER}
Luôn trích dẫn nguồn ở dạng [file_name.pdf, trang X] cho các ý trả lời.
Trả lời ngắn gọn, rõ ràng bằng tiếng Việt.

CONTEXT:
{context}

CÂU HỎI:
{question}

TRẢ LỜI:"""
