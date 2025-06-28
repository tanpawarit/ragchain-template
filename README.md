# RAG-Chain Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot system with comprehensive data versioning, MLflow integration, and evaluation capabilities. Built for sales and support automation with Thai language support.

## 🚀 Features

- **Production-Ready RAG Pipeline**: Complete ingestion, chunking, embedding, and retrieval system
- **Data Version Management**: Automated versioning with lineage tracking and GCS support
- **MLflow Integration**: Comprehensive experiment tracking and model registry
- **Multi-Modal Evaluation**: Retriever, generator, and end-to-end evaluation with DeepEval
- **Prompt Versioning**: YAML-based prompt templates with version control
- **Thai Language Support**: Optimized for Thai content with semantic chunking
- **Cost Optimization**: Efficient API usage tracking and optimization

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Evaluation](#evaluation)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [API Reference](#api-reference)

## 🏗️ Architecture

```
ragchain-chatbot/
├── src/
│   ├── components/           # Core RAG components
│   │   ├── ingestion.py     # Data ingestion pipeline
│   │   ├── ragchain.py      # CLI interface
│   │   └── ragchain_runner.py # RAG chain implementation
│   ├── prompts/             # Prompt management
│   │   ├── prompt_manager.py
│   │   └── templates/       # YAML prompt templates
│   └── utils/
│       ├── config/          # Configuration management
│       ├── logger.py        # Logging utilities
│       └── pipeline/        # Pipeline utilities
│           ├── data_version_manager.py
│           ├── mlflow_tracker.py
│           └── vectorstore_manager.py
├── scripts/                 # Utility scripts
├── evaluation/              # Evaluation modules
├── configs/                 # Configuration files
├── data/                    # Data storage
└── artifacts/               # Generated artifacts
```

## ⚡ Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Configure Environment

Create `config.yaml` in the project root:

```yaml
openai:
  token: "your-openai-api-key-here"

# MLflow configuration
mlflow:
  tracking_uri: "http://localhost:5000"
  experiment_name: "rag-chatbot-production"
```

### 3. Prepare Data

```bash
# Create data version from your files
python scripts/create_data_version.py --files data/raw/*.txt --inc minor

# Build FAISS index
python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking
```

### 4. Run Chatbot

```bash
# Interactive mode
python -m src.components.ragchain

# Or use the runner directly
from src.components.ragchain_runner import RAGChainRunner
```

## 🔧 Installation

### Prerequisites

- Python 3.12+
- OpenAI API key
- MLflow (optional, for experiment tracking)

### Install with uv (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd ragchain-chatbot

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### Install with pip

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### Model Configuration (`configs/model_config.yaml`)

```yaml
paths:
  data_folder: "data/raw"
  file_names:
    - "workshop.txt"
    - "rerun.txt"
    - "overall.txt"
  faiss_index: "artifacts/faiss_product_index"

models:
  embedding: "text-embedding-3-small"
  llm: "gpt-3.5-turbo"

retriever:
  search_type: "similarity"
  k_value: 4

prompt_config:
  template_name: "sales_support"
  version: "v1"
```

### Environment Configuration (`config.yaml`)

```yaml
openai:
  token: "sk-your-api-key"

# MLflow configuration
mlflow:
  tracking_uri: "http://localhost:5000"
  experiment_name: "rag-chatbot-production"
```

## 📖 Usage

### Data Management

#### Create New Data Version

```bash
# Create minor version update
python scripts/create_data_version.py --files data/raw/*.txt --inc minor

# Create major version update
python scripts/create_data_version.py --files data/raw/*.txt --inc major
```

#### Build FAISS Index

```bash
# Build with semantic chunking (recommended)
python scripts/build_faiss_index.py \
  --model-config configs/model_config.yaml \
  --env-config config.yaml \
  --data-version latest \
  --use-semantic-chunking \
  --chunk-size 1000 \
  --chunk-overlap 200
```

### RAG Pipeline Usage

#### Interactive Mode

```bash
python -m src.components.ragchain
```

#### Programmatic Usage

```python
from src.components.ragchain_runner import RAGChainRunner
from src.utils.config.app_config import AppConfig
from src.utils.pipeline.vectorstore_manager import load_vectorstore

# Load configuration
cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")

# Load vectorstore
vectorstore = load_vectorstore(cfg, data_version="latest")

# Create RAG runner
rag = RAGChainRunner(cfg, vectorstore=vectorstore)

# Get answer
answer = rag.answer("What courses do you offer?")
print(answer)
```

### Prompt Management

#### Create New Prompt Template

```yaml
# src/prompts/templates/sales_support_v2.yaml
template: |
  ### ROLE ###
  You are an AI Sales & Support Specialist for Investic Company.

  ### OBJECTIVE ###
  Convert customer questions into sales opportunities by providing accurate information,
  emphasizing benefits, and creating impressive experiences based on KNOWLEDGE BASE only.

  ### TONE OF VOICE ###
  - Professional and helpful
  - Persuasive and confident
  - Thai language, formal tone

  ### KNOWLEDGE BASE ###
  {context}

  ### CUSTOMER QUESTION ###
  {question}

  ### RESPONSE ###
```

#### Use Prompt Manager

```python
from src.prompts.prompt_manager import PromptManager

pm = PromptManager()
template = pm.get_template("sales_support", "v2")
formatted = pm.format_template("sales_support", "v2", context="...", question="...")
```

## 📊 Evaluation

### End-to-End Evaluation

```python
from evaluation.e2e_evaluation import evaluate_e2e_system
from src.components.ragchain_runner import RAGChainRunner

# Load test data
with open("evaluation/test_data/golden_dataset_v1.json", "r") as f:
    test_data = json.load(f)

# Create RAG system
rag_system = RAGChainRunner(cfg, vectorstore=vectorstore)

# Evaluate
results = evaluate_e2e_system(
    test_data=test_data,
    rag_system=rag_system,
    evaluation_model="gpt-4o",
    experiment_name="e2e_evaluation"
)
```

### Run Evaluation Scripts

```bash
# End-to-end evaluation
python evaluation/e2e_evaluation.py

# Retriever evaluation
python evaluation/retriever_evaluation.py

# Generator evaluation
python evaluation/generator_evaluation.py
```

### MLflow Dashboard

```bash
# Start MLflow UI
mlflow ui --port 5000

# View experiments and runs
open http://localhost:5000
```

## 🛠️ Development

### Project Structure

```
src/
├── components/           # Core RAG components
│   ├── ingestion.py     # Data ingestion with versioning
│   ├── ragchain.py      # CLI interface
│   └── ragchain_runner.py # RAG chain implementation
├── prompts/             # Prompt management system
│   ├── prompt_manager.py # Template loading and versioning
│   └── templates/       # YAML prompt templates
└── utils/
    ├── config/          # Configuration management
    ├── logger.py        # Structured logging
    └── pipeline/        # Pipeline utilities
        ├── data_version_manager.py # Data versioning
        ├── mlflow_tracker.py      # MLflow integration
        └── vectorstore_manager.py # Vector store management
```

### Key Components

#### DataIngestionPipeline

Handles document loading, chunking, embedding, and FAISS index creation with data versioning support.

```python
from src.components.ingestion import DataIngestionPipeline

pipeline = DataIngestionPipeline(
    model_config_path="configs/model_config.yaml",
    environment_config_path="config.yaml",
    data_version="latest"
)

pipeline.run(chunking_params={
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "use_semantic_chunking": True
})
```

#### DataVersionManager

Manages data versions, index versions, and data lineage tracking.

```python
from src.utils.pipeline.data_version_manager import DataVersionManager

dvm = DataVersionManager(
    base_data_dir="data",
    base_index_dir="artifacts"
)

# Create new version
new_version = dvm.create_new_version(["data/raw/file.txt"], "minor")

# Get lineage
lineage = dvm.get_lineage_for_index("artifacts/faiss_index_v1.1")
```

#### MLflowTracker

Simplified MLflow integration for experiment tracking.

```python
from src.utils.pipeline.mlflow_tracker import MLflowTracker

with MLflowTracker(experiment_name="rag_experiment", run_name="test_run") as tracker:
    tracker.log_params({"model": "gpt-4o", "k_value": 4})
    tracker.log_metrics({"accuracy": 0.95, "latency": 1.2})
    tracker.log_artifact("artifacts/faiss_index_v1.1")
```

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync

EXPOSE 8000
CMD ["python", "-m", "src.api.main"]
```

### FastAPI Service

```python
# src/api/main.py
from fastapi import FastAPI
from src.components.ragchain_runner import RAGChainRunner

app = FastAPI()
rag = RAGChainRunner(cfg, vectorstore=vectorstore)

@app.post("/chat")
async def chat(question: str, user_id: str = None):
    answer = rag.answer(question, user_id=user_id)
    return {"answer": answer}
```

### Cloud Deployment

#### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/rag-chatbot
gcloud run deploy rag-chatbot --image gcr.io/PROJECT_ID/rag-chatbot --platform managed
```

#### AWS Lambda

```bash
# Package for Lambda
pip install -t package/ -r requirements.txt
cd package && zip -r ../deployment-package.zip .
```

### Monitoring and Logging

```python
# Enable structured logging
import logging
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("RAG system started", extra={"user_id": user_id, "question": question})
```

## 📚 API Reference

### Core Classes

#### RAGChainRunner

Main RAG system orchestrator.

```python
class RAGChainRunner:
    def __init__(self, cfg: AppConfig, vectorstore: FAISS, mlflow_tracker: Optional[MLflowTracker] = None)
    
    def answer(self, question: str, user_id: Optional[str] = None) -> str
```

#### DataIngestionPipeline

Data processing pipeline with versioning.

```python
class DataIngestionPipeline:
    def __init__(self, cfg: Optional[AppConfig] = None, data_version: str = "latest")
    
    def run(self, chunking_params: Dict[str, Any]) -> None
    def load_documents(self) -> List[Document]
    def chunk_documents(self, documents: List[Document], **kwargs) -> List[Document]
    def create_and_save_vectorstore(self, chunks: List[Document]) -> None
```

#### DataVersionManager

Data versioning and lineage management.

```python
class DataVersionManager:
    def __init__(self, base_data_dir: str, base_index_dir: str, data_version: str = "latest")
    
    def create_new_version(self, source_files: List[str], increment_type: str = "minor") -> str
    def get_data_version_path(self, version: Optional[str] = None) -> Path
    def get_index_path_for_version(self, version: Optional[str] = None) -> Path
    def create_lineage_record(self, index_path: str, data_version: str, files_used: List[str], parameters: Dict[str, Any]) -> Dict[str, Any]
```

### Configuration

#### AppConfig

Application configuration with type safety.

```python
@dataclass
class AppConfig:
    embedding_model_name: str
    llm_model_name: str
    data_folder: str
    file_names: List[str]
    faiss_index_path: str
    retriever_search_type: str
    retriever_k_value: int
    openai_token: str
    prompt_template: str
    prompt_template_name: str
    prompt_template_version: Optional[str]
    
    @classmethod
    def from_files(cls, model_config_path: str, environment_config_path: str) -> AppConfig
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Use type hints consistently
- Write comprehensive tests
- Update documentation
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) for RAG pipeline
- [MLflow](https://mlflow.org/) for experiment tracking
- [DeepEval](https://github.com/confident-ai/deepeval) for evaluation
- [FAISS](https://faiss.ai/) for vector similarity search

## 📞 Support

For support and questions:

- Create an issue on GitHub
- Check the [documentation](docs/)
- Review the [notebooks](notebook/) for examples

---

**Built with ❤️ for production-ready RAG systems**