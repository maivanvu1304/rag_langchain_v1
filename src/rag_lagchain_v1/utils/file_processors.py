"""File processing utilities for different document formats."""

from __future__ import annotations

import io
from typing import List, Dict, Tuple
from pathlib import Path

import docx2txt
from pypdf import PdfReader
from markdown import markdown
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import pandas as pd


def read_pdf_with_images(file_bytes: bytes, filename: str) -> Tuple[str, List[str], List[Dict]]:
    """Extract text, images, and tables from PDF using PyMuPDF."""
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


def read_pdf(file_bytes: bytes) -> str:
    """Fallback PDF reader using pypdf."""
    reader = PdfReader(io.BytesIO(file_bytes))
    texts = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            texts.append(f"[Trang {i}]\n{text}")
    return "\n".join(texts)


def read_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX files."""
    with io.BytesIO(file_bytes) as f:
        return docx2txt.process(f) or ""


def read_md(file_bytes: bytes) -> str:
    """Extract text from Markdown files."""
    html = markdown(file_bytes.decode("utf-8", errors="ignore"))
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text("\n")


def read_txt(file_bytes: bytes) -> str:
    """Extract text from plain text files."""
    return file_bytes.decode("utf-8", errors="ignore")
