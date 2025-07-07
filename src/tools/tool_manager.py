"""Tool manager for handling tool configuration and selection.

This module provides a centralized way to manage which tools are available
based on configuration settings.
"""

from typing import Any, Dict, List

from langchain_core.tools import BaseTool

from src.tools.calculator import calculate_expression, fibonacci, multiply, statistics
from src.tools.text_analyzer import analyze_text, count_words
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ToolManager:
    """Manages tool availability based on configuration."""

    # Registry of all available tools
    AVAILABLE_TOOLS: Dict[str, Dict[str, BaseTool]] = {
        "calculator": {
            "multiply": multiply,
            "calculate_expression": calculate_expression,
            "fibonacci": fibonacci,
            "statistics": statistics,
        },
        "text_analyzer": {
            "count_words": count_words,
            "analyze_text": analyze_text,
        },
    }

    def __init__(self, tools_config: Dict[str, Any]) -> None:
        """Initialize tool manager with configuration.

        Args:
            tools_config: Tools configuration from model config
        """
        self.tools_config = tools_config
        self.enabled_tools: List[BaseTool] = []
        self._load_enabled_tools()

    def _load_enabled_tools(self) -> None:
        """Load enabled tools based on configuration."""
        if not self.tools_config.get("enabled", False):
            logger.info("Tools are disabled in configuration")
            return

        enabled_tools = []

        for tool_category, category_config in self.tools_config.items():
            if tool_category == "enabled":
                continue

            if not isinstance(category_config, dict):
                continue

            if not category_config.get("enabled", False):
                logger.info(f"Tool category '{tool_category}' is disabled")
                continue

            if tool_category not in self.AVAILABLE_TOOLS:
                logger.warning(f"Unknown tool category: {tool_category}")
                continue

            # Get tools for this category
            category_tools = self.AVAILABLE_TOOLS[tool_category]
            configured_tools = category_config.get("tools", [])

            for tool_name in configured_tools:
                if tool_name in category_tools:
                    enabled_tools.append(category_tools[tool_name])
                    logger.info(f"Enabled tool: {tool_category}.{tool_name}")
                else:
                    logger.warning(f"Unknown tool: {tool_category}.{tool_name}")

        self.enabled_tools = enabled_tools
        logger.info(f"Total enabled tools: {len(self.enabled_tools)}")

    def get_enabled_tools(self) -> List[BaseTool]:
        """Get list of enabled tools.

        Returns:
            List of enabled BaseTool instances
        """
        return self.enabled_tools

    def is_tools_enabled(self) -> bool:
        """Check if tools are enabled.

        Returns:
            True if tools are enabled, False otherwise
        """
        return bool(self.enabled_tools)

    def get_tool_info(self) -> Dict[str, Any]:
        """Get information about enabled tools.

        Returns:
            Dictionary with tool information
        """
        tool_info = {
            "enabled": self.is_tools_enabled(),
            "total_tools": len(self.enabled_tools),
            "tools": [],
        }

        for tool in self.enabled_tools:
            tool_info["tools"].append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "args": tool.args if hasattr(tool, "args") else {},
                }
            )

        return tool_info
