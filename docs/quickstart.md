# Quick Start Guide

Get RAG-Chain Chatbot up and running in 5 minutes.

## Prerequisites

- Python 3.12+
- OpenAI API key
- 4GB+ available RAM

## 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd ragchain-chatbot

# Install with uv (recommended)
uv sync

# Or with pip
pip install -r requirements.txt
```

## 2. Configuration

Create `config.yaml` in the project root:

```yaml
openai:
  token: "your-openai-api-key-here"

mlflow:
  tracking_uri: "http://localhost:5000"
  experiment_name: "rag-chatbot-production"
```

## 3. Prepare Sample Data

```bash
# Create your first data version
python scripts/create_data_version.py --files data/raw/*.txt --inc minor

# Build FAISS index with semantic chunking
python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking
```

## 4. Run the Chatbot

```bash
# Interactive mode
python -m src.components.ragchain
```

## 5. Test Your Setup

Try asking a question related to your data:
```
User: What is the main topic of the documents?
Bot: [AI-generated response based on your data]
```

## Next Steps

- [GCS Setup](gcs_setup.md) - Production deployment with Google Cloud Storage
- [System Evaluation](evaluation.md) - Evaluate your RAG system performance
- [Prompt Management](prompts.md) - Customize prompt templates

## Troubleshooting

**Common Issues:**
- **API Key Error**: Ensure your OpenAI API key is valid and has sufficient credits
- **Memory Error**: Reduce chunk size or use a smaller model
- **Import Error**: Run `uv sync` to install all dependencies

For more help, see [Troubleshooting Guide](troubleshooting.md). 