from __future__ import annotations

import os

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


def _get_documents() -> list[dict]:
    response = requests.get(f"{BACKEND_BASE_URL}/documents", timeout=30)
    _raise_for_status(response)
    return response.json()


def _post_file(uploaded_file) -> dict:
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
    response = requests.post(f"{BACKEND_BASE_URL}/documents/upload", files=files, timeout=120)
    _raise_for_status(response)
    return response.json()


def _index_documents(file_name: str | None = None) -> dict:
    response = requests.post(
        f"{BACKEND_BASE_URL}/documents/index",
        json={"file_name": file_name},
        timeout=300,
    )
    _raise_for_status(response)
    return response.json()


def _chat(question: str) -> dict:
    response = requests.post(f"{BACKEND_BASE_URL}/chat", json={"question": question}, timeout=300)
    _raise_for_status(response)
    return response.json()


st.set_page_config(page_title="Chatbot PDF tiếng Việt", layout="wide", initial_sidebar_state="expanded")
st.title("Chatbot hỏi đáp tài liệu PDF tiếng Việt")

if "question" not in st.session_state:
    st.session_state.question = SUMMARY_QUESTION

with st.sidebar:
    st.header("Tài liệu")
    uploaded = st.file_uploader("Tải lên PDF", type=["pdf"])

    if uploaded and st.button("Lưu PDF và index", use_container_width=True, type="primary"):
        try:
            upload_result = _post_file(uploaded)
            index_result = _index_documents(upload_result["file_name"])
            if index_result["chunks_indexed"] == 0:
                st.warning("PDF đã lưu nhưng không tạo được chunk mới. Nếu là file scan/ảnh thì cần OCR.")
            else:
                st.success(f"Đã lưu và index {index_result['chunks_indexed']} chunk.")
        except Exception as exc:
            st.error(f"Lỗi upload/index: {exc}")

    if st.button("Index lại toàn bộ PDF", use_container_width=True):
        try:
            result = _index_documents()
            st.success(f"Đã index {result['chunks_indexed']} chunk mới.")
        except Exception as exc:
            st.error(f"Lỗi index: {exc}")

    try:
        documents = _get_documents()
        st.caption(f"Đang có {len(documents)} PDF trong data/raw_pdfs.")
        for document in documents:
            st.caption(f"- {document['file_name']}")
    except Exception:
        st.caption("Chưa kết nối được backend.")

st.subheader("Đặt câu hỏi")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("Tóm tắt tài liệu", use_container_width=True):
        st.session_state.question = SUMMARY_QUESTION
with col2:
    st.caption("Cách test đơn giản: upload PDF -> Lưu PDF và index -> Tóm tắt tài liệu -> Hỏi tài liệu.")

question = st.text_area(
    "Câu hỏi",
    key="question",
    placeholder="Nhập câu hỏi về nội dung trong PDF...",
    height=100,
)

if st.button("Hỏi tài liệu", type="primary") and question.strip():
    try:
        result = _chat(question.strip())
        st.markdown("### Câu trả lời")
        st.write(result["answer"])

        st.markdown("### Nguồn")
        for source in result.get("sources", []):
            file_name = source.get("file_name")
            page = source.get("page")
            text = source.get("text", "")
            with st.expander(f"{file_name}, trang {page}"):
                st.caption(source.get("source", ""))
                st.write(text)
    except Exception as exc:
        st.error(f"Lỗi khi hỏi tài liệu: {exc}")
        st.info("Nếu lỗi nhắc Ollama, chạy: ollama pull qwen2.5:7b. Nếu không có nguồn, hãy upload và index PDF trước.")

st.caption(f"Backend: {BACKEND_BASE_URL}")
