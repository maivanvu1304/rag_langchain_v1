"""Content analyzer for detailed content type classification."""

from __future__ import annotations

import re
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass

from .file_router import ProcessingResult, FileType


class ContentType(Enum):
    """Types of content detected in documents."""
    TEXT_ONLY = "text_only"
    TEXT_TABLE = "text_table"  
    TEXT_TABLE_IMAGE = "text_table_image"
    TABLE_ONLY = "table_only"
    IMAGE_ONLY = "image_only"
    MIXED_CONTENT = "mixed_content"
    EMPTY = "empty"
    STRUCTURED_TEXT = "structured_text"  # For markdown with headers, lists, etc.


@dataclass
class ContentAnalysis:
    """Detailed analysis of document content."""
    content_type: ContentType
    confidence: float
    
    # Content flags
    has_text: bool = False
    has_tables: bool = False
    has_images: bool = False
    has_structure: bool = False
    
    # Quantitative metrics
    text_length: int = 0
    table_count: int = 0
    image_count: int = 0
    page_count: int = 0
    
    # Quality metrics
    text_quality_score: float = 0.0
    structure_score: float = 0.0
    
    # Processing recommendations
    recommended_chunk_size: int = 800
    recommended_strategy: str = "standard"
    
    # Additional metadata
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ContentAnalyzer:
    """Analyzes document content to determine detailed content types and processing strategies."""
    
    def __init__(self):
        """Initialize the content analyzer."""
        # Patterns for detecting structured content
        self.structure_patterns = {
            'headers': [
                r'^#+\s+',  # Markdown headers
                r'^[A-Z][A-Z\s]+$',  # ALL CAPS headers
                r'^\d+\.\s+[A-Z]',  # Numbered sections
                r'^(CHƯƠNG|PHẦN|MỤC|TIẾT)\s+\d+',  # Vietnamese sections
                r'^(CHAPTER|SECTION|PART)\s+\d+',  # English sections
            ],
            'lists': [
                r'^\s*[-*+]\s+',  # Bullet points
                r'^\s*\d+\.\s+',  # Numbered lists
                r'^\s*[a-z]\)\s+',  # Lettered lists
            ],
            'tables_text': [
                r'\|.*\|.*\|',  # Markdown tables
                r'\t.*\t.*\t',  # Tab-separated
                r'[:,]\s*\d+\s*[:,]',  # Numbers with separators
                r'(Bảng|Table)\s*\d+',  # Table references
            ],
            'images_text': [
                r'(Hình|Figure|Fig)\s*\d+',  # Image references
                r'\!\[.*\]\(.*\)',  # Markdown images
                r'(hình ảnh|image|ảnh)',  # Image mentions
            ],
        }
        
        # Compile patterns for efficiency
        self._compile_patterns()
    
    def analyze_content(self, processing_result: ProcessingResult) -> ContentAnalysis:
        """
        Analyze processed content to determine content type and characteristics.
        
        Args:
            processing_result: Result from file processing
            
        Returns:
            Detailed content analysis
        """
        if not processing_result.success:
            return ContentAnalysis(
                content_type=ContentType.EMPTY,
                confidence=1.0,
                metadata={'error': processing_result.error}
            )
        
        content = processing_result.content
        tables = processing_result.tables
        images = processing_result.images
        file_type = processing_result.file_type
        
        # Basic content flags
        has_text = bool(content and content.strip())
        has_tables = len(tables) > 0
        has_images = len(images) > 0
        
        # Text analysis
        text_analysis = self._analyze_text_content(content) if has_text else {}
        
        # Structure analysis
        structure_analysis = self._analyze_structure(content, file_type) if has_text else {}
        
        # Determine content type
        content_type, confidence = self._determine_content_type(
            has_text, has_tables, has_images, text_analysis, structure_analysis
        )
        
        # Calculate metrics
        text_length = len(content) if content else 0
        table_count = len(tables)
        image_count = len(images)
        page_count = processing_result.metadata.get('page_count', 1)
        
        # Quality scores
        text_quality_score = self._calculate_text_quality(content, text_analysis)
        structure_score = structure_analysis.get('structure_score', 0.0)
        
        # Processing recommendations
        chunk_size, strategy = self._recommend_processing_strategy(
            content_type, text_length, table_count, image_count, structure_score
        )
        
        return ContentAnalysis(
            content_type=content_type,
            confidence=confidence,
            has_text=has_text,
            has_tables=has_tables,
            has_images=has_images,
            has_structure=structure_score > 0.3,
            text_length=text_length,
            table_count=table_count,
            image_count=image_count,
            page_count=page_count,
            text_quality_score=text_quality_score,
            structure_score=structure_score,
            recommended_chunk_size=chunk_size,
            recommended_strategy=strategy,
            metadata={
                'file_type': file_type.value,
                'processing_method': processing_result.metadata.get('processing_method', 'unknown'),
                'text_analysis': text_analysis,
                'structure_analysis': structure_analysis,
            }
        )
    
    def analyze_multiple_files(self, processing_results: Dict[str, ProcessingResult]) -> Dict[str, ContentAnalysis]:
        """
        Analyze multiple processed files.
        
        Args:
            processing_results: Dictionary of filename -> ProcessingResult
            
        Returns:
            Dictionary of filename -> ContentAnalysis
        """
        analyses = {}
        
        for filename, result in processing_results.items():
            analyses[filename] = self.analyze_content(result)
        
        return analyses
    
    def get_content_summary(self, analyses: Dict[str, ContentAnalysis]) -> Dict[str, Any]:
        """
        Get summary statistics from multiple content analyses.
        
        Args:
            analyses: Dictionary of filename -> ContentAnalysis
            
        Returns:
            Summary statistics
        """
        if not analyses:
            return {'total_files': 0}
        
        # Count by content type
        type_counts = {}
        for content_type in ContentType:
            type_counts[content_type.value] = sum(
                1 for analysis in analyses.values() 
                if analysis.content_type == content_type
            )
        
        # Aggregate metrics
        total_text_length = sum(a.text_length for a in analyses.values())
        total_tables = sum(a.table_count for a in analyses.values())
        total_images = sum(a.image_count for a in analyses.values())
        avg_confidence = sum(a.confidence for a in analyses.values()) / len(analyses)
        avg_quality = sum(a.text_quality_score for a in analyses.values()) / len(analyses)
        
        # Processing recommendations
        strategy_counts = {}
        for analysis in analyses.values():
            strategy = analysis.recommended_strategy
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            'total_files': len(analyses),
            'content_type_distribution': type_counts,
            'aggregate_metrics': {
                'total_text_length': total_text_length,
                'total_tables': total_tables,
                'total_images': total_images,
                'average_confidence': avg_confidence,
                'average_quality_score': avg_quality,
            },
            'processing_recommendations': {
                'strategy_distribution': strategy_counts,
                'recommended_chunk_sizes': [a.recommended_chunk_size for a in analyses.values()],
            }
        }
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.compiled_patterns = {}
        for category, patterns in self.structure_patterns.items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.MULTILINE | re.IGNORECASE) 
                for pattern in patterns
            ]
    
    def _analyze_text_content(self, content: str) -> Dict[str, Any]:
        """Analyze text content for basic metrics."""
        if not content:
            return {}
        
        lines = content.split('\n')
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        # Character distribution
        alpha_chars = sum(1 for c in content if c.isalpha())
        digit_chars = sum(1 for c in content if c.isdigit())
        space_chars = sum(1 for c in content if c.isspace())
        
        return {
            'line_count': len(lines),
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'character_count': len(content),
            'alpha_ratio': alpha_chars / max(len(content), 1),
            'digit_ratio': digit_chars / max(len(content), 1),
            'space_ratio': space_chars / max(len(content), 1),
            'avg_word_length': sum(len(word) for word in words) / max(len(words), 1),
            'avg_line_length': sum(len(line) for line in lines) / max(len(lines), 1),
        }
    
    def _analyze_structure(self, content: str, file_type: FileType) -> Dict[str, Any]:
        """Analyze document structure."""
        if not content:
            return {'structure_score': 0.0}
        
        structure_counts = {}
        total_lines = len(content.split('\n'))
        
        # Count different structure types
        for category, patterns in self.compiled_patterns.items():
            count = 0
            for pattern in patterns:
                matches = pattern.findall(content)
                count += len(matches)
            structure_counts[category] = count
        
        # Calculate structure score
        structure_indicators = sum(structure_counts.values())
        structure_score = min(structure_indicators / max(total_lines, 1), 1.0)
        
        # Special handling for markdown files
        if file_type == FileType.MD:
            structure_score = min(structure_score * 1.5, 1.0)  # Boost for markdown
        
        return {
            'structure_counts': structure_counts,
            'structure_score': structure_score,
            'total_structure_indicators': structure_indicators,
        }
    
    def _determine_content_type(
        self, 
        has_text: bool, 
        has_tables: bool, 
        has_images: bool, 
        text_analysis: Dict, 
        structure_analysis: Dict
    ) -> tuple[ContentType, float]:
        """Determine content type and confidence."""
        
        # Handle empty content
        if not has_text and not has_tables and not has_images:
            return ContentType.EMPTY, 1.0
        
        # Handle single content types
        if has_text and not has_tables and not has_images:
            # Check if it's structured text
            structure_score = structure_analysis.get('structure_score', 0.0)
            if structure_score > 0.3:
                return ContentType.STRUCTURED_TEXT, 0.9
            else:
                return ContentType.TEXT_ONLY, 0.95
        
        if has_tables and not has_text and not has_images:
            return ContentType.TABLE_ONLY, 0.9
        
        if has_images and not has_text and not has_tables:
            return ContentType.IMAGE_ONLY, 0.9
        
        # Handle combinations
        if has_text and has_tables and has_images:
            return ContentType.TEXT_TABLE_IMAGE, 0.95
        
        if has_text and has_tables and not has_images:
            return ContentType.TEXT_TABLE, 0.9
        
        # Mixed content (other combinations)
        return ContentType.MIXED_CONTENT, 0.7
    
    def _calculate_text_quality(self, content: str, text_analysis: Dict) -> float:
        """Calculate text quality score."""
        if not content or not text_analysis:
            return 0.0
        
        # Quality indicators
        alpha_ratio = text_analysis.get('alpha_ratio', 0)
        avg_word_length = text_analysis.get('avg_word_length', 0)
        word_count = text_analysis.get('word_count', 0)
        
        # Base score from alphabetic content
        quality_score = alpha_ratio
        
        # Bonus for reasonable word length (3-8 characters)
        if 3 <= avg_word_length <= 8:
            quality_score += 0.2
        
        # Bonus for sufficient content
        if word_count >= 50:
            quality_score += 0.1
        
        # Penalty for very short or very long average words
        if avg_word_length < 2 or avg_word_length > 15:
            quality_score -= 0.2
        
        return max(0.0, min(1.0, quality_score))
    
    def _recommend_processing_strategy(
        self, 
        content_type: ContentType, 
        text_length: int, 
        table_count: int, 
        image_count: int, 
        structure_score: float
    ) -> tuple[int, str]:
        """Recommend chunk size and processing strategy."""
        
        # Base chunk size
        chunk_size = 800
        strategy = "standard"
        
        # Adjust based on content type
        if content_type == ContentType.TEXT_ONLY:
            chunk_size = 1000
            strategy = "text_only"
        
        elif content_type == ContentType.STRUCTURED_TEXT:
            chunk_size = 600
            strategy = "structure_aware"
        
        elif content_type == ContentType.TEXT_TABLE:
            chunk_size = 1200
            strategy = "table_aware"
        
        elif content_type == ContentType.TEXT_TABLE_IMAGE:
            chunk_size = 1500
            strategy = "multimedia_aware"
        
        elif content_type == ContentType.TABLE_ONLY:
            chunk_size = 2000
            strategy = "table_focused"
        
        # Adjust for document length
        if text_length < 2000:
            chunk_size = min(chunk_size, text_length // 2)
        elif text_length > 50000:
            chunk_size = min(chunk_size + 300, 2000)
        
        # Adjust for content density
        if table_count > 5 or image_count > 10:
            chunk_size += 200
        
        # Ensure minimum chunk size
        chunk_size = max(chunk_size, 200)
        
        return chunk_size, strategy
