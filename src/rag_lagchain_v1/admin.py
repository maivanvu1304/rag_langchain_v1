from __future__ import annotations

import streamlit as st
from pathlib import Path

from .vectorstore import (
    get_collection_info,
    list_sources, 
    search_by_source,
    delete_by_source,
    clear_collection
)


def admin_page():
    st.title("🔧 Quản lý Vector Store")
    
    # Collection Info
    st.subheader("📊 Thông tin Collection")
    if st.button("Làm mới thông tin"):
        info = get_collection_info()
        if "error" in info:
            st.error(f"Lỗi: {info['error']}")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tổng documents", info["total_documents"])
            with col2:
                st.metric("Vector size", info["vector_size"])
            with col3:
                st.metric("Distance metric", info["distance"])
    
    st.divider()
    
    # List sources
    st.subheader("📂 Danh sách file nguồn")
    sources = list_sources()
    
    if sources:
        st.write(f"Có **{len(sources)}** file trong vector store:")
        
        # Create tabs for different management actions
        tab1, tab2, tab3 = st.tabs(["📋 Xem", "🗑️ Xóa", "🧹 Xóa tất cả"])
        
        with tab1:
            # View documents by source
            selected_source = st.selectbox("Chọn file để xem:", sources, key="view_source")
            if st.button("Xem documents", key="view_docs"):
                docs = search_by_source(selected_source)
                st.write(f"**{len(docs)} documents** từ `{selected_source}`:")
                
                for i, doc in enumerate(docs[:10]):  # Show first 10
                    with st.expander(f"Document {i+1} - Chunk {doc.metadata.get('chunk', 'N/A')}"):
                        st.text(doc.page_content[:500] + ("..." if len(doc.page_content) > 500 else ""))
                        st.json(doc.metadata)
                
                if len(docs) > 10:
                    st.info(f"Chỉ hiển thị 10/{len(docs)} documents đầu tiên")
        
        with tab2:
            # Delete by source
            st.warning("⚠️ Thao tác này sẽ xóa VĨNh VIỄN tất cả documents từ file được chọn!")
            selected_delete = st.selectbox("Chọn file để xóa:", sources, key="delete_source")
            
            if st.button("🗑️ Xóa file này", type="secondary", key="delete_file"):
                with st.spinner("Đang xóa..."):
                    result = delete_by_source(selected_delete)
                    if result:
                        st.success(f"Đã xóa tất cả documents từ `{selected_delete}`")
                        st.rerun()
                    else:
                        st.error("Có lỗi xảy ra khi xóa")
        
        with tab3:
            # Clear all
            st.error("⚠️ NGUY HIỂM: Thao tác này sẽ xóa TẤT CẢ documents trong vector store!")
            
            confirm_text = st.text_input("Nhập 'DELETE ALL' để xác nhận:")
            if confirm_text == "DELETE ALL":
                if st.button("🧹 XÓA TẤT CẢ", type="primary", key="clear_all"):
                    with st.spinner("Đang xóa tất cả..."):
                        if clear_collection():
                            st.success("Đã xóa tất cả documents!")
                            st.rerun()
                        else:
                            st.error("Có lỗi xảy ra khi xóa")
            else:
                st.button("🧹 XÓA TẤT CẢ", disabled=True, key="clear_all_disabled")
    
    else:
        st.info("Không có file nào trong vector store")
    
    st.divider()
    
    # Quick stats
    st.subheader("📈 Thống kê nhanh")
    if sources:
        # Show source file stats
        source_stats = {}
        for source in sources:
            docs = search_by_source(source)
            source_stats[source] = len(docs)
        
        # Display as chart
        import pandas as pd
        df = pd.DataFrame(list(source_stats.items()), columns=['File', 'Documents'])
        st.bar_chart(df.set_index('File'))
        
        # Display as table
        st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    admin_page()
