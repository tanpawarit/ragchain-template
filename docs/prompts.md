# Prompt Versioning System

This directory contains the prompt versioning system for the Typhoon project. It allows you to manage different versions of prompts and easily switch between them.

## Directory Structure

```
src/prompts/
├── __init__.py           # Package exports
├── prompt_manager.py     # Core prompt management functionality
└── templates/            # Directory containing prompt template files
    └── sales_support_v1.yaml  # Example prompt template
```

## How It Works

1. Prompt templates are stored as YAML files in the `templates/` directory
2. Templates are versioned with a naming convention: `{template_name}_v{version}.yaml`
3. The `PromptManager` class handles loading and versioning of prompts
4. Configuration in `model_config.yaml` references which template to use

## Usage

### Configuration

In `configs/model_config.yaml`, specify the prompt template to use:

```yaml
prompt_config:
  template_name: "sales_support"  # Base name of the template
  version: "v1"                   # Version to use (optional)
```

### Loading Prompts

```python
from src.prompts import PromptManager

# Initialize the prompt manager
prompt_manager = PromptManager()

# Get a specific template version
template = prompt_manager.get_template("sales_support", "v1")

# Get the latest version of a template
template = prompt_manager.get_template("sales_support")

# Format a template with variables
formatted = prompt_manager.format_template("sales_support", "v1", 
                                          context="Some context", 
                                          question="User question")
```

### Creating New Template Versions

1. Create a new YAML file in the `templates/` directory
2. Name it according to the convention: `{template_name}_v{version}.yaml`
3. Update `model_config.yaml` to reference the new version

Example template file structure:

```yaml
template: |
  ### ROLE ###
  Your role description here
  
  ### INSTRUCTIONS ###
  Your instructions here
  
  ### CONTEXT ###
  {context}
  
  ### QUESTION ###
  {question}
```

## Best Practices

1. **Version Control** - Always create a new version when making significant changes
2. **Documentation** - Document changes between versions
3. **Semantic Versioning** - Use clear version naming (v1, v2, etc.)
4. **Testing** - Test new prompt versions before deploying to production
5. **Evaluation** - Use the evaluation framework to measure prompt performance

## Related Documentation

- **[Quick Start](quickstart.md)** - Basic setup and configuration
- **[System Evaluation](evaluation.md)** - Test your prompt changes  
- **[GCS Setup](gcs_setup.md)** - Production prompt management
- **[Complete Documentation](README.md)** - Return to documentation overview
