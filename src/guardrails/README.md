# Guardrails System

A comprehensive guardrails system for RAG Chatbot that ensures security and quality validation of data throughout the pipeline.

## Overview

The guardrails system consists of multiple validators working together to:

- **Input Validation**: Validate user input before processing
- **Output Validation**: Validate generated responses before delivery
- **Content Safety**: Detect inappropriate or harmful content
- **PII Detection**: Identify and handle personally identifiable information

## Usage

### Basic Setup

```python
from src.guardrails import GuardrailManager

# Configure guardrails
config = {
    "enabled": True,
    "input_validation": {
        "enabled": True,
        "max_length": 1000,
        "check_prompt_injection": True,
        "check_profanity": True
    },
    "output_validation": {
        "enabled": True,
        "max_response_length": 2000,
        "check_relevance": True,
        "check_hallucination": True
    },
    "content_safety": {
        "enabled": True,
        "toxicity_threshold": 0.7,
        "hate_speech_threshold": 0.8
    },
    "pii_detection": {
        "enabled": True,
        "mask_pii": True,
        "fail_on_pii": False
    }
}

# Create guardrail manager
guardrail_manager = GuardrailManager(config)
```

### Usage in RAG Pipeline

```python
# Validate input
is_valid, input_results = guardrail_manager.validate_input(
    question="What is machine learning?",
    user_id="user123"
)

if not is_valid:
    print("Input validation failed:", input_results)
    return

# Validate retrieved context
is_valid, context_results = guardrail_manager.validate_context(retrieved_docs)

# Validate output
is_valid, output_results = guardrail_manager.validate_output(
    answer="Machine learning is...",
    question="What is machine learning?",
    context="Retrieved context..."
)

# Get validation report
report = guardrail_manager.get_validation_report(output_results)
print(f"Status: {report['status']}")
```

## Available Validators

### Input Validators
- **PromptInjectionValidator**: Detects prompt injection attempts
- **InputLengthValidator**: Validates input length constraints
- **ProfanityValidator**: Detects profane language

### Output Validators
- **OutputLengthValidator**: Validates response length
- **RelevanceValidator**: Checks answer relevance to question
- **HallucinationValidator**: Detects hallucinated information

### Content Safety
- **ToxicityValidator**: Detects toxic content
- **HateSpeechValidator**: Detects hate speech

### PII Detection
- **PIIDetector**: Identifies and handles personal information

## Creating Custom Validators

```python
from src.guardrails.base import BaseGuardrail, GuardrailResponse, GuardrailResult

class CustomValidator(BaseGuardrail):
    guardrail_name = "CustomValidator"
    
    def validate(self, input_data: str) -> GuardrailResponse:
        # Your validation logic
        if "bad_word" in input_data.lower():
            return GuardrailResponse(
                result=GuardrailResult.FAIL,
                message="Contains inappropriate content",
                confidence=0.9
            )
        
        return GuardrailResponse(
            result=GuardrailResult.PASS,
            message="Validation passed",
            confidence=1.0
        )
```

## Validation Results

GuardrailResponse has three possible states:
- **PASS**: Validation successful
- **FAIL**: Validation failed
- **WARNING**: Validation passed with warnings

## Advanced Configuration

For detailed configuration options, see `GuardrailManagerConfig` class in `manager.py`.

## Key Features

- **Modular Design**: Easy to add new validators
- **Configurable**: Flexible configuration per validator
- **Comprehensive Logging**: Detailed logging for debugging
- **Error Handling**: Graceful handling of validation errors
- **Performance Optimized**: Efficient validation pipeline 