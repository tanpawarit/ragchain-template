# RAG System Evaluation

## Overview

The RAG-Chain system includes a comprehensive evaluation framework with:

1. **Retriever Evaluation** - Evaluate document retrieval performance
2. **Generator Evaluation** - Evaluate answer generation quality
3. **End-to-End Evaluation** - Evaluate complete system performance

## Structure

```
evaluation/
├── retriever_evaluation.py    # Retriever evaluation
├── generator_evaluation.py    # Generator evaluation
├── e2e_evaluation.py          # End-to-end evaluation
├── metrics.py                 # Various metrics
└── test_data/                 # Test datasets
    ├── golden_dataset_v1.json
    └── golden_dataset_v2.json
```

## Usage

### 1. Retriever Evaluation

```python
from evaluation.retriever_evaluation import evaluate_retriever

results = evaluate_retriever(
    vectorstore=vectorstore,
    test_data=test_data,
    k_values=[3, 5, 10]
)
```

### 2. Generator Evaluation

```python
from evaluation.generator_evaluation import evaluate_generator

results = evaluate_generator(
    rag_system=rag_system,
    test_data=test_data,
    metrics=["relevancy", "faithfulness"]
)
```

### 3. End-to-End Evaluation

```python
from evaluation.e2e_evaluation import evaluate_e2e_system

results = evaluate_e2e_system(
    test_data=test_data,
    rag_system=rag_system,
    evaluation_model="gpt-4o"
)
```

## Key Metrics

### Retriever
- **Precision@K**: Accuracy of retrieved documents
- **Recall@K**: Coverage of relevant documents
- **MRR**: Mean Reciprocal Rank

### Generator
- **Relevancy**: Answer relevance to the question
- **Faithfulness**: Answer accuracy based on context
- **Answer Completeness**: Completeness of the response

### End-to-End
- **Overall Accuracy**: System-wide accuracy
- **Response Time**: Query response time
- **Cost per Query**: Cost per query execution

## Running Evaluations

```bash
# Evaluate retriever
python evaluation/retriever_evaluation.py

# Evaluate generator
python evaluation/generator_evaluation.py

# Run end-to-end evaluation
python evaluation/e2e_evaluation.py
```

## View Results in MLflow

```bash
# Start MLflow UI
mlflow ui --port 5000

# Access at http://localhost:5000
```

## Preparing Test Data

Create a JSON file with the following format:

```json
[
  {
    "question": "Test question",
    "expected_answer": "Expected answer",
    "context": "Relevant context"
  }
]
```

## Evaluation Best Practices

1. **Use diverse test data** - Cover various scenarios
2. **Evaluate regularly** - Track performance changes
3. **Use multiple metrics** - Don't rely on a single metric
4. **Test with real users** - Conduct user acceptance testing

## Related Documentation

- **[Quick Start](quickstart.md)** - Set up your system before evaluation
- **[Prompt Management](prompts.md)** - Optimize prompts based on evaluation results
- **[Complete Documentation](README.md)** - Return to documentation overview 