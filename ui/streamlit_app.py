from __future__ import annotations

import os
from datetime import datetime
from urllib.parse import quote

import requests
import streamlit as st


BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")
SUMMARY_QUESTION = "Hãy tóm tắt ngắn gọn nội dung chính của tài liệu."


def _raise_for_status(response: requests.Response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text
        raise RuntimeError(detail or str(exc)) from exc


def _get(path: str, timeout: int = 30):
    response = requests.get(f"{BACKEND_BASE_URL}{path}", timeout=timeout)
    _raise_for_status(response)
    return response.json()


def _post(path: str, payload: dict | None = None, timeout: int = 300):
    response = requests.post(f"{BACKEND_BASE_URL}{path}", json=payload or {}, timeout=timeout)
    _raise_for_status(response)
    return response.json()


def _delete(path: str, timeout: int = 120):
    response = requests.delete(f"{BACKEND_BASE_URL}{path}", timeout=timeout)
    _raise_for_status(response)
    return response.json()


def _post_file(uploaded_file) -> dict:
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
    response = requests.post(f"{BACKEND_BASE_URL}/documents/upload", files=files, timeout=120)
    _raise_for_status(response)
    return response.json()


def _chat(question: str) -> dict:
    return _post("/chat", {"question": question}, timeout=300)


def _export_history() -> str:
    lines = ["# Lịch sử chat", ""]
    for index, item in enumerate(st.session_state.chat_history, start=1):
        lines.extend(
            [
                f"## Lượt {index}",
                "",
                f"**Thời gian:** {item['created_at']}",
                "",
                f"**Câu hỏi:** {item['question']}",
                "",
                f"**Trả lời:** {item['answer']}",
                "",
                "**Nguồn:**",
            ]
        )
        for source in item.get("sources", []):
            lines.append(f"- {source.get('file_name')}, trang {source.get('page')}: {source.get('source')}")
        if not item.get("sources"):
            lines.append("- Không có nguồn.")
        lines.append("")
    return "\n".join(lines)


st.set_page_config(page_title="Chatbot PDF tiếng Việt", layout="wide", initial_sidebar_state="expanded")
st.title("Chatbot hỏi đáp tài liệu PDF tiếng Việt")

if "question" not in st.session_state:
    st.session_state.question = SUMMARY_QUESTION
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header("Hệ thống")
    if st.button("Kiểm tra hệ thống", use_container_width=True):
        try:
            status = _get("/system/check")
            st.success("Backend OK")
            st.write(f"Ollama: {'OK' if status['ollama_available'] else 'Chưa kết nối'}")
            st.write(f"Model: {status['ollama_model']}")
            st.write(f"OCR: {'OK' if status['ocr']['available'] else 'Chưa sẵn sàng'}")
            if not status["ollama_available"]:
                st.warning("Hãy mở Ollama và chạy: ollama pull qwen2.5:7b")
            if not status["ocr"]["available"]:
                st.info("OCR là tùy chọn. PDF scan cần Tesseract + language pack vie.")
        except Exception as exc:
            st.error(f"Không kiểm tra được hệ thống: {exc}")

    st.header("Tài liệu")
    uploaded = st.file_uploader("Tải lên PDF", type=["pdf"])

    if uploaded and st.button("Lưu PDF và index", use_container_width=True, type="primary"):
        try:
            with st.spinner("Đang lưu và index tài liệu..."):
                upload_result = _post_file(uploaded)
                index_result = _post("/documents/index", {"file_name": upload_result["file_name"]})
            if index_result["chunks_indexed"] == 0:
                st.warning("PDF đã lưu nhưng không tạo được chunk mới. Nếu là file scan/ảnh thì cần OCR.")
            else:
                st.success(f"Đã lưu và index {index_result['chunks_indexed']} chunk.")
        except Exception as exc:
            st.error(f"Lỗi upload/index: {exc}")

    if st.button("Index lại toàn bộ PDF", use_container_width=True):
        try:
            with st.spinner("Đang index lại toàn bộ..."):
                result = _post("/documents/index")
            st.success(f"Đã index {result['chunks_indexed']} chunk mới.")
        except Exception as exc:
            st.error(f"Lỗi index: {exc}")

    st.subheader("Danh sách PDF")
    try:
        documents = _get("/documents")
        if not documents:
            st.caption("Chưa có PDF.")
        for document in documents:
            label = f"{document['file_name']} ({document['chunk_count']} chunk)"
            with st.expander(label):
                st.caption(f"Trang: {document['page_count']}")
                st.caption(f"Indexed: {'Có' if document['indexed'] else 'Chưa'}")
                st.caption(f"OCR: {'Có' if document['ocr_used'] else 'Không'}")
                st.caption(f"Method: {document['text_extraction_method']}")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Re-index", key=f"reindex-{document['file_name']}", use_container_width=True):
                        try:
                            _post(f"/documents/{quote(document['file_name'])}/reindex")
                            st.success("Đã re-index.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                with col_b:
                    if st.button("Xóa", key=f"delete-{document['file_name']}", use_container_width=True):
                        try:
                            _delete(f"/documents/{quote(document['file_name'])}")
                            st.success("Đã xóa.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
    except Exception as exc:
        st.caption(f"Chưa kết nối được backend: {exc}")

st.subheader("Chat")

actions = st.columns([1, 1, 1, 5])
with actions[0]:
    if st.button("Tóm tắt", use_container_width=True):
        st.session_state.question = SUMMARY_QUESTION
with actions[1]:
    if st.button("Xóa chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
with actions[2]:
    st.download_button(
        "Export MD",
        data=_export_history(),
        file_name="chat_history.md",
        mime="text/markdown",
        use_container_width=True,
    )

for item in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(item["question"])
    with st.chat_message("assistant"):
        st.write(item["answer"])
        if item.get("sources"):
            with st.expander("Nguồn"):
                for source in item["sources"]:
                    st.markdown(f"**{source.get('file_name')}, trang {source.get('page')}**")
                    st.caption(source.get("source", ""))
                    st.write(source.get("text", ""))

question = st.text_area(
    "Câu hỏi",
    key="question",
    placeholder="Nhập câu hỏi về nội dung trong PDF...",
    height=100,
)

if st.button("Hỏi tài liệu", type="primary") and question.strip():
    try:
        with st.spinner("Đang truy xuất tài liệu và gọi Ollama..."):
            result = _chat(question.strip())
        st.session_state.chat_history.append(
            {
                "question": question.strip(),
                "answer": result["answer"],
                "sources": result.get("sources", []),
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        st.rerun()
    except Exception as exc:
        st.error(f"Lỗi khi hỏi tài liệu: {exc}")
        st.info("Nếu lỗi nhắc Ollama, chạy: ollama pull qwen2.5:7b. Nếu không có nguồn, hãy upload và index PDF trước.")

st.caption(f"Backend: {BACKEND_BASE_URL}")
