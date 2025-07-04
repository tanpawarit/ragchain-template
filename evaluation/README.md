# RAG Evaluation System

A unified, easy-to-use evaluation system for RAG (Retrieval-Augmented Generation) components.

## Features

- **Single File Solution**: All evaluation logic in one module
- **Minimal Dependencies**: Only requires `openai` and `numpy`
- **Easy to Use**: Clean API with sensible defaults
- **Comprehensive**: Evaluates retrieval, generation, and end-to-end RAG systems
- **Thai Language Support**: Works with Thai text and questions

## Quick Start

### 1. Install Dependencies

```bash
pip install openai numpy
```

### 2. Set OpenAI API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Basic Usage

```python
from evaluation import RAGEvaluator, load_test_data

# Initialize evaluator
evaluator = RAGEvaluator()

# Load test data
test_data = load_test_data("test_data/golden_dataset_v1.json")

# Evaluate your RAG system
results = evaluator.evaluate_rag_system(test_data, your_rag_system)

# Save results
evaluator.save_results(results, "results/evaluation.json")
```

## Evaluation Types

### 1. Retrieval Evaluation

Evaluates how well your vector store retrieves relevant documents:

```python
results = evaluator.evaluate_retrieval(
    vectorstore=your_vectorstore,
    test_data=test_data,
    k=5,  # Number of documents to retrieve
    similarity_threshold=0.7  # Relevance threshold
)
```

**Metrics:**
- Precision: Fraction of retrieved documents that are relevant
- Recall: Fraction of relevant documents that are retrieved
- F1 Score: Harmonic mean of precision and recall
- Average Relevance: Average semantic similarity score

### 2. Generation Evaluation

Evaluates the quality of generated answers:

```python
def your_generator(question: str) -> str:
    # Your generation logic here
    return generated_answer

results = evaluator.evaluate_generation(test_data, your_generator)
```

**Metrics:**
- Relevance: How well the answer addresses the question
- Coherence: How well-structured and clear the answer is
- Accuracy: How accurate the answer is compared to reference
- Overall Quality: Overall quality considering all factors

### 3. End-to-End RAG Evaluation

Evaluates your complete RAG system:

```python
class YourRAGSystem:
    def query(self, question: str) -> dict:
        return {
            "answer": "Generated answer",
            "context": "Retrieved context",
            "sources": ["source1", "source2"]
        }

results = evaluator.evaluate_rag_system(test_data, YourRAGSystem())
```

**Metrics:**
- Answer Relevance: How relevant the answer is to the question
- Context Relevance: How relevant the retrieved context is
- Accuracy: How accurate the answer is compared to reference
- Overall Quality: Overall quality of the RAG response

## Test Data Format

Your test data should be a JSON file with the following structure:

```json
[
  {
    "question": "Your question here",
    "ideal_answer": "Expected answer",
    "ideal_context": ["Expected relevant context"]
  }
]
```

## Quick Evaluation Functions

For even easier usage, use the quick evaluation functions:

```python
from evaluation import quick_rag_eval, quick_retrieval_eval, quick_generation_eval

# Quick RAG evaluation
results = quick_rag_eval(your_rag_system, "test_data/golden_dataset_v1.json")

# Quick retrieval evaluation
results = quick_retrieval_eval(your_vectorstore, "test_data/golden_dataset_v1.json")

# Quick generation evaluation
results = quick_generation_eval(your_generator, "test_data/golden_dataset_v1.json")
```

## Example Usage

See `example_usage.py` for complete working examples of all evaluation types.

## Configuration

You can customize the evaluator:

```python
evaluator = RAGEvaluator(
    openai_api_key="your-key",  # Optional if set in environment
    evaluation_model="gpt-4o-mini",  # Model for LLM-based evaluation
    embedding_model="text-embedding-3-small"  # Model for similarity calculations
)
```

## Results Structure

All evaluation methods return results in this format:

```python
{
    "results": [
        {
            "question": "Question text",
            "metric1": score1,
            "metric2": score2,
            # ... other metrics and details
        }
    ],
    "summary": {
        "avg_metric1": average_score1,
        "avg_metric2": average_score2,
        "total_queries": number_of_queries,
        # ... other summary statistics
    }
}
```

## Benefits

- **Easy to Use**: No complex configuration or setup required
- **Reliable**: Fewer dependencies means fewer potential issues
- **Fast Setup**: Get started with evaluation in minutes
- **Clear Results**: Well-structured output with detailed metrics
- **Flexible**: Works with any RAG system architecture

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**: Make sure your API key is set in environment variables or passed to the evaluator
2. **Test Data Not Found**: Ensure your test data file path is correct
3. **Model Not Available**: Check that you have access to the specified OpenAI models

### Getting Help

If you encounter issues:
1. Check the example usage in `example_usage.py`
2. Verify your test data format matches the expected structure
3. Ensure you have the required dependencies installed

## File Structure

```
evaluation/
├── __init__.py              # Package initialization
├── evaluator.py             # Main evaluation module
├── example_usage.py         # Usage examples
├── README.md               # This documentation
└── test_data/              # Test datasets
    ├── golden_dataset_v1.json
    └── golden_dataset_v2.json
```
 