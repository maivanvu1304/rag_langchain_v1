from __future__ import annotations

import streamlit as st
from pathlib import Path

from ..core.config import get_config
from ..services.ingestion import load_and_split
from ..services.vectorstore import index_documents, similarity_search
from ..services.agent import build_graph, RAGState
from .admin_ui import admin_page


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
        total_files = len(uploaded_files)
        
        with st.spinner("Đang xử lý tài liệu..."):
            try:
                items = []
                processing_info = []
                
                # Sử dụng intelligent router để phân tích files
                from ..routers import FileRouter, ContentAnalyzer
                
                router = FileRouter()
                analyzer = ContentAnalyzer()
                
                for f in uploaded_files:
                    file_ext = f.name.lower().split('.')[-1]
                    
                    # Router analysis
                    file_bytes = f.read()
                    processing_result = router.route_file(f.name, file_bytes)
                    
                    if processing_result.success:
                        # Content analysis
                        content_analysis = analyzer.analyze_content(processing_result)
                        
                        # Smart chunking based on analysis
                        recommended_size = content_analysis.recommended_chunk_size
                        chunks = load_and_split(
                            f.name,
                            file_bytes,
                            chunk_size=recommended_size,
                            chunk_overlap=min(cfg.chunk_overlap, recommended_size // 4),
                        )
                        
                        items.extend(chunks)
                        
                        # Detailed processing info
                        processing_info.append({
                            'name': f.name,
                            'type': file_ext.upper(),
                            'chunks': len(chunks),
                            'size': f.size,
                            'content_type': content_analysis.content_type.value,
                            'quality_score': content_analysis.text_quality_score,
                            'has_tables': content_analysis.has_tables,
                            'has_images': content_analysis.has_images,
                            'recommended_size': recommended_size,
                            'processing_method': processing_result.metadata.get('processing_method', 'unknown')
                        })
                    else:
                        # Fallback to simple processing
                        chunks = load_and_split(
                            f.name,
                            file_bytes,
                            chunk_size=cfg.chunk_size,
                            chunk_overlap=cfg.chunk_overlap,
                        )
                        
                        items.extend(chunks)
                        
                        processing_info.append({
                            'name': f.name,
                            'type': file_ext.upper(),
                            'chunks': len(chunks),
                            'size': f.size,
                            'content_type': 'error',
                            'error': processing_result.error
                        })
                
                # Index tất cả chunks
                if items:
                    total = index_documents(items)
                    
                    # Hiển thị kết quả chi tiết
                    st.success(f"🎉 Đã xử lý {total_files} files và lập chỉ mục {total} chunks")
                    
                    # Bảng thông tin chi tiết với router analysis
                    if processing_info:
                        st.subheader("📊 Chi tiết xử lý với Router Analysis")
                        
                        for info in processing_info:
                            # File header
                            st.markdown(f"### 📄 {info['name']}")
                            
                            # Basic info
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("File Type", info['type'])
                            with col2:
                                st.metric("Chunks", info['chunks'])
                            with col3:
                                st.metric("Size", f"{info['size']/1024:.1f} KB")
                            with col4:
                                if 'quality_score' in info:
                                    st.metric("Quality", f"{info['quality_score']:.1%}")
                            
                            # Advanced analysis (if available)
                            if 'content_type' in info and info['content_type'] != 'error':
                                col5, col6, col7, col8 = st.columns(4)
                                with col5:
                                    content_type_display = info['content_type'].replace('_', ' ').title()
                                    st.info(f"📋 Content: {content_type_display}")
                                with col6:
                                    if info.get('has_tables'):
                                        st.success("📊 Has Tables")
                                    else:
                                        st.write("📊 No Tables")
                                with col7:
                                    if info.get('has_images'):
                                        st.success("🖼️ Has Images")
                                    else:
                                        st.write("🖼️ No Images")
                                with col8:
                                    if 'recommended_size' in info:
                                        st.info(f"📏 Chunk: {info['recommended_size']}")
                                
                                # Processing method
                                if 'processing_method' in info:
                                    st.caption(f"🔧 Method: {info['processing_method']}")
                            
                            elif 'error' in info:
                                st.error(f"❌ Error: {info['error']}")
                            
                            st.divider()
                    
                    st.info("🔬 Files được xử lý với Router System thông minh:\n"
                            "- Phân loại tự động theo content type\n" 
                            "- Routing đến handler phù hợp\n"
                            "- Phân tích chất lượng và cấu trúc\n"
                            "- Tối ưu chunk size theo content type")
                    
                else:
                    st.error("❌ Không có chunks nào được tạo")
                    
            except Exception as e:
                st.error(f"❌ Lỗi xử lý: {str(e)}")
                st.write("Chi tiết lỗi:", str(e))

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
