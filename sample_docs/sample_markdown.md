# Advanced Document Processing Pipeline

## Overview

This pipeline provides **8-step professional document processing** for RAG systems.

## Features

### File Classification

- Multi-format support
- Confidence scoring
- Automatic detection

### Smart Processing

- Content-aware routing
- Adaptive strategies
- Quality control

## Supported Formats

| Format | Extension         | Handler      |
| ------ | ----------------- | ------------ |
| PDF    | .pdf              | PDFHandler   |
| Word   | .docx, .doc       | WordHandler  |
| Excel  | .xlsx, .xls, .csv | ExcelHandler |
| Text   | .txt, .md         | TextHandler  |

## Code Example

```python
from rag_lagchain_v1.processing import DocumentProcessingPipeline

# Initialize pipeline
pipeline = DocumentProcessingPipeline()

# Process files
results = pipeline.process_directory("/path/to/docs")

# Check results
print(f"Processed: {results.processed_files} files")
```

## Benefits

- ✅ **Scalable**: Handle 100+ files
- ✅ **Intelligent**: Adaptive processing
- ✅ **Robust**: Error handling
- ✅ **Configurable**: Extensive options

## Links

- [Documentation](https://example.com/docs)
- [GitHub](https://github.com/example/repo)
- [Demo](https://demo.example.com)
