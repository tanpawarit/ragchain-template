# RAG-Chain Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot system with comprehensive data versioning, MLflow integration, and evaluation capabilities. Built for sales and support automation with Thai language support.

## 🚀 Quick Start

```bash
# Install dependencies
uv sync

# Configure your API key
cp config.example.yaml config.yaml
# Edit config.yaml with your OpenAI API key

# Prepare data and run
python scripts/create_data_version.py --files data/raw/*.txt --inc minor
python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking
python -m src.components.ragchain
```

## ✨ Key Features

- **🤖 Production-Ready RAG**: Complete ingestion, chunking, embedding, and retrieval system
- **📊 Data Versioning**: Automated versioning with lineage tracking and GCS support
- **📈 MLflow Integration**: Comprehensive experiment tracking and model registry
- **🧪 Multi-Modal Evaluation**: Retriever, generator, and end-to-end evaluation with DeepEval
- **📝 Prompt Versioning**: YAML-based prompt templates with version control
- **🇹🇭 Thai Language Support**: Optimized for Thai content with semantic chunking
- **💰 Cost Optimization**: Efficient API usage tracking and optimization

## 🏗️ Architecture

```
ragchain-chatbot/
├── src/                    # Core application code
│   ├── components/         # RAG pipeline components
│   ├── prompts/           # Prompt management system
│   └── utils/             # Utilities and configuration
├── evaluation/            # Evaluation framework
├── scripts/              # Utility scripts
├── configs/              # Configuration files
└── docs/                 # 📚 Complete documentation
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
- **Evaluation**: DeepEval framework
- **Model Tracking**: MLflow
- **Storage**: Local filesystem + Google Cloud Storage
- **Package Manager**: uv
 
## 🆘 Support

- 📖 [Documentation](docs/README.md)
- 🐛 [Issue Tracker](https://github.com/your-org/ragchain-chatbot/issues)
- 💬 [Discussions](https://github.com/your-org/ragchain-chatbot/discussions)
- 🔧 [Troubleshooting](docs/troubleshooting.md)

"This Project Built on my meticulously designed architecture and Design System, with code accelerated through Cursor.sh and Claude."