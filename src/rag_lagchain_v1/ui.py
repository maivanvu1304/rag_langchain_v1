from __future__ import annotations

import streamlit as st
from pathlib import Path

from .config import get_config
from .ingestion import load_and_split
from .vectorstore import index_documents, similarity_search
from .agent import build_graph, RAGState
from .admin import admin_page


def app():
    st.set_page_config(page_title="RAG LangGraph App", page_icon="🤖")
    
    # Sidebar navigation
    st.sidebar.title("🤖 RAG Navigator")
    page = st.sidebar.radio(
        "Chọn trang:",
        ["📝 Q&A", "🔧 Quản lý"],
        index=0
    )
    
    if page == "🔧 Quản lý":
        admin_page()
        return
    
    # Main Q&A page
    st.title("RAG Q&A với LangChain + LangGraph + Qdrant")

    cfg = get_config()

    with st.expander("Cấu hình"):
        st.write(
            {
                "Qdrant": cfg.qdrant_url,
                "Collection": cfg.qdrant_collection,
                "Embedding": cfg.embedding_model,
                "LLM": cfg.openai_model,
            }
        )

    st.subheader("Tải lên tài liệu")
    uploaded_files = st.file_uploader(
        "Chọn file (.pdf, .docx, .txt, .md)",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt", "md"],
    )

    if uploaded_files and st.button("Nạp & Lập chỉ mục"):
        total = 0
        with st.spinner("Đang xử lý..."):
            items = []
            for f in uploaded_files:
                chunks = load_and_split(
                    f.name,
                    f.read(),
                    chunk_size=cfg.chunk_size,
                    chunk_overlap=cfg.chunk_overlap,
                )
                items.extend(chunks)
            total = index_documents(items)
        st.success(f"Đã lập chỉ mục {total} chunks")

    st.subheader("Hỏi đáp")
    question = st.text_input("Câu hỏi của bạn")
    if st.button("Hỏi") and question:
        graph = build_graph()
        state = RAGState(question=question)
        with st.spinner("Đang tạo câu trả lời..."):
            result = graph.invoke(state)
        
        st.markdown("**Câu trả lời:**")
        st.write(result["answer"])
        
        # Get context documents to check for multimedia content
        docs = similarity_search(question, k=5)
        
        # Show tables if question mentions relevant keywords
        if any(keyword in question.lower() for keyword in ["bảng", "table", "tác động", "bbkh", "khu vực", "loại"]):
            tables_found = []
            for doc in docs:
                if "tables" in doc.metadata:
                    tables_found.extend(doc.metadata["tables"])
            
            if tables_found:
                st.markdown("**Bảng liên quan:**")
                for i, table_dict in enumerate(tables_found[:3]):  # Limit to 3 tables
                    st.markdown(f"**Bảng {i+1} (Trang {table_dict['page']}):**")
                    st.dataframe(table_dict['data'], use_container_width=True)
        
        # Show images if question mentions relevant keywords
        if any(keyword in question.lower() for keyword in ["hình", "ảnh", "thực tế", "vùng", "ảnh hưởng"]):
            images_found = []
            for doc in docs:
                if "images" in doc.metadata:
                    images_found.extend(doc.metadata["images"])
            
            if images_found:
                st.markdown("**Hình ảnh liên quan:**")
                cols = st.columns(min(len(images_found), 3))
                for i, img_path in enumerate(images_found[:6]):  # Limit to 6 images
                    if Path(img_path).exists():
                        with cols[i % 3]:
                            st.image(img_path, caption=Path(img_path).name, width=200)
                    else:
                        st.warning(f"Không tìm thấy file hình ảnh: {img_path}")


if __name__ == "__main__":
    app()
