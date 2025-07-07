"""Tests for tool configuration and management."""

import pytest

from src.tools.tool_manager import ToolManager


class TestToolManager:
    """Test cases for ToolManager."""

    def test_tools_disabled(self):
        """Test that no tools are loaded when disabled."""
        config = {"enabled": False}
        manager = ToolManager(config)

        assert not manager.is_tools_enabled()
        assert len(manager.get_enabled_tools()) == 0

    def test_all_tools_enabled(self):
        """Test that all tools are loaded when enabled."""
        config = {
            "enabled": True,
            "calculator": {
                "enabled": True,
                "tools": [
                    "multiply",
                    "calculate_expression",
                    "fibonacci",
                    "statistics",
                ],
            },
            "text_analyzer": {
                "enabled": True,
                "tools": ["count_words", "analyze_text"],
            },
        }
        manager = ToolManager(config)

        assert manager.is_tools_enabled()
        assert len(manager.get_enabled_tools()) == 6

    def test_partial_tools_enabled(self):
        """Test that only specified tools are loaded."""
        config = {
            "enabled": True,
            "calculator": {"enabled": True, "tools": ["multiply", "fibonacci"]},
            "text_analyzer": {"enabled": False},
        }
        manager = ToolManager(config)

        assert manager.is_tools_enabled()
        assert len(manager.get_enabled_tools()) == 2

        # Check that the right tools are loaded
        tool_names = [tool.name for tool in manager.get_enabled_tools()]
        assert "multiply" in tool_names
        assert "fibonacci" in tool_names
        assert "count_words" not in tool_names

    def test_category_disabled(self):
        """Test that tools from disabled categories are not loaded."""
        config = {
            "enabled": True,
            "calculator": {"enabled": False, "tools": ["multiply"]},
            "text_analyzer": {"enabled": True, "tools": ["count_words"]},
        }
        manager = ToolManager(config)

        assert manager.is_tools_enabled()
        assert len(manager.get_enabled_tools()) == 1

        tool_names = [tool.name for tool in manager.get_enabled_tools()]
        assert "count_words" in tool_names
        assert "multiply" not in tool_names

    def test_unknown_tool_category(self):
        """Test handling of unknown tool categories."""
        config = {
            "enabled": True,
            "unknown_category": {"enabled": True, "tools": ["unknown_tool"]},
        }
        manager = ToolManager(config)

        # Should not crash, but no tools should be loaded
        assert not manager.is_tools_enabled()
        assert len(manager.get_enabled_tools()) == 0

    def test_unknown_tool_name(self):
        """Test handling of unknown tool names."""
        config = {
            "enabled": True,
            "calculator": {"enabled": True, "tools": ["multiply", "unknown_tool"]},
        }
        manager = ToolManager(config)

        # Should load known tools and skip unknown ones
        assert manager.is_tools_enabled()
        assert len(manager.get_enabled_tools()) == 1

        tool_names = [tool.name for tool in manager.get_enabled_tools()]
        assert "multiply" in tool_names

    def test_get_tool_info(self):
        """Test tool information retrieval."""
        config = {
            "enabled": True,
            "calculator": {"enabled": True, "tools": ["multiply"]},
        }
        manager = ToolManager(config)

        tool_info = manager.get_tool_info()

        assert tool_info["enabled"] is True
        assert tool_info["total_tools"] == 1
        assert len(tool_info["tools"]) == 1
        assert tool_info["tools"][0]["name"] == "multiply"
        assert "description" in tool_info["tools"][0]

    def test_empty_config(self):
        """Test handling of empty configuration."""
        config = {}
        manager = ToolManager(config)

        assert not manager.is_tools_enabled()
        assert len(manager.get_enabled_tools()) == 0


if __name__ == "__main__":
    pytest.main([__file__])
