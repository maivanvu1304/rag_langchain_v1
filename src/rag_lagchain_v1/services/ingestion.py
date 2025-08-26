"""Document ingestion service for loading and splitting documents."""

from __future__ import annotations

import os
from typing import List, Dict
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..utils.file_processors import (
    read_pdf_with_images,
    read_pdf,
    read_docx,
    read_md,
    read_txt,
)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def load_and_split(
    filename: str,
    file_bytes: bytes,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> List[Dict]:
    """
    Load and split a document into chunks.
    
    Args:
        filename: Name of the file
        file_bytes: File content as bytes
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of dictionaries with content and metadata
        
    Raises:
        ValueError: If file type is not supported
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    image_paths = []
    tables_data = []
    
    # Extract text based on file type
    if ext == ".pdf":
        try:
            text, image_paths, tables_data = read_pdf_with_images(file_bytes, filename)
        except Exception:
            # Fallback to simple text extraction
            text = read_pdf(file_bytes)
    elif ext == ".docx":
        text = read_docx(file_bytes)
    elif ext == ".md":
        text = read_md(file_bytes)
    else:
        text = read_txt(file_bytes)

    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_text(text)

    # Create results with metadata
    results: List[Dict] = []
    for i, chunk in enumerate(chunks):
        metadata = {"source": filename, "chunk": i}
        
        # Add image paths to metadata if this chunk mentions images
        chunk_images = []
        for img_path in image_paths:
            img_filename = Path(img_path).name
            if img_filename in chunk:
                chunk_images.append(img_path)
        
        if chunk_images:
            metadata["images"] = chunk_images
            
        # Add table data to metadata if this chunk mentions tables
        chunk_tables = []
        for table_dict in tables_data:
            table_ref = f"{Path(filename).stem}_page{table_dict['page']}_table{table_dict['table_index'] + 1}"
            if table_ref in chunk:
                chunk_tables.append(table_dict)
        
        if chunk_tables:
            metadata["tables"] = chunk_tables
            
        results.append(
            {
                "content": chunk,
                "metadata": metadata,
            }
        )
    return results
