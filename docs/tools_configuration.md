# Tools Configuration Guide

This guide explains how to configure and use tools in the RAG Chatbot system.

## Overview

The RAG Chatbot supports configurable tools that can be enabled/disabled through the model configuration. When tools are enabled, the chatbot uses an agent-based approach that can:

1. Search the knowledge base for relevant information
2. Use available tools to perform calculations, text analysis, etc.
3. Combine information from both sources to provide comprehensive answers

## Configuration

### Model Configuration (`configs/model_config.yaml`)

Add a `tools` section to your model configuration:

```yaml
# Tools configuration
tools:
  enabled: true  # Master switch for all tools
  
  # Calculator tools
  calculator:
    enabled: true
    tools: [multiply, calculate_expression, fibonacci, statistics]
  
  # Text analyzer tools
  text_analyzer:
    enabled: true
    tools: [count_words, analyze_text]
```

### Configuration Options

- **`tools.enabled`**: Master switch to enable/disable all tools
- **`tools.<category>.enabled`**: Enable/disable specific tool categories
- **`tools.<category>.tools`**: List of specific tools to enable within a category

## Available Tools

### Calculator Tools

- **`multiply`**: Multiply two numbers
- **`calculate_expression`**: Safely evaluate mathematical expressions
- **`fibonacci`**: Calculate Fibonacci numbers
- **`statistics`**: Calculate comprehensive statistics for number lists

### Text Analyzer Tools

- **`count_words`**: Count words and characters in text
- **`analyze_text`**: Comprehensive text analysis with language detection

## Usage Examples

### Basic Usage

```python
from src.components.ragchain_runner import RAGChainRunner
from src.utils.config.app_config import AppConfig
from src.utils.pipeline.vectorstore_manager import load_vectorstore

# Load configuration
cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")
vectorstore = load_vectorstore(cfg)

# Create RAG runner
rag = RAGChainRunner(cfg, vectorstore=vectorstore)

# Ask questions that use tools
answer = rag.answer("What is 15 multiplied by 23?")
print(answer)
```

### Interactive Usage

Run the example script:

```bash
python examples/tools_usage_example.py
```

## Configuration Scenarios

### Enable All Tools
```yaml
tools:
  enabled: true
  calculator:
    enabled: true
    tools: [multiply, calculate_expression, fibonacci, statistics]
  text_analyzer:
    enabled: true
    tools: [count_words, analyze_text]
```

### Only Calculator Tools
```yaml
tools:
  enabled: true
  calculator:
    enabled: true
    tools: [multiply, calculate_expression]
  text_analyzer:
    enabled: false
```

### Disable All Tools
```yaml
tools:
  enabled: false
```

## Architecture

### Without Tools (Chain Mode)
```
User Question → Retriever → Context → Prompt → LLM → Answer
```

### With Tools (Agent Mode)
```
User Question → Agent → {
  - Retriever (for context)
  - Tools (for calculations/analysis)
  - LLM (for reasoning)
} → Answer
```

## Troubleshooting

### Common Issues

1. **Tools Not Working**: Check `tools.enabled: true` in model config
2. **Unknown Tool**: Verify tool names match exactly
3. **Performance**: Agent mode is slower than chain mode

### Best Practices

1. Start with a few tools and gradually add more
2. Monitor performance with MLflow tracking
3. Test tool combinations before production

## Extending Tools

To add new tools:

1. Create tool function with `@tool` decorator
2. Add to appropriate category in `ToolManager.AVAILABLE_TOOLS`
3. Update configuration documentation

Example:
```python
@tool
def new_tool(input_param: str) -> str:
    """Description of new tool."""
    return f"Processed: {input_param}"
``` 