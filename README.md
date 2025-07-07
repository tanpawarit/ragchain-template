# RAG-Chain Template

![FAISS](https://img.shields.io/badge/FAISS-blue?style=flat-square)
![Langchain](https://img.shields.io/badge/Framework-Langchain-green?style=flat-square&logo=langchain)
![MLflow](https://img.shields.io/badge/MLOps-MLflow-orange?style=flat-square&logo=mlflow)
![DeepEval](https://img.shields.io/badge/Evaluation-DeepEval-purple?style=flat-square)

A production-ready RAG template for building specialized chatbots with advanced retrieval techniques. This template provides a solid foundation for domain-specific use cases, from customer support to technical documentation systems.

## Core Capabilities

### Multilingual NLP in Guardrails
- **Thai & English Support**: Using pythainlp and spacy with word vectors
- **Smart Text Processing**: Language detection and semantic similarity
- **Enhanced Guardrails**: Relevance checking and hallucination detection for safer responses

### RAG Pipeline
- **Document Processing**: Semantic and character-based chunking
- **Vector Storage**: FAISS with OpenAI embeddings
- **Prompt Management**: YAML-based templates with version control
- **Evaluation**: Comprehensive metrics for retrieval and generation

### Configurable Tools System
- **Mathematical Operations**: Calculator tools with caching and rate limiting
- **Text Analysis**: Word counting, language detection, and readability scoring
- **Agent Mode**: Dynamic tool selection based on user queries
- **Performance Optimized**: Built-in caching and rate limiting for production use

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Document       │     │  Vector Store    │     │  User Query       │
│  Processing     │────▶│  (FAISS)         │     │                   │
└─────────────────┘     └──────────────────┘     └─────────┬─────────┘
                                │                          │
                                │                          ▼
                                │                ┌───────────────────┐
                                │                │  Query Processing │
                                │                └─────────┬─────────┘
                                │                          │
                                ▼                          ▼
                        ┌──────────────────┐     ┌───────────────────┐
                        │  Retrieved       │     │  NLP Guardrails   │
                        │  Context         │     │  ・Relevance      │
                        └─────────┬────────┘     │  ・Hallucination  │
                                  │              └─────────┬─────────┘
                                  │                        │
                                  ▼                        ▼
                        ┌────────────────────────────────────────────┐
                        │  LLM Generation                            │
                        │  (with Prompt Templates)                   │
                        └─────────────────────┬────────────────────┘
                                              │
                                              ▼
                                    ┌───────────────────┐
                                    │  Response         │
                                    └───────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Tools System (Agent Mode)                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │  Calculator     │  │  Text Analyzer  │  │  Custom Tools       │  │
│  │  • Math ops     │  │  • Text proc    │  │  • rate limiting    │  │
│  │  • Statistics   │  │  • Language     │  │  • caching          │  │
│  │  • Functions    │  │  • Analysis     │  │  • security         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

The system integrates NLP capabilities throughout the pipeline, with special emphasis on the guardrails component that ensures response quality and safety using pythainlp (Thai) and spacy (English). When tools are enabled, the system switches to agent mode, allowing dynamic tool selection for calculations, text analysis, and other operations.

## Getting Started

```bash
# 1. Install dependencies
uv sync

# 2. Configure API key in configs/model_config.yaml
# 3. Add your documents to data/raw/
# 4. Build index
python scripts/build_faiss_index.py --use-semantic-chunking

# 5. Run the chatbot
python -m src.components.ragchain
```

### NLP Setup

```bash
# Setup NLP capabilities
uv add pythainlp spacy
python -m spacy download en_core_web_md
```

For more details, check out our [Quick Start Guide](docs/quickstart.md).

## Documentation

- [Quick Start Guide](docs/quickstart.md) - Get running in 5 minutes
- [System Evaluation](docs/evaluation.md) - Evaluation framework
- [Prompt Management](docs/prompts.md) - Domain-specific prompt engineering
- [NLP Setup](docs/nlp_setup.md) - Multilingual NLP features
- [Tools Configuration](docs/tools_configuration.md) - Configurable tools system

## Use Cases

This template works well for:

- **Customer Support**: FAQ automation with escalation logic and calculations
- **Sales Enablement**: Product knowledge, objection handling, and pricing calculations
- **Technical Documentation**: API docs, troubleshooting, and code analysis
- **Research Assistant**: Paper summarization, citation tracking, and data analysis
- **Data Analysis**: Statistical calculations and text processing with built-in tools

## Tech Stack

- **Language**: Python 3.12+
- **LLM and Embedding**: OpenAI GPT models
- **Vector Store**: FAISS
- **Package Manager**: uv
- **Frameworks**: Langchain, DeepEval, MLflow
- **NLP Libraries**: pythainlp, spacy

## About

Built with care by Pawarison Tanyu to accelerate RAG development from prototype to production. Every component has been crafted with extensibility and best practices in mind.

For architecture details and extension points, see [Complete Documentation](docs/README.md).
 