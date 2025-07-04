from typing import Any, Dict, List, Optional

"""
Evaluation package for the RAG system.

This package provides a unified evaluation system for RAG components.
"""

# Version of the evaluation package
__version__ = "0.3.0"

# Import the main evaluator
from .evaluator import (
    RAGEvaluator,
    load_test_data,
    quick_generation_eval,
    quick_rag_eval,
    quick_retrieval_eval,
)

__all__ = [
    "RAGEvaluator",
    "load_test_data",
    "quick_rag_eval",
    "quick_retrieval_eval",
    "quick_generation_eval",
]
