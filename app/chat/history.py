from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ChatTurn:
    question: str
    answer: str
    sources: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def export_chat_markdown(turns: list[ChatTurn]) -> str:
    """Export chat history to Markdown text."""
    lines = ["# Lịch sử chat", ""]
    for index, turn in enumerate(turns, start=1):
        lines.extend(
            [
                f"## Lượt {index}",
                "",
                f"**Thời gian:** {turn.created_at}",
                "",
                f"**Câu hỏi:** {turn.question}",
                "",
                f"**Trả lời:** {turn.answer}",
                "",
                "**Nguồn:**",
            ]
        )
        if turn.sources:
            for source in turn.sources:
                lines.append(f"- {source.get('file_name')}, trang {source.get('page')}: {source.get('source')}")
        else:
            lines.append("- Không có nguồn.")
        lines.append("")
    return "\n".join(lines)
