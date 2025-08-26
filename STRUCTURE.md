# Cấu trúc dự án RAG LangChain v1

Dự án đã được tổ chức lại theo cấu trúc modular để dễ quản lý và mở rộng.

## 📁 Cấu trúc thư mục

```
rag_langchain_v1/
├── 📁 src/
│   └── 📁 rag_lagchain_v1/
│       ├── 📁 core/              # Cấu hình và models cốt lõi
│       │   ├── config.py         # Cấu hình ứng dụng
│       │   └── __init__.py
│       ├── 📁 services/          # Business logic
│       │   ├── agent.py          # RAG agent với LangGraph
│       │   ├── ingestion.py      # Xử lý và chia tài liệu
│       │   ├── vectorstore.py    # Quản lý vector store
│       │   └── __init__.py
│       ├── 📁 routers/           # 🔬 Intelligent routing system
│       │   ├── file_router.py    # Smart file routing
│       │   ├── content_analyzer.py # Content analysis & classification
│       │   └── __init__.py
│       ├── 📁 ui/                # Giao diện người dùng
│       │   ├── main_ui.py        # Giao diện chính (Q&A) + Router integration
│       │   ├── admin_ui.py       # Giao diện quản lý
│       │   └── __init__.py
│       ├── 📁 utils/             # Tiện ích chung
│       │   ├── file_processors.py # Xử lý file (PDF, DOCX, etc.)
│       │   └── __init__.py
│       └── __init__.py
├── 📁 tests/                     # Test cases
├── 📁 sample_docs/               # Sample files for testing
├── 📄 app.py                     # Entry point
├── 📄 pyproject.toml            # Dependencies
└── 📄 README.md                 # Tài liệu
```

## 🎯 Phân chia chức năng

### 🔧 Core (`src/rag_lagchain_v1/core/`)

- **config.py**: Quản lý cấu hình ứng dụng từ environment variables
- Chứa các model dữ liệu cốt lõi

### ⚙️ Services (`src/rag_lagchain_v1/services/`)

- **vectorstore.py**:
  - Kết nối và quản lý Qdrant vector database
  - Embedding documents, similarity search
  - CRUD operations cho documents
- **ingestion.py**:
  - Load và split documents thành chunks
  - Quản lý metadata và các loại file khác nhau
- **agent.py**:
  - RAG agent logic với LangGraph
  - Question-answering pipeline

### 🔬 Routers (`src/rag_lagchain_v1/routers/`) ⭐ **NEW**

- **file_router.py**:

  - Intelligent file type detection
  - Smart routing to appropriate handlers
  - Advanced PDF processing (text + tables + images)
  - DOCX text extraction with formatting
  - Error handling và fallback mechanisms
  - Processing statistics tracking

- **content_analyzer.py**:
  - Detailed content type classification:
    - `TEXT_ONLY`: Pure text documents
    - `TEXT_TABLE`: Documents with tables
    - `TEXT_TABLE_IMAGE`: Multimedia documents
    - `STRUCTURED_TEXT`: Documents with headers, lists
    - `MIXED_CONTENT`: Complex combinations
  - Quality scoring và structure analysis
  - Processing strategy recommendations
  - Smart chunk size optimization (200-2000 characters)

### 🖥️ UI (`src/rag_lagchain_v1/ui/`)

- **main_ui.py**: Giao diện chính cho Q&A
- **admin_ui.py**: Giao diện quản lý vector store

### 🛠️ Utils (`src/rag_lagchain_v1/utils/`)

- **file_processors.py**:
  - Xử lý các loại file: PDF, DOCX, TXT, MD
  - Extract text, images, tables từ PDF

## 🚀 Cách chạy

```bash
# Từ thư mục gốc
python app.py

# Hoặc từ module
python -m rag_lagchain_v1.ui
```

## 📦 Import patterns

```python
# Cấu hình
from rag_lagchain_v1.core.config import get_config

# Services
from rag_lagchain_v1.services.vectorstore import similarity_search
from rag_lagchain_v1.services.ingestion import load_and_split
from rag_lagchain_v1.services.agent import build_graph

# UI
from rag_lagchain_v1.ui import app, admin_page

# Utils
from rag_lagchain_v1.utils.file_processors import read_pdf

# Routers
from rag_lagchain_v1.routers import FileRouter, ContentAnalyzer
```

## ✨ Lợi ích của cấu trúc mới

1. **Tách biệt rõ ràng**: Mỗi thư mục có trách nhiệm riêng biệt
2. **Dễ maintain**: Code được tổ chức logic, dễ tìm và sửa
3. **Scalable**: Dễ dàng thêm modules mới
4. **Testable**: Cấu trúc thuận lợi cho việc viết test
5. **Reusable**: Các services có thể được tái sử dụng
6. **Import clean**: Import paths rõ ràng và nhất quán

## 🔄 Migration từ cấu trúc cũ

Tất cả functionality vẫn giữ nguyên, chỉ thay đổi cách tổ chức:

- ✅ Tất cả features hoạt động bình thường
- ✅ API không thay đổi
- ✅ Configuration và environment variables giữ nguyên
- ✅ Dependencies không thay đổi
