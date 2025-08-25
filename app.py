#!/usr/bin/env python3
"""Entry point for the RAG application."""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import and run the app
from rag_lagchain_v1.ui import app

if __name__ == "__main__":
    app()
