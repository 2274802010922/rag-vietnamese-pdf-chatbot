# Chatbot hỏi đáp tài liệu PDF tiếng Việt dùng RAG local

Project này là Giai đoạn 1 của hệ thống chatbot hỏi đáp tài liệu PDF tiếng Việt sử dụng RAG và mô hình ngôn ngữ lớn chạy cục bộ.

Mục tiêu chính:

- Chạy 100% local trên máy cá nhân.
- Không dùng Docker.
- Không dùng Google Colab.
- Không dùng OpenAI API.
- Không dùng cloud LLM.
- Không dùng Qdrant ở giai đoạn này.
- Dùng Python venv.
- Dùng ChromaDB local để lưu vector.
- Dùng Ollama local để chạy LLM.
- Dùng FastAPI cho backend.
- Dùng Streamlit cho giao diện người dùng.

## Tính năng

- Upload PDF tiếng Việt qua giao diện Streamlit.
- Lưu PDF vào `data/raw_pdfs`.
- Extract text theo từng page bằng PyMuPDF.
- Giữ tiếng Việt có dấu.
- Chunk text có overlap.
- Mỗi chunk có metadata:
  - `doc_id`
  - `file_name`
  - `page`
  - `chunk_id`
  - `source`
- `source` có format: `file_name.pdf#page=X`.
- Tạo embedding bằng `sentence-transformers`.
- Embedding model lấy từ `.env`.
- Lưu vector vào ChromaDB local.
- Search top-k chunks theo câu hỏi.
- Build context từ các chunk tìm được.
- Gọi Ollama local qua HTTP API.
- Trả lời bằng tiếng Việt.
- Dẫn nguồn dạng `[file_name.pdf, trang X]`.
- Nếu không đủ thông tin trong context, trả lời:

```text
Tôi không tìm thấy thông tin này trong tài liệu.
```

## Công nghệ

- Python 3.10+
- FastAPI
- Streamlit
- PyMuPDF
- ChromaDB
- sentence-transformers
- Ollama
- pytest

## Cấu trúc project

```text
rag-vietnamese-pdf-chatbot/
├── app/
│   ├── api/
│   │   ├── main.py
│   │   └── schemas.py
│   ├── ingestion/
│   │   ├── pdf_loader.py
│   │   └── chunker.py
│   ├── rag/
│   │   ├── retriever.py
│   │   ├── prompt.py
│   │   └── pipeline.py
│   ├── llm/
│   │   └── ollama_client.py
│   ├── vectorstore/
│   │   └── chroma_store.py
│   └── utils/
│       ├── config.py
│       └── logging.py
├── ui/
│   └── streamlit_app.py
├── data/
│   ├── raw_pdfs/
│   ├── chroma_db/
│   └── eval/
├── tests/
├── scripts/
│   └── rebuild_index.py
├── requirements.txt
├── .env.example
├── .gitignore
├── PROJECT_RULES.md
└── README.md
```

## Yêu cầu môi trường

Bạn cần cài sẵn:

- Windows, macOS, hoặc Linux
- Python 3.10 trở lên
- Git
- Ollama

Kiểm tra nhanh trên Windows PowerShell:

```powershell
python --version
git --version
ollama --version
```

Nếu `python` không chạy, hãy cài Python từ:

```text
https://www.python.org/downloads/
```

Khi cài Python trên Windows, nên bật tùy chọn `Add python.exe to PATH`.

## Cài Ollama

Tải Ollama tại:

```text
https://ollama.com/download
```

Hoặc trên Windows PowerShell:

```powershell
irm https://ollama.com/install.ps1 | iex
```

Sau khi cài xong, mở terminal mới và kiểm tra:

```powershell
ollama --version
```

Pull model mặc định:

```powershell
ollama pull qwen2.5:7b
```

Kiểm tra model:

```powershell
ollama list
```

Test model:

```powershell
ollama run qwen2.5:7b
```

Nếu model trả lời được, gõ:

```text
/bye
```

## Cài đặt project từ GitHub

Clone repo:

```powershell
git clone https://github.com/2274802010922/rag-vietnamese-pdf-chatbot.git
cd rag-vietnamese-pdf-chatbot
```

Tạo virtual environment:

```powershell
python -m venv .venv
```

Nếu PowerShell chặn activate script, bạn có thể bỏ qua bước activate và chạy Python trực tiếp từ venv. Đây là cách khuyến nghị để ít lỗi trên Windows.

Cài dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Tạo file cấu hình:

```powershell
Copy-Item .env.example .env
```

## Cấu hình

File `.env.example`:

```env
EMBEDDING_MODEL=BAAI/bge-m3
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
CHROMA_DB_DIR=data/chroma_db
RAW_PDF_DIR=data/raw_pdfs
TOP_K=5
CHUNK_SIZE=800
CHUNK_OVERLAP=150
BACKEND_BASE_URL=http://localhost:8000
```

Ý nghĩa:

- `EMBEDDING_MODEL`: model embedding dùng bởi sentence-transformers.
- `OLLAMA_MODEL`: model LLM chạy qua Ollama.
- `OLLAMA_BASE_URL`: địa chỉ Ollama local.
- `CHROMA_DB_DIR`: nơi lưu ChromaDB local.
- `RAW_PDF_DIR`: nơi lưu file PDF upload.
- `TOP_K`: số chunk truy xuất khi hỏi.
- `CHUNK_SIZE`: kích thước chunk theo ký tự.
- `CHUNK_OVERLAP`: số ký tự overlap giữa các chunk.
- `BACKEND_BASE_URL`: URL backend FastAPI để Streamlit gọi.

## Chạy backend

Mở terminal 1:

```powershell
cd rag-vietnamese-pdf-chatbot
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --reload
```

Backend mặc định chạy tại:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

Kiểm tra backend:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Kết quả mẫu:

```json
{
  "status": "ok",
  "ollama_base_url": "http://localhost:11434",
  "ollama_model": "qwen2.5:7b"
}
```

## Chạy UI

Mở terminal 2:

```powershell
cd rag-vietnamese-pdf-chatbot
.\.venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py
```

UI mặc định chạy tại:

```text
http://localhost:8501
```

## Cách dùng đơn giản nhất

1. Chạy Ollama và đảm bảo đã có model:

```powershell
ollama list
```

2. Chạy backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --reload
```

3. Chạy UI:

```powershell
.\.venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py
```

4. Mở:

```text
http://localhost:8501
```

5. Trong UI:

- Upload PDF ở sidebar bên trái.
- Bấm `Lưu PDF và index`.
- Bấm `Tóm tắt tài liệu`.
- Bấm `Hỏi tài liệu`.

Đây là cách test nhanh nhất cho câu hỏi kiểu:

```text
Hãy tóm tắt file
```

## API

### GET /health

Kiểm tra backend đang sống.

```powershell
Invoke-RestMethod http://localhost:8000/health
```

### POST /documents/upload

Upload PDF. Endpoint này thường dùng qua UI.

### POST /documents/index

Index toàn bộ PDF trong `data/raw_pdfs`:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/documents/index `
  -ContentType "application/json" `
  -Body "{}"
```

Index một file cụ thể:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/documents/index `
  -ContentType "application/json" `
  -Body '{"file_name":"ten-file.pdf"}'
```

### GET /documents

Liệt kê PDF đã upload:

```powershell
Invoke-RestMethod http://localhost:8000/documents
```

### POST /search

Search chunk liên quan:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/search `
  -ContentType "application/json" `
  -Body '{"question":"Hãy tóm tắt tài liệu"}' | ConvertTo-Json -Depth 5
```

### POST /chat

Hỏi tài liệu:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/chat `
  -ContentType "application/json" `
  -Body '{"question":"Hãy tóm tắt tài liệu"}'
```

Lưu ý: nếu bạn mở `/chat` trực tiếp trên browser, browser dùng `GET`, FastAPI sẽ trả:

```json
{"detail":"Method Not Allowed"}
```

Điều này bình thường vì `/chat` yêu cầu `POST`.

## Rebuild index bằng script

Nếu đã có PDF trong `data/raw_pdfs`, có thể index lại bằng:

```powershell
.\.venv\Scripts\python.exe scripts\rebuild_index.py
```

## Chạy test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Các test tối thiểu hiện có:

- Chunking giữ metadata.
- Source format đúng `file_name.pdf#page=X`.
- Prompt chứa fallback rule.
- Config load được từ `.env.example`.
- Chroma search trả về metadata.

## Cách tái hiện từ đầu trên máy mới

Quy trình đầy đủ:

```powershell
git clone https://github.com/2274802010922/rag-vietnamese-pdf-chatbot.git
cd rag-vietnamese-pdf-chatbot
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull qwen2.5:7b
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --reload
```

Mở terminal thứ hai:

```powershell
cd rag-vietnamese-pdf-chatbot
.\.venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py
```

Sau đó mở:

```text
http://localhost:8501
```

## Lưu ý về PDF scan

Giai đoạn 1 dùng PyMuPDF để extract text trực tiếp. Nếu PDF là bản scan hoặc ảnh, hệ thống có thể không đọc được chữ.

Cách kiểm tra:

1. Mở PDF.
2. Thử bôi đen và copy một đoạn chữ.
3. Nếu không copy được chữ, PDF có thể là scan.

Với PDF scan, cần thêm OCR ở giai đoạn sau.

## Lỗi thường gặp

### PowerShell không cho activate venv

Lỗi:

```text
running scripts is disabled on this system
```

Cách đơn giản: không cần activate, chạy trực tiếp:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --reload
.\.venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py
```

Hoặc cho phép activate:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### No module named uvicorn hoặc streamlit

Venv chưa cài requirements.

Chạy:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Method Not Allowed

Bạn đang mở endpoint `POST` bằng browser.

Dùng Swagger:

```text
http://localhost:8000/docs
```

Hoặc dùng `Invoke-RestMethod` với `-Method Post`.

### Chat trả 500 hoặc 503

Kiểm tra Ollama:

```powershell
ollama list
```

Nếu thiếu model:

```powershell
ollama pull qwen2.5:7b
```

Test Ollama:

```powershell
ollama run qwen2.5:7b
```

### Trả lời "Tôi không tìm thấy thông tin này trong tài liệu."

Các nguyên nhân thường gặp:

- Chưa bấm `Lưu PDF và index`.
- PDF là bản scan/ảnh.
- Câu hỏi không liên quan đến nội dung PDF.
- Index đang rỗng.

Kiểm tra PDF đã upload:

```powershell
Invoke-RestMethod http://localhost:8000/documents
```

Index lại:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/documents/index `
  -ContentType "application/json" `
  -Body "{}"
```

Search thử:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/search `
  -ContentType "application/json" `
  -Body '{"question":"Hãy tóm tắt tài liệu"}' | ConvertTo-Json -Depth 5
```

## Ghi chú bảo mật và dữ liệu

Repo không commit:

- `.env`
- `.venv`
- PDF upload thật trong `data/raw_pdfs`
- ChromaDB vector store trong `data/chroma_db`
- Cache Python/test

Điều này giúp tránh đẩy dữ liệu riêng tư và file nặng lên GitHub.

## Hướng phát triển tiếp theo

- OCR cho PDF scan.
- Xóa/re-index từng tài liệu.
- Hiển thị lịch sử chat.
- Đánh giá chất lượng retrieval.
- Hỗ trợ nhiều collection.
- Tối ưu prompt theo từng loại tài liệu.
- Thêm reranker cho tiếng Việt.
