# Project Rules

- Chạy 100% local, không dùng Docker, Colab, OpenAI API, cloud LLM, hoặc Qdrant ở Giai đoạn 1.
- Dùng Python venv, ChromaDB local, Ollama local, FastAPI backend, Streamlit UI.
- Không hard-code model, path, port trong logic chính; lấy từ `.env` hoặc config.
- Trả lời tiếng Việt và chỉ dựa trên context truy xuất từ tài liệu.
- Nếu context không đủ, dùng đúng fallback: `Tôi không tìm thấy thông tin này trong tài liệu.`
- Mọi câu trả lời có thông tin từ tài liệu phải dẫn nguồn dạng `[file_name.pdf, trang X]`.
- Dùng logging thay vì print trong code ứng dụng.
- Public functions cần type hints; hàm quan trọng cần docstring.
