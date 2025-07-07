"""
Tools package for RAG Chatbot.

This package contains simple tools that can be used with LangChain agents.
"""

from .calculator import calculate_expression, fibonacci, multiply, statistics
from .text_analyzer import analyze_text, count_words
from .tool_manager import ToolManager

__all__ = [
    # Calculator tools
    "multiply",
    "calculate_expression",
    "fibonacci",
    "statistics",
    # Text analyzer tools
    "count_words",
    "analyze_text",
    # Tool manager
    "ToolManager",
]
