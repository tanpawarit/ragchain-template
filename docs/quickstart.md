# Quick Start Guide

Get RAG-Chain Chatbot up and running in 5 minutes.

## Prerequisites

- Python 3.9+
- `uv` package manager
- OpenAI API key (must have credits)
- 4GB+ available RAM

## Setup for New Projects (No existing data versions or indexes)

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

### 4. Create Data Version

```bash
# Create first data version from your files
python scripts/create_data_version.py --files data/raw/*.txt --inc minor

# Or specify files explicitly:
# python scripts/create_data_version.py --files data/raw/workshop.txt data/raw/rerun.txt data/raw/overall.txt --inc minor
```

### 5. Build FAISS Index

```bash
# Build FAISS index (index directories will be created automatically)
python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking
```

### 6. Run the Chatbot

```bash
# Start the interactive chatbot
python -m src.components.ragchain
```

## Setup for Projects with Existing Data

### Quick Setup

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
- **📝 [Prompt Management](prompts.md)** - Customize AI responses and prompt templates
- **📊 [System Evaluation](evaluation.md)** - Test and monitor your RAG system performance

### Production Deployment  
- **☁️ [GCS Setup](gcs_setup.md)** - Scale with Google Cloud Storage
- **📚 [Complete Documentation](README.md)** - Explore all features and guides

## Troubleshooting

**Common Issues:**

- **API Key Error**: Ensure your OpenAI API key is valid and has sufficient credits
- **Memory Error**: Reduce chunk size or use a smaller embedding model
- **Import Error**: Run `uv sync` to install all dependencies
- **File Not Found**: Ensure your .txt files are in the `data/raw/` directory
- **Index Error**: Make sure you've built the FAISS index before running the chatbot

For additional help, check the project documentation or create an issue in the repository. 