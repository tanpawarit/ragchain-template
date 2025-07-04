# RAG-Chain Template

![FAISS](https://img.shields.io/badge/FAISS-blue?style=flat-square)
![Prompt Versioning](https://img.shields.io/badge/Prompts-Versioning-informational?style=flat-square)
![MLflow](https://img.shields.io/badge/MLOps-MLflow-orange?style=flat-square&logo=mlflow)
![DeepEval](https://img.shields.io/badge/Evaluation-DeepEval-purple?style=flat-square)
![Langchain](https://img.shields.io/badge/Framework-Langchain-green?style=flat-square&logo=langchain)  

A **production-ready RAG template** for building specialized chatbots and implementing advanced RAG techniques. This template provides a solid foundation that can be extended for domain-specific use cases, from customer support to technical documentation systems.

## 🎯 Template Philosophy

This is not just another RAG implementation—it's a **comprehensive template** designed for:

- **🏗️ Rapid Prototyping**: Get a working RAG system in minutes, then customize for your specific domain
- **🔧 Advanced RAG Techniques**: Extensible architecture supporting Pre-Retrieval, Core Retrieval, and Post-Retrieval enhancements
- **🎨 Domain Specialization**: Easy customization for specific industries (sales, support, legal, medical, etc.)
- **📈 Production Scaling**: Built-in MLflow tracking and evaluation framework for production deployment

## ✨ Key Features

- **🤖 Complete RAG Pipeline**: End-to-end ingestion, chunking, embedding, and retrieval system
- **📝 Prompt Management**: YAML-based prompt templates with version control for easy customization
- **📈 MLflow Integration**: Experiment tracking and model versioning for production workflows
- **🧪 Comprehensive Evaluation**: DeepEval integration for retriever, generator, and end-to-end evaluation
- **⚡ Quick Setup**: Simplified configuration and deployment for rapid iteration
- **🔄 Extensible Architecture**: Modular design supporting advanced RAG techniques

## 🚀 Current Features & Extension Capabilities

This template provides a solid foundation with **core RAG functionality** and an **extensible architecture** for implementing advanced techniques as needed:

### ✅ **Current Implementation**
- **Document Processing**: Semantic and character-based chunking strategies
- **Vector Storage**: FAISS-based similarity search with OpenAI embeddings
- **Prompt Management**: YAML-based template system with versioning
- **Evaluation Framework**: Comprehensive metrics for retrieval, generation, and end-to-end performance
- **MLflow Integration**: Experiment tracking and model versioning
- **Production Ready**: Logging, configuration management, and error handling

### 🔧 **Extensible for Advanced RAG Techniques**

*The following advanced techniques can be implemented as extensions to address specific use cases:*

#### 🔍 Pre-Retrieval Enhancements
- **Query Enhancement**: Add query rewriting, expansion, and decomposition for complex queries
- **Metadata Enrichment**: Implement document tagging and classification for better filtering
- **Multi-Modal Support**: Extend for text, image, and structured data integration

#### ⚙️ Core Retrieval Techniques
- **Metadata Filtering**: Add document metadata-based filtering for targeted retrieval
- **Hybrid Search**: Combine semantic and keyword-based retrieval for improved accuracy
- **Re-ranking**: Implement cross-encoder re-ranking for precision optimization
- **Multi-Vector Retrieval**: Support multiple embedding models for diverse content types
- **Adaptive Retrieval**: Add dynamic retrieval strategies based on query characteristics

#### 🎯 Post-Retrieval Optimization
- **Context Compression**: Implement intelligent context pruning and summarization
- **Answer Synthesis**: Add multi-document reasoning and synthesis capabilities
- **Confidence Scoring**: Build uncertainty estimation for answer reliability
- **Response Validation**: Add automated fact-checking and hallucination detection

## 🛠️ Tech Stack

- **Language**: Python 3.12+
- **LLM and Embedding**: OpenAI GPT models (easily extensible to other providers)
- **Vector Store**: FAISS (with support for other vector databases)
- **Package Manager**: uv
- **Frameworks**: Langchain, DeepEval, MLflow
- **Evaluation**: Multi-modal evaluation with comprehensive metrics

## 🏗️ Architecture

```
ragchain-chatbot/
├── src/                                    # Core application code
│   ├── components/                         # RAG pipeline components
│   │   ├── ingestion.py                   # Document loading and chunking pipeline
│   │   ├── ragchain.py                    # Main RAG chain orchestration
│   │   └── ragchain_runner.py             # Interactive chatbot runner
│   ├── prompts/                           # Prompt management system
│   │   ├── prompt_manager.py              # Prompt template loading and versioning
│   │   └── templates/                     # YAML prompt templates
│   │       └── sales_support_v1.yaml      # Sales support prompt template
│   └── utils/                             # Utilities and configuration
│       ├── logger.py                      # Application logging configuration
│       ├── config/                        # Configuration management
│       │   ├── app_config.py              # Application configuration loader
│       │   └── manager.py                 # Configuration manager utilities
│       └── pipeline/                      # Data pipeline utilities
│           ├── mlflow_tracker.py          # MLflow experiment tracking
│           └── vectorstore_manager.py     # Vector store operations and management
├── evaluation/                            # Evaluation framework
├── scripts/                              # Utility scripts
├── configs/                              # Configuration files
├── data/                                 # Data storage
│   └── raw/                             # Raw text documents
└── artifacts/                           # Generated FAISS indexes
```

### 🔄 Current Data Flow & Extension Points

```
📝 Raw Documents (txt files)
    ⬇️
🔨 Document Processing Pipeline [✅ Implemented]
    ⬇️ (semantic/character chunking, metadata)
📄 Document Chunks
    ⬇️
🤖 OpenAI Embeddings [✅ Implemented]
    ⬇️ (text-embedding-3-small)
🗂️ FAISS Vector Store [✅ Implemented]
    ⬇️ (similarity search)
💾 Persistent Storage [✅ Implemented]
    ⬇️
🔍 Basic Retrieval [✅ Implemented]
    ⬇️ [🔧 Extension Point: hybrid search, re-ranking]
🎯 Direct Context Passing [✅ Implemented]
    ⬇️ [🔧 Extension Point: compression, synthesis]
🤖 LLM Generation [✅ Implemented]
    ⬇️ [🔧 Extension Point: confidence scoring]
💬 Chatbot Response [✅ Implemented]
```

## 🎨 Use Case Examples

This template can be quickly adapted for various domains:

### 🏢 Enterprise Applications
- **Customer Support**: FAQ automation with escalation logic
- **Sales Enablement**: Product knowledge and objection handling
- **HR Assistant**: Policy queries and onboarding support
- **Legal Research**: Document analysis and case law retrieval

### 🔬 Technical Applications
- **API Documentation**: Interactive code examples and troubleshooting
- **Research Assistant**: Paper summarization and citation tracking
- **DevOps Support**: Infrastructure documentation and incident response
- **Compliance Monitoring**: Regulatory document analysis

## 🚀 Getting Started

Ready to build your specialized RAG system? Check out our comprehensive guides:

**👉 [Quick Start Guide](docs/quickstart.md)** - Get running in 5 minutes

### Quick Setup Preview

```bash
# 1. Install dependencies
uv sync

# 2. Configure API key in configs/model_config.yaml
# 3. Add your domain-specific documents to data/raw/
# 4. Build index with semantic chunking
python scripts/build_faiss_index.py --use-semantic-chunking

# 5. Run the chatbot and start customizing
python -m src.components.ragchain
```

## 📚 Documentation

**👉 [Complete Documentation](docs/README.md)**

### Essential Guides
- **🚀 [Quick Start Guide](docs/quickstart.md)** - Get running in 5 minutes
- **📊 [System Evaluation](docs/evaluation.md)** - Comprehensive evaluation framework
- **📝 [Prompt Management](docs/prompts.md)** - Domain-specific prompt engineering

### API Configuration
```yaml
# In configs/model_config.yaml
openai:
  token: "sk-proj-xxxxxxxxxxxxxxxxxxxxx"  # Your OpenAI API key
  
# MLflow integration for experiment tracking
mlflow:
  tracking_uri: "http://localhost:5000"
  experiment_name: "rag-chatbot-production"
```

## 🔮 Extension Roadmap

This template is designed to grow with your needs. Consider implementing these extensions based on your specific requirements:

- **🔄 Multi-Agent RAG**: Orchestrate multiple specialized agents for complex workflows
- **🌐 Multi-Modal RAG**: Add support for image, audio, and video document processing
- **🤖 Fine-Tuning Integration**: Integrate custom model training workflows
- **📊 Advanced Analytics**: Implement user interaction analysis and optimization
- **🔒 Enterprise Security**: Add authentication, authorization, and audit logging
- **🔍 Advanced Retrieval**: Implement hybrid search, re-ranking, and adaptive strategies
- **🎯 Context Optimization**: Add intelligent compression and multi-document synthesis

---

## 📝 About This Project

This RAG-Chain template was designed and implemented from the ground up to provide a production-ready foundation for specialized chatbot development. Every component has been carefully crafted with extensibility and best practices in mind.

**Created by:** Pawarison Tanyu
**Project Type:** Original implementation  
**Purpose:** Production-ready RAG template for enterprise applications

---

*"A meticulously designed RAG template that accelerates development from prototype to production. Built with extensibility and best practices in mind."*
 