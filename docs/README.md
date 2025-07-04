# RAG-Chain Chatbot Documentation

Welcome to the complete documentation for RAG-Chain Chatbot - a simple and production-ready Retrieval-Augmented Generation system with MLflow integration and evaluation capabilities.

## 📚 Documentation Overview

This documentation is organized into focused guides for different aspects of the system:

### 🚀 Getting Started
- **[Quick Start Guide](quickstart.md)** - Get up and running in 5 minutes
  - Installation and setup
  - Index building and chatbot testing

### 🏗️ System Components

#### **[Prompt Management](prompts.md)**
- YAML-based prompt templates with version control
- Template creation and versioning best practices
- Integration with configuration system

#### **[System Evaluation](evaluation.md)**
- Multi-modal evaluation framework (Retriever, Generator, End-to-End)
- DeepEval integration and metrics
- MLflow tracking for evaluation results

#### **[NLP Setup](nlp_setup.md)**
- Multilingual support with pythainlp and spacy
- Language detection and semantic similarity
- Guardrails for relevance and hallucination detection


## 🏗️ System Architecture

```
RAG-Chain System Flow
├── Data Ingestion → Index Building
├── Prompt Management → Template Versioning
├── Query Processing → NLP Guardrails
├── RAG Pipeline → Retrieval + Generation
└── Evaluation → Metrics + MLflow Tracking
```

### NLP Guardrails Integration

The system incorporates NLP-based guardrails at multiple points:

1. **Query Processing**: Language detection and preprocessing
2. **Response Validation**: 
   - Relevance checking (comparing query to response)
   - Hallucination detection (comparing response to context)
   - Content safety filtering

These guardrails use pythainlp for Thai language and spacy for English language processing, providing multilingual safety mechanisms.

## 🛠️ Quick Reference

### Essential Commands
```bash
# Setup and run
uv sync
python scripts/build_faiss_index.py --use-semantic-chunking
python -m src.components.ragchain

# NLP features setup
uv add pythainlp spacy
python -m spacy download en_core_web_md

# Evaluation
python evaluation/e2e_evaluation.py
mlflow ui --port 5000
```

### Configuration Files
- **`configs/model_config.yaml`** - Main system configuration
- **`src/prompts/templates/`** - Prompt templates
- **`evaluation/test_data/`** - Evaluation datasets

## 📖 Detailed Guides

### For Developers
1. **[Quick Start](quickstart.md)** - Basic setup and first run
2. **[Prompt Management](prompts.md)** - Customizing AI responses
3. **[System Evaluation](evaluation.md)** - Testing and monitoring
4. **[NLP Setup](nlp_setup.md)** - Multilingual text processing

### For Production Teams
1. **[System Evaluation](evaluation.md)** - Performance monitoring
2. **[Quick Start](quickstart.md)** - Deployment procedures

## 🔗 External Resources

- **[Main Repository](../README.md)** - Project overview and features
- **[Examples](../examples/)** - Code examples and use cases
- **[Source Code](../src/)** - Core implementation

## 💡 Common Workflows

### New Project Setup
1. Follow [Quick Start Guide](quickstart.md)
2. Configure prompts using [Prompt Management](prompts.md)
3. Set up evaluation with [System Evaluation](evaluation.md)
4. Configure NLP features with [NLP Setup](nlp_setup.md)

### Production Deployment
1. Configure monitoring and evaluation
2. Deploy using production configurations

### System Optimization
1. Run [evaluation framework](evaluation.md)
2. Analyze results in MLflow
3. Iterate on prompts and configuration

---

**Need Help?** Check the specific guide for your use case, or create an issue in the repository for additional support. 