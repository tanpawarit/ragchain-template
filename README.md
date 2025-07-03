# RAG-Chain Chatbot

![Data Versioning](https://img.shields.io/badge/Data-Versioning-blue?style=flat-square)
![FAISS Index Versioning](https://img.shields.io/badge/Index-Versioning-blue?style=flat-square)
![Prompt Versioning](https://img.shields.io/badge/Prompts-Versioning-informational?style=flat-square)
![MLflow](https://img.shields.io/badge/MLOps-MLflow-orange?style=flat-square&logo=mlflow)
![DeepEval](https://img.shields.io/badge/Evaluation-DeepEval-purple?style=flat-square)
![Langchain](https://img.shields.io/badge/Framework-Langchain-green?style=flat-square&logo=langchain)  

A production-ready Retrieval-Augmented Generation (RAG) chatbot system with comprehensive data versioning, MLflow integration, and evaluation capabilities. Built for sales and support automation with Thai language support.

## 🚀 Quick Start

### For New Projects (No existing data versions or indexes)

```bash
# 1. Install dependencies
uv sync

# 2. Configure your API key (edit config.yaml with your OpenAI API key)
# Edit in config.yaml file:
openai:
  token: "your-openai-api-key-here"

# 3. Create required directories
mkdir -p artifacts
mkdir -p data/raw

# 4. Add your data files to data/raw/
# Place your .txt files in data/raw/ directory
# Example: data/raw/document1.txt, data/raw/document2.txt

# 5. Create first data version from your files
python scripts/create_data_version.py --files data/raw/*.txt --inc minor

# Or specify files explicitly:
# python scripts/create_data_version.py --files data/raw/workshop.txt data/raw/rerun.txt data/raw/overall.txt --inc minor

# 6. Build FAISS index (index directories will be created automatically)
python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking

# 7. Run the chatbot
python -m src.components.ragchain
```

### For Projects with Existing Data

```bash
# 1. Activate environment
source .venv/bin/activate  # or uv sync

# 2. Create new data version from existing files
python scripts/create_data_version.py --files data/raw/*.txt --inc minor

# 3. Build FAISS index
python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking

# 4. Run the chatbot
python -m src.components.ragchain
```

## ✨ Key Features

- **🤖 Production-Ready RAG**: Complete ingestion, chunking, embedding, and retrieval system
- **📊 Data Versioning**: Automated versioning with lineage tracking and GCS support
- **🔍 Faiss Index Versioning**: Automatic index versioning with data version synchronization
- **📝 Prompt Versioning**: YAML-based prompt templates with version control
- **📈 MLflow Integration**: Comprehensive experiment tracking and model registry
- **🧪 Multi-Modal Evaluation**: Retriever, generator, and end-to-end evaluation with DeepEval 
- **🇹🇭 Thai Language Support**: Optimized for Thai content with semantic chunking
- **💰 Cost Optimization**: Efficient API usage tracking and optimization
- **🔧 Auto Index Versioning**: Index directories automatically sync with data versions

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

## 📚 Documentation

**👉 [Complete Documentation](docs/README.md)**

### Quick Links
- **🚀 [Quick Start Guide](docs/quickstart.md)** - Get running in 5 minutes
- **☁️ [GCS Setup](docs/gcs_setup.md)** - Production storage setup
- **📊 [System Evaluation](docs/evaluation.md)** - System evaluation framework
- **🔧 [Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **📝 [Prompt Management](docs/prompts.md)** - Prompt templates and versioning

## 🛠️ Tech Stack

- **Language**: Python 3.12+
- **LLM and Embedding**: OpenAI GPT models
- **Vector Store**: FAISS 
- **Storage**: Local filesystem + Google Cloud Storage
- **Package Manager**: uv
- **Frameworks**: Langchain, DeepEval, MLflow

## 🔄 What's New

**Auto Index Versioning**: Index directories now automatically sync with data versions! No more manual directory creation.

"This Project Built on my meticulously designed architecture and Design System, with code accelerated through Cursor.sh and Claude."

## �� Setup Details

### System Requirements
- Python 3.9+
- `uv` package manager
- OpenAI API key (must have credits)

### Data Preparation
1. **Support .txt files only** - Thai or English text
2. **File Size** - Recommended < 10MB per file
3. **Number of Files** - Unlimited, but start with 2-5 files

### API Key Configuration
```yaml
# In config.yaml
openai:
  token: "sk-proj-xxxxxxxxxxxxxxxxxxxxx"  # API key from OpenAI
  
# MLflow configuration (not required)
mlflow:
  tracking_uri: "http://localhost:5000"
  experiment_name: "rag-chatbot-production"
```
 