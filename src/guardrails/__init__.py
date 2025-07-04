"""
Guardrails package for RAG system security and validation.

This package provides comprehensive input/output validation, content safety,
and security measures for the RAG chatbot system.
"""

# Version of the guardrails package
__version__ = "0.1.0"

# Import main components
from .base import BaseGuardrail, GuardrailResponse, GuardrailResult
from .manager import GuardrailManager

__all__ = [
    "GuardrailManager",
    "BaseGuardrail",
    "GuardrailResult",
    "GuardrailResponse",
]
