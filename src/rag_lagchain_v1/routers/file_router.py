"""File router for directing files to appropriate handlers."""

from __future__ import annotations

import os
from typing import Dict, Any, Callable, Optional
from pathlib import Path
from enum import Enum

from ..utils.file_processors import (
    read_pdf_with_images,
    read_pdf,
    read_docx,
    read_md,
    read_txt,
)


class FileType(Enum):
    """Supported file types for routing."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    MD = "md"
    UNKNOWN = "unknown"


class ProcessingResult:
    """Result from file processing with metadata."""
    
    def __init__(
        self,
        success: bool,
        file_type: FileType,
        content: str = "",
        tables: list = None,
        images: list = None,
        metadata: dict = None,
        error: str = ""
    ):
        self.success = success
        self.file_type = file_type
        self.content = content
        self.tables = tables or []
        self.images = images or []
        self.metadata = metadata or {}
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'success': self.success,
            'file_type': self.file_type.value,
            'content': self.content,
            'tables': self.tables,
            'images': self.images,
            'metadata': self.metadata,
            'error': self.error
        }


class FileRouter:
    """Intelligent file router that directs files to appropriate handlers."""
    
    def __init__(self):
        """Initialize the file router."""
        self._handlers: Dict[FileType, Callable] = {
            FileType.PDF: self._handle_pdf,
            FileType.DOCX: self._handle_docx,
            FileType.DOC: self._handle_docx,  # Same as DOCX
            FileType.TXT: self._handle_txt,
            FileType.MD: self._handle_md,
        }
        
        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'successful_processing': 0,
            'failed_processing': 0,
            'files_by_type': {file_type.value: 0 for file_type in FileType},
        }
    
    def detect_file_type(self, filename: str) -> FileType:
        """
        Detect file type from filename extension.
        
        Args:
            filename: Name of the file
            
        Returns:
            Detected file type
        """
        ext = os.path.splitext(filename)[1].lower()
        
        type_mapping = {
            '.pdf': FileType.PDF,
            '.docx': FileType.DOCX,
            '.doc': FileType.DOC,
            '.txt': FileType.TXT,
            '.md': FileType.MD,
            '.markdown': FileType.MD,
        }
        
        return type_mapping.get(ext, FileType.UNKNOWN)
    
    def route_file(self, filename: str, file_bytes: bytes) -> ProcessingResult:
        """
        Route file to appropriate handler based on type.
        
        Args:
            filename: Name of the file
            file_bytes: File content as bytes
            
        Returns:
            ProcessingResult with extracted content and metadata
        """
        self.stats['files_processed'] += 1
        
        # Detect file type
        file_type = self.detect_file_type(filename)
        self.stats['files_by_type'][file_type.value] += 1
        
        if file_type == FileType.UNKNOWN:
            self.stats['failed_processing'] += 1
            return ProcessingResult(
                success=False,
                file_type=file_type,
                error=f"Unsupported file type: {os.path.splitext(filename)[1]}"
            )
        
        # Get appropriate handler
        handler = self._handlers.get(file_type)
        if not handler:
            self.stats['failed_processing'] += 1
            return ProcessingResult(
                success=False,
                file_type=file_type,
                error=f"No handler available for {file_type.value}"
            )
        
        try:
            # Process file with handler
            result = handler(filename, file_bytes)
            
            if result.success:
                self.stats['successful_processing'] += 1
            else:
                self.stats['failed_processing'] += 1
            
            return result
            
        except Exception as e:
            self.stats['failed_processing'] += 1
            return ProcessingResult(
                success=False,
                file_type=file_type,
                error=f"Processing error: {str(e)}"
            )
    
    def route_multiple_files(self, files: Dict[str, bytes]) -> Dict[str, ProcessingResult]:
        """
        Route multiple files to their handlers.
        
        Args:
            files: Dictionary of filename -> file_bytes
            
        Returns:
            Dictionary of filename -> ProcessingResult
        """
        results = {}
        
        for filename, file_bytes in files.items():
            results[filename] = self.route_file(filename, file_bytes)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get routing statistics."""
        stats = self.stats.copy()
        if stats['files_processed'] > 0:
            stats['success_rate'] = (stats['successful_processing'] / stats['files_processed']) * 100
        else:
            stats['success_rate'] = 0
        
        return stats
    
    def reset_statistics(self):
        """Reset routing statistics."""
        self.stats = {
            'files_processed': 0,
            'successful_processing': 0,
            'failed_processing': 0,
            'files_by_type': {file_type.value: 0 for file_type in FileType},
        }
    
    # Handler methods for different file types
    
    def _handle_pdf(self, filename: str, file_bytes: bytes) -> ProcessingResult:
        """Handle PDF files with advanced processing."""
        try:
            # Try advanced PDF processing first
            text, image_paths, tables_data = read_pdf_with_images(file_bytes, filename)
            
            return ProcessingResult(
                success=True,
                file_type=FileType.PDF,
                content=text,
                tables=tables_data,
                images=image_paths,
                metadata={
                    'processing_method': 'pymupdf_advanced',
                    'page_count': text.count('[Trang ') if '[Trang ' in text else 1,
                    'has_tables': len(tables_data) > 0,
                    'has_images': len(image_paths) > 0,
                }
            )
            
        except Exception as e:
            # Fallback to simple PDF processing
            try:
                text = read_pdf(file_bytes)
                
                return ProcessingResult(
                    success=True,
                    file_type=FileType.PDF,
                    content=text,
                    metadata={
                        'processing_method': 'pypdf_simple',
                        'page_count': text.count('[Trang ') if '[Trang ' in text else 1,
                        'fallback_reason': str(e),
                    }
                )
                
            except Exception as e2:
                return ProcessingResult(
                    success=False,
                    file_type=FileType.PDF,
                    error=f"Both PDF processing methods failed: {str(e2)}"
                )
    
    def _handle_docx(self, filename: str, file_bytes: bytes) -> ProcessingResult:
        """Handle DOCX/DOC files."""
        try:
            text = read_docx(file_bytes)
            
            if not text or not text.strip():
                return ProcessingResult(
                    success=False,
                    file_type=FileType.DOCX,
                    error="No text content extracted from DOCX file"
                )
            
            # Basic analysis for DOCX content
            word_count = len(text.split())
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
            
            return ProcessingResult(
                success=True,
                file_type=FileType.DOCX,
                content=text,
                metadata={
                    'processing_method': 'docx2txt',
                    'word_count': word_count,
                    'paragraph_count': paragraph_count,
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                file_type=FileType.DOCX,
                error=f"DOCX processing failed: {str(e)}"
            )
    
    def _handle_txt(self, filename: str, file_bytes: bytes) -> ProcessingResult:
        """Handle plain text files."""
        try:
            text = read_txt(file_bytes)
            
            if not text or not text.strip():
                return ProcessingResult(
                    success=False,
                    file_type=FileType.TXT,
                    error="Empty text file"
                )
            
            # Basic text analysis
            lines = text.split('\n')
            word_count = len(text.split())
            
            return ProcessingResult(
                success=True,
                file_type=FileType.TXT,
                content=text,
                metadata={
                    'processing_method': 'plain_text',
                    'line_count': len(lines),
                    'word_count': word_count,
                    'character_count': len(text),
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                file_type=FileType.TXT,
                error=f"Text processing failed: {str(e)}"
            )
    
    def _handle_md(self, filename: str, file_bytes: bytes) -> ProcessingResult:
        """Handle Markdown files."""
        try:
            text = read_md(file_bytes)
            
            if not text or not text.strip():
                return ProcessingResult(
                    success=False,
                    file_type=FileType.MD,
                    error="Empty markdown file"
                )
            
            # Basic markdown analysis
            original_text = file_bytes.decode('utf-8', errors='ignore')
            header_count = original_text.count('#')
            link_count = original_text.count('[')
            code_block_count = original_text.count('```')
            
            return ProcessingResult(
                success=True,
                file_type=FileType.MD,
                content=text,
                metadata={
                    'processing_method': 'markdown_parser',
                    'header_count': header_count,
                    'link_count': link_count,
                    'code_block_count': code_block_count // 2,  # Pairs of ```
                    'word_count': len(text.split()),
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                file_type=FileType.MD,
                error=f"Markdown processing failed: {str(e)}"
            )
