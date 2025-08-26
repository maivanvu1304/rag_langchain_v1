from __future__ import annotations

from typing import Iterable, List, Dict, Optional
import uuid

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from ..core.config import get_config


def get_embeddings() -> OpenAIEmbeddings:
    cfg = get_config()
    return OpenAIEmbeddings(model=cfg.embedding_model)


def get_qdrant_client() -> QdrantClient:
    cfg = get_config()
    return QdrantClient(url=cfg.qdrant_url, api_key=cfg.qdrant_api_key)


def get_qdrant() -> Qdrant:
    cfg = get_config()
    client = get_qdrant_client()
    embeddings = get_embeddings()
    return Qdrant(
        client=client, collection_name=cfg.qdrant_collection, embeddings=embeddings
    )


def index_documents(items: List[Dict]) -> int:
    """Add new documents to vector store"""
    vs = get_qdrant()
    documents = [
        Document(page_content=it["content"], metadata=it.get("metadata", {}))
        for it in items
    ]
    vs.add_documents(documents)
    return len(documents)


def similarity_search(query: str, k: int = 5) -> List[Document]:
    vs = get_qdrant()
    return vs.similarity_search(query, k=k)


def search_by_source(source_filename: str) -> List[Document]:
    """Search documents by source filename"""
    vs = get_qdrant()
    filter_condition = Filter(
        must=[FieldCondition(key="metadata.source", match=MatchValue(value=source_filename))]
    )
    return vs.similarity_search("", k=1000, filter=filter_condition)


def delete_by_source(source_filename: str) -> int:
    """Delete all documents from a specific source file"""
    cfg = get_config()
    client = get_qdrant_client()
    
    filter_condition = Filter(
        must=[FieldCondition(key="metadata.source", match=MatchValue(value=source_filename))]
    )
    
    # Delete points matching the filter
    result = client.delete(
        collection_name=cfg.qdrant_collection,
        points_selector=filter_condition
    )
    return result.operation_id if result else 0


def update_document(document_id: str, new_content: str, new_metadata: Dict) -> bool:
    """Update a specific document by ID"""
    try:
        cfg = get_config()
        client = get_qdrant_client()
        embeddings = get_embeddings()
        
        # Create new embedding
        new_embedding = embeddings.embed_query(new_content)
        
        # Update the point
        client.upsert(
            collection_name=cfg.qdrant_collection,
            points=[{
                "id": document_id,
                "vector": new_embedding,
                "payload": {
                    "page_content": new_content,
                    "metadata": new_metadata
                }
            }]
        )
        return True
    except Exception as e:
        print(f"Error updating document {document_id}: {e}")
        return False


def get_collection_info() -> Dict:
    """Get information about the vector store collection"""
    cfg = get_config()
    client = get_qdrant_client()
    
    try:
        collection_info = client.get_collection(cfg.qdrant_collection)
        
        # Count total points
        count_result = client.count(collection_name=cfg.qdrant_collection)
        
        return {
            "collection_name": cfg.qdrant_collection,
            "total_documents": count_result.count,
            "vector_size": collection_info.config.params.vectors.size,
            "distance": collection_info.config.params.vectors.distance.name
        }
    except Exception as e:
        return {"error": str(e)}


def list_sources() -> List[str]:
    """List all unique source files in the collection"""
    cfg = get_config()
    client = get_qdrant_client()
    
    try:
        # Scroll through all points to get unique sources
        points, _ = client.scroll(
            collection_name=cfg.qdrant_collection,
            limit=1000,
            with_payload=True
        )
        
        sources = set()
        for point in points:
            if point.payload and "metadata" in point.payload:
                source = point.payload["metadata"].get("source")
                if source:
                    sources.add(source)
        
        return sorted(list(sources))
    except Exception as e:
        print(f"Error listing sources: {e}")
        return []


def clear_collection() -> bool:
    """Delete all documents from the collection"""
    cfg = get_config()
    client = get_qdrant_client()
    
    try:
        # Delete all points
        client.delete(
            collection_name=cfg.qdrant_collection,
            points_selector=Filter(must=[])  # Empty filter matches all
        )
        return True
    except Exception as e:
        print(f"Error clearing collection: {e}")
        return False
