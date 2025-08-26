from __future__ import annotations

from typing import Dict, List, Any

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from ..core.config import get_config
from .vectorstore import similarity_search


class RAGState(BaseModel):
    question: str
    context: List[Document] = Field(default_factory=list)
    answer: str | None = None


def retrieve_node(state: RAGState) -> RAGState:
    docs = similarity_search(state.question, k=5)
    return RAGState(question=state.question, context=docs)


def generate_node(state: RAGState) -> RAGState:
    cfg = get_config()
    llm = ChatOpenAI(model=cfg.openai_model, temperature=0)
    system = """Bạn là một trợ lý AI thông minh, chuyên trả lời câu hỏi dựa trên thông tin được cung cấp.

        QUY TẮC BẮT BUỘC:
        1. CHỈ SỬ DỤNG thông tin từ các đoạn văn bản được cung cấp trong phần "Ngữ cảnh" để trả lời câu hỏi.
        2. TUYỆT ĐỐI KHÔNG ĐƯỢC BỊA ĐẶT thông tin.
        3. Nếu câu trả lời KHÔNG CÓ trong ngữ cảnh được cung cấp, hãy trả lời CHÍNH XÁC câu sau: "Tôi không có đủ thông tin để trả lời câu hỏi này." và KHÔNG TRẢ LỜI thêm bất cứ điều gì khác.
        
        Sử dụng ngôn ngữ tự nhiên, thân thiện với người dùng.
        Trả lời bằng cùng ngôn ngữ với câu hỏi (Tiếng Việt hoặc Tiếng Anh).

        QUY TẮC TRÍCH DẪN BẮT BUỘC:
        - BẮT BUỘC phải trích dẫn nguồn cho MỖI thông tin bạn cung cấp.
        - SỬ DỤNG CHÍNH XÁC trích dẫn đã được cung cấp trong từng đoạn văn bản.
        - Mỗi đoạn văn bản trong "Ngữ cảnh" đã được đánh dấu nguồn và số đoạn (chunk) ở đầu, ví dụ: "[source=ten_file.pdf, chunk=X]". BẠN PHẢI sử dụng đúng định dạng trích dẫn này.
        - KHÔNG được tự tạo trích dẫn mới, chỉ sử dụng trích dẫn có sẵn trong ngữ cảnh.
        - Khi tham khảo thông tin từ một đoạn văn bản, LUÔN bao gồm trích dẫn của đoạn đó.
        - Nếu thông tin đến từ nhiều đoạn văn bản, liệt kê TẤT CẢ các trích dẫn liên quan.

        CÁCH TRÍCH DẪN:
        - Sau mỗi thông tin, thêm trích dẫn trong ngoặc vuông.
        - Ví dụ: "Doanh thu năm 2023 là 100 triệu đồng [source=bao_cao_tai_chinh.pdf, chunk=5]".
        - Với nhiều nguồn: "Thông tin này được xác nhận [source=file1.pdf, chunk=2] [source=file2.pdf, chunk=7]".

        Ngữ cảnh:
        {context}

        Câu hỏi: {question}

        Trả lời chi tiết (BẮT BUỘC bao gồm trích dẫn nguồn cho mọi thông tin nếu có):"""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "Câu hỏi: {question}\n\nNgữ cảnh:\n{context}\n\nTrả lời:",
            ),
        ]
    )
    context_text = "\n\n".join(
        [
            f"[source={d.metadata.get('source')}, chunk={d.metadata.get('chunk')}]\n{d.page_content}"
            for d in state.context
        ]
    )
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"question": state.question, "context": context_text})
    return RAGState(question=state.question, context=state.context, answer=answer)


def build_graph():
    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()
