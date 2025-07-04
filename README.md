# RAG-Chain Chatbot
 
![FAISS](https://img.shields.io/badge/FAISS-blue?style=flat-square)
![Prompt Versioning](https://img.shields.io/badge/Prompts-Versioning-informational?style=flat-square)
![MLflow](https://img.shields.io/badge/MLOps-MLflow-orange?style=flat-square&logo=mlflow)
![DeepEval](https://img.shields.io/badge/Evaluation-DeepEval-purple?style=flat-square)
![Langchain](https://img.shields.io/badge/Framework-Langchain-green?style=flat-square&logo=langchain)  

A simple and production-ready Retrieval-Augmented Generation (RAG) chatbot system with MLflow integration and evaluation capabilities. Built for sales and support automation with Thai language support.

## ✨ Key Features

- **🤖 Simple RAG System**: Complete ingestion, chunking, embedding, and retrieval system
- **📝 Prompt Management**: YAML-based prompt templates with version control
- **📈 MLflow Integration**: Experiment tracking and logging
- **🧪 Multi-Modal Evaluation**: Retriever, generator, and end-to-end evaluation with DeepEval
- **🌏 Thai Language Support**: Optimized for both Thai and English content
- **⚡ Easy Setup**: Simplified configuration and deployment

## 🛠️ Tech Stack

- **Language**: Python 3.12+
- **LLM and Embedding**: OpenAI GPT models
- **Vector Store**: FAISS 
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
│           ├── mlflow_tracker.py          # MLflow experiment tracking
│           └── vectorstore_manager.py     # Vector store operations and management
├── evaluation/                            # Evaluation framework
├── scripts/                              # Utility scripts
├── configs/                              # Configuration files
├── data/                                 # Data storage
│   └── raw/                             # Raw text documents
└── artifacts/                           # Generated FAISS indexes
```

### 🔄 Data Flow Architecture

```
📝 Raw Text Files (.txt)
    ⬇️
🔨 Data Ingestion Pipeline
    ⬇️ (loads & chunks documents)
📄 Document Chunks
    ⬇️
🤖 OpenAI Embeddings
    ⬇️ (generates vector embeddings)
🗂️ FAISS Vector Store
    ⬇️ (saves to artifacts/)
💾 artifacts/faiss_product_index/
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
# 4. Build index
python scripts/build_faiss_index.py --use-semantic-chunking

# 5. Run the chatbot
python -m src.components.ragchain
```

## 📚 Documentation

**👉 [Complete Documentation](docs/README.md)**

### Essential Guides
- **🚀 [Quick Start Guide](docs/quickstart.md)** - Get running in 5 minutes
- **📊 [System Evaluation](docs/evaluation.md)** - System evaluation framework
- **📝 [Prompt Management](docs/prompts.md)** - Prompt templates and versioning

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
