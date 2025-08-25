## RAG LangGraph v1

Ứng dụng RAG sử dụng LangChain + LangGraph, lưu trữ vector trên Qdrant và giao diện Streamlit.

### Cài đặt

1. Cài Poetry, sau đó:

```bash
poetry install
```

2. Khởi chạy Qdrant (Docker):

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

3. Cấu hình biến môi trường (tùy chọn):

```bash
set QDRANT_URL=http://localhost:6333
set QDRANT_COLLECTION=my_documents1
set EMBEDDING_MODEL=text-embedding-3-small
set LLM_PROVIDER=openai
set OPENAI_MODEL=gpt-4o-mini
set OPENAI_API_KEY=sk-...
```

### Chạy ứng dụng

```bash
poetry run streamlit run app.py
```

### Tính năng

- Tải lên .pdf/.docx/.txt/.md
- Trích xuất hình ảnh và bảng từ PDF với metadata
- Tách đoạn đệ quy, cấu hình chunk size/overlap
- Vector hóa bằng OpenAI Embeddings, lưu Qdrant
- Hỏi đáp RAG, sinh câu trả lời kèm trích dẫn metadata
- Hiển thị bảng khi hỏi về "bảng", "tác động", "khu vực", "loại"
- Hiển thị hình ảnh khi hỏi về "hình ảnh", "thực tế", "vùng ảnh hưởng"
- Quản lý vector store: xem, xóa theo file, xóa tất cả, thống kê
