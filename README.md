# RAG-Chain Chatbot
 
![FAISS](https://img.shields.io/badge/FAISS-blue?style=flat-square)
![Prompt Versioning](https://img.shields.io/badge/Prompts-Versioning-informational?style=flat-square)
![MLflow](https://img.shields.io/badge/MLOps-MLflow-orange?style=flat-square&logo=mlflow)
![DeepEval](https://img.shields.io/badge/Evaluation-DeepEval-purple?style=flat-square)
![Langchain](https://img.shields.io/badge/Framework-Langchain-green?style=flat-square&logo=langchain)  

A production-ready Retrieval-Augmented Generation (RAG) chatbot system with comprehensive data versioning, MLflow integration, and evaluation capabilities. Built for sales and support automation with Thai language support.

## ✨ Key Features

- **🤖 Production-Ready RAG**: Complete ingestion, chunking, embedding, and retrieval system
- **📊 Data Versioning**: Automated versioning with lineage tracking and GCS support
- **🔍 Faiss Index Versioning**: Automatic index versioning with data version synchronization
- **📝 Prompt Versioning**: YAML-based prompt templates with version control
- **📈 MLflow Integration**: Comprehensive experiment tracking and model registry
- **🧪 Multi-Modal Evaluation**: Retriever, generator, and end-to-end evaluation with DeepEval
- **🌏 Thai Language Support**: Optimized for both Thai and English content
- **☁️ Cloud-Ready**: GCS integration for production deployments

## 🛠️ Tech Stack

- **Language**: Python 3.12+
- **LLM and Embedding**: OpenAI GPT models
- **Vector Store**: FAISS 
- **Storage**: Local filesystem + Google Cloud Storage
- **Package Manager**: uv
- **Frameworks**: Langchain, DeepEval, MLflow
- **Evaluation**: Multi-modal evaluation with DeepEval metrics

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
│           ├── data_version_manager.py    # Data versioning and lineage tracking
│           ├── mlflow_tracker.py          # MLflow experiment tracking
│           └── vectorstore_manager.py     # Vector store operations and management
├── evaluation/                            # Evaluation framework
├── scripts/                              # Utility scripts
├── configs/                              # Configuration files
├── data/                                 # Data storage (auto-versioned)
│   └── raw/                             # Raw text documents
│       ├── latest -> vX.X              # Symlink to latest version
│       └── vX.X/                       # Version directories
└── artifacts/                           # Generated indexes (auto-versioned)
    ├── latest -> vX.X                   # Symlink to latest index (auto-created)
    └── vX.X/                            # Index version directories (auto-created)
```

### 🔄 Data Flow Architecture

```
📝 Raw Text Files (.txt)
    ⬇️
📦 Data Version Manager
    ⬇️ (creates versioned directories)
📂 data/raw/v1.X/
    ⬇️
🔨 Data Ingestion Pipeline
    ⬇️ (loads & chunks documents)
📄 Document Chunks
    ⬇️
🤖 OpenAI Embeddings
    ⬇️ (generates vector embeddings)
🗂️ FAISS Vector Store
    ⬇️ (saves to artifacts/vX.X/)
💾 artifacts/latest/faiss_product_index/
    ⬇️
🤖 RAG Chain Runner
    ⬇️ (retrieval + generation)
💬 Chatbot Response
```

## 🚀 Getting Started

Ready to try it out? Check out our comprehensive guides:

**👉 [Quick Start Guide](docs/quickstart.md)** - Get running in 5 minutes

### Quick Setup Preview

```bash
# 1. Install dependencies
uv sync

# 2. Configure API key in configs/model_config.yaml
# 3. Add your .txt files to data/raw/
# 4. Create data version and build index
python scripts/create_data_version.py --files data/raw/*.txt --inc minor
python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking

# 5. Run the chatbot
python -m src.components.ragchain
```

## 📚 Documentation

**👉 [Complete Documentation](docs/README.md)**

### Essential Guides
- **🚀 [Quick Start Guide](docs/quickstart.md)** - Get running in 5 minutes
- **☁️ [GCS Setup](docs/gcs_setup.md)** - Production storage setup
- **📊 [System Evaluation](docs/evaluation.md)** - System evaluation framework
- **📝 [Prompt Management](docs/prompts.md)** - Prompt templates and versioning

## 🔄 What's New

**Auto Index Versioning**: Index directories now automatically sync with data versions! No more manual directory creation.

## 💡 System Requirements & Configuration

### Prerequisites
- **Python**: 3.9+
- **Package Manager**: uv
- **API Key**: OpenAI API key with credits
- **Memory**: 4GB+ available RAM

### Data Specifications
- **Format**: .txt files only
- **Languages**: Thai and English support
- **File Size**: Recommended < 10MB per file
- **Scalability**: Unlimited files (start with 2-5)

### API Configuration
```yaml
# In configs/model_config.yaml
openai:
  token: "sk-proj-xxxxxxxxxxxxxxxxxxxxx"  # Your OpenAI API key
  
# MLflow integration (optional)
mlflow:
  tracking_uri: "http://localhost:5000"
  experiment_name: "rag-chatbot-production"
```

---

*"This project built on my meticulously designed architecture and Design System, with code accelerated through Cursor.sh and Claude."*
