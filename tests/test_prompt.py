from app.rag.prompt import FALLBACK_ANSWER, build_rag_prompt


def test_prompt_contains_fallback_rule() -> None:
    prompt = build_rag_prompt("Hỏi gì đó?", "")

    assert FALLBACK_ANSWER in prompt
    assert "CHỈ trả lời dựa trên CONTEXT" in prompt
    assert "Không bịa" in prompt
