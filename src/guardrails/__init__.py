"""
Guardrails package for RAG system security and validation.

This package provides comprehensive input/output validation, content safety,
and security measures for the RAG chatbot system.
"""

# Version of the guardrails package
__version__ = "0.1.0"

# Import main components
from .base import BaseGuardrail, GuardrailResponse, GuardrailResult
from .guardrails_manager import GuardrailManager

# Import NLP utilities
from .nlp_utils import (
    NLPProcessor,
    calculate_similarity,
    detect_language,
    get_keywords,
    get_nlp_processor,
    tokenize,
)

__all__ = [
    "GuardrailManager",
    "BaseGuardrail",
    "GuardrailResult",
    "GuardrailResponse",
    # NLP utilities
    "NLPProcessor",
    "get_nlp_processor",
    "detect_language",
    "tokenize",
    "get_keywords",
    "calculate_similarity",
]
