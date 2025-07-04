# Quick Start Guide

Get RAG-Chain Chatbot up and running in 5 minutes.

## Prerequisites

- Python 3.9+
- `uv` package manager
- OpenAI API key (must have credits)
- 4GB+ available RAM

## Setup

### 1. Installation & Environment Setup

```bash
# Install dependencies
uv sync

# Create required directories
mkdir -p artifacts
mkdir -p data/raw
```

### 2. API Key Configuration

Edit the `configs/model_config.yaml` file with your OpenAI API key:

```yaml
# In configs/model_config.yaml
openai:
  token: "your-openai-api-key-here"
```

### 3. Data Preparation

Add your data files to the `data/raw/` directory:

```bash
# Place your .txt files in data/raw/ directory
# Example: data/raw/document1.txt, data/raw/document2.txt
```

**Data Requirements:**
- **Format**: Support .txt files only
- **Languages**: Thai or English text
- **File Size**: Recommended < 10MB per file
- **Number of Files**: Unlimited, but start with 2-5 files

### 4. Build FAISS Index

```bash
# Build FAISS index with semantic chunking
python scripts/build_faiss_index.py --use-semantic-chunking

# Or with character-based chunking
python scripts/build_faiss_index.py --chunk-size 1000 --chunk-overlap 200
```

### 5. Run the Chatbot

```bash
# Start the interactive chatbot
python -m src.components.ragchain
```

## Test Your Setup

Try asking questions related to your data:

```
User: What is the main topic of the documents?
Bot: [AI-generated response based on your data]

User: Can you summarize the key points?
Bot: [AI-generated summary based on your indexed documents]
```

## Configuration Details

### Complete API Configuration

```yaml
# In configs/model_config.yaml
openai:
  token: "sk-proj-xxxxxxxxxxxxxxxxxxxxx"  # API key from OpenAI
  
# MLflow configuration (optional)
mlflow:
  tracking_uri: "http://localhost:5000"
  experiment_name: "rag-chatbot-production"
```

## Next Steps

### Customize Your System
- **[Prompt Management](prompts.md)** - Customize AI responses and prompt templates
- **[System Evaluation](evaluation.md)** - Test and monitor your RAG system performance

### Advanced Features
- **[Complete Documentation](README.md)** - Explore all features and guides

## Troubleshooting

**Common Issues:**

- **API Key Error**: Ensure your OpenAI API key is valid and has sufficient credits
- **Memory Error**: Reduce chunk size or use a smaller embedding model
- **Import Error**: Run `uv sync` to install all dependencies
- **File Not Found**: Ensure your .txt files are in the `data/raw/` directory
- **Index Error**: Make sure you've built the FAISS index before running the chatbot

For additional help, check the project documentation or create an issue in the repository. 