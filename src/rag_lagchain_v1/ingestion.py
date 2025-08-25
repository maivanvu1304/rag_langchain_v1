from __future__ import annotations

import io
import os
from typing import Iterable, List, Dict
from pathlib import Path

import docx2txt
from pypdf import PdfReader
from markdown import markdown
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
from PIL import Image
import pandas as pd

from langchain_text_splitters import RecursiveCharacterTextSplitter


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def _read_pdf_with_images(file_bytes: bytes, filename: str) -> tuple[str, List[str], List[Dict]]:
    """Extract text, images, and tables from PDF"""
    # Create images directory
    images_dir = Path("extracted_images")
    images_dir.mkdir(exist_ok=True)
    
    # Extract text, images, and tables using PyMuPDF
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    texts = []
    image_paths = []
    tables_data = []
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # Extract tables first
        tables = page.find_tables()
        page_tables = []
        
        for table_index, table in enumerate(tables):
            try:
                # Extract table data
                table_data = table.extract()
                if table_data and len(table_data) > 1:  # At least header + 1 row
                    # Create DataFrame
                    df = pd.DataFrame(table_data[1:], columns=table_data[0])
                    # Clean empty columns and rows
                    df = df.dropna(how='all').dropna(axis=1, how='all')
                    
                    if not df.empty:
                        table_dict = {
                            'page': page_num + 1,
                            'table_index': table_index,
                            'data': df,
                            'bbox': table.bbox  # Table position
                        }
                        tables_data.append(table_dict)
                        page_tables.append(table_dict)
                        
                        # Add table reference to text
                        texts.append(f"[Trang {page_num + 1}] Bảng {table_index + 1}: {filename}_page{page_num + 1}_table{table_index + 1}")
            except Exception as e:
                print(f"Error extracting table {table_index} from page {page_num + 1}: {e}")
        
        # Extract text (excluding table areas)
        text = page.get_text()
        if text.strip():
            # Remove table areas from text if tables found
            if page_tables:
                # This is a simple approach - in practice you might want more sophisticated text cleaning
                texts.append(f"[Trang {page_num + 1}]\n{text}")
            else:
                texts.append(f"[Trang {page_num + 1}]\n{text}")
        
        # Extract images
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            # Get image data
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            
            if pix.n - pix.alpha < 4:  # GRAY or RGB
                # Save image
                img_filename = f"{Path(filename).stem}_page{page_num + 1}_img{img_index + 1}.png"
                img_path = images_dir / img_filename
                pix.save(str(img_path))
                image_paths.append(str(img_path))
                
                # Add image reference to text
                texts.append(f"[Trang {page_num + 1}] Hình ảnh: {img_filename}")
            
            pix = None  # Free memory
    
    doc.close()
    return "\n\n".join(texts), image_paths, tables_data


def _read_pdf(file_bytes: bytes) -> str:
    """Fallback PDF reader using pypdf"""
    reader = PdfReader(io.BytesIO(file_bytes))
    texts = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            texts.append(f"[Trang {i}]\n{text}")
    return "\n".join(texts)


def _read_docx(file_bytes: bytes) -> str:
    with io.BytesIO(file_bytes) as f:
        return docx2txt.process(f) or ""


def _read_md(file_bytes: bytes) -> str:
    html = markdown(file_bytes.decode("utf-8", errors="ignore"))
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text("\n")


def _read_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore")


def load_and_split(
    filename: str,
    file_bytes: bytes,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> List[Dict]:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    image_paths = []
    tables_data = []
    
    if ext == ".pdf":
        try:
            text, image_paths, tables_data = _read_pdf_with_images(file_bytes, filename)
        except Exception:
            # Fallback to simple text extraction
            text = _read_pdf(file_bytes)
    elif ext == ".docx":
        text = _read_docx(file_bytes)
    elif ext == ".md":
        text = _read_md(file_bytes)
    else:
        text = _read_txt(file_bytes)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_text(text)

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
