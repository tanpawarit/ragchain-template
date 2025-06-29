# Troubleshooting Guide

## Common Issues

### 1. API Key Error

**Symptoms**: `openai.AuthenticationError`

**Solution**:
```bash
# Check API key in config.yaml
cat config.yaml

# Check credits in OpenAI dashboard
# https://platform.openai.com/usage
```

### 2. Memory Error

**Symptoms**: `MemoryError` or `OOM killed`

**Solution**:
```yaml
# Reduce chunk_size in config
chunk_size: 500  # from 1000
chunk_overlap: 100  # from 200

# Or use smaller models
models:
  embedding: "text-embedding-3-small"
  llm: "gpt-3.5-turbo"
```

### 3. Import Error

**Symptoms**: `ModuleNotFoundError`

**Solution**:
```bash
# Reinstall dependencies
uv sync

# Or with pip
pip install -r requirements.txt
```

### 4. FAISS Index Error

**Symptoms**: `RuntimeError: Error in faiss`

**Solution**:
```bash
# Rebuild index
python scripts/build_faiss_index.py --data-version latest

# Check if index files exist
ls -la artifacts/
```

### 5. Data Version Error

**Symptoms**: `FileNotFoundError: Data version not found`

**Solution**:
```bash
# Check available versions
python -c "from src.utils.pipeline.data_version_manager import DataVersionManager; print(DataVersionManager().list_available_versions())"

# Create new version
python scripts/create_data_version.py --files data/raw/*.txt --inc minor
```

### 6. MLflow Connection Error

**Symptoms**: `ConnectionError: MLflow tracking server`

**Solution**:
```bash
# Start MLflow server
mlflow ui --port 5000 &

# Or use local file store
# Edit config.yaml
mlflow:
  tracking_uri: "file:./mlruns"
```

### 7. Thai Language Issues

**Symptoms**: Thai characters display incorrectly

**Solution**:
```python
# Set encoding
import locale
locale.setlocale(locale.LC_ALL, 'th_TH.UTF-8')

# Use semantic chunking for Thai text
python scripts/build_faiss_index.py --use-semantic-chunking
```

## Debugging

### 1. Enable Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Check Configuration

```python
from src.utils.config.app_config import AppConfig

cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")
print(cfg)
```

### 3. Test Components Separately

```python
# Test embedding
from src.utils.config.app_config import AppConfig
cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")

from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model=cfg.embedding_model_name)
result = embeddings.embed_query("test")
print(f"Embedding dimension: {len(result)}")

# Test LLM
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model=cfg.llm_model_name)
result = llm.invoke("Hello")
print(result.content)
```

## Performance Issues

### 1. Slow Response

**Causes**:
- Index too large
- k_value too high
- Network latency

**Solutions**:
```yaml
# Reduce k_value
retriever:
  k_value: 3  # from 5

# Use faster models
models:
  llm: "gpt-3.5-turbo"  # instead of gpt-4
```

### 2. High API Costs

**Solutions**:
```yaml
# Use cheaper models
models:
  embedding: "text-embedding-3-small"
  llm: "gpt-3.5-turbo"

# Reduce chunk size
chunk_size: 800
```

## Getting Help

1. **Check logs** - Review complete error messages
2. **Try minimal examples** - Test only the problematic component
3. **Check versions** - Verify dependency versions
4. **Create an issue** - In the GitHub repository with complete error logs 