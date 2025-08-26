"""RAG LangChain application with modular structure."""

from .core.config import get_config, AppConfig
from .services import (
    index_documents,
    similarity_search,
    build_graph,
    RAGState,
    load_and_split,
)
from .ui import app, admin_page

__version__ = "1.0.0"

__all__ = [
    "get_config",
    "AppConfig", 
    "index_documents",
    "similarity_search",
    "build_graph",
    "RAGState",
    "load_and_split",
    "app",
    "admin_page",
]
