# RAG-Chain Chatbot Documentation

Complete guide for RAG-Chain Chatbot - An AI-powered chatbot system for sales and support operations.

## 📚 Main Guides

### Getting Started
- **[Quick Start](quickstart.md)** - Get up and running in 5 minutes
- **[GCS Setup](gcs_setup.md)** - Configure Google Cloud Storage

### User Guides
- **[System Evaluation](evaluation.md)** - How to evaluate your RAG system
- **[Prompt Management](prompts.md)** - Manage prompt templates
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## 🚀 Quick Start

```bash
# Installation
uv sync

# Configuration
cp config.example.yaml config.yaml
# Edit config.yaml and add your OpenAI API key

# Run
python scripts/create_data_version.py --files data/raw/*.txt --inc minor
python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking
python -m src.components.ragchain
```

## 🏗️ Project Structure

```
ragchain-chatbot/
├── src/                    # Core source code
│   ├── components/         # RAG pipeline components
│   ├── prompts/           # Prompt management
│   └── utils/             # Utility modules
├── evaluation/            # Evaluation framework
├── scripts/              # Helper scripts
├── configs/              # Configuration files
└── docs/                 # Documentation
```

## 💡 Tips

- **New to RAG?** Start with [Quick Start](quickstart.md)
- **Production deployment?** See [GCS Setup](gcs_setup.md)
- **Having issues?** Check [Troubleshooting](troubleshooting.md)
- **Need evaluation?** Read [Evaluation Guide](evaluation.md)

## 🔗 Useful Links

- [GitHub Repository](https://github.com/your-org/ragchain-chatbot)
- [Issues & Bug Reports](https://github.com/your-org/ragchain-chatbot/issues) 