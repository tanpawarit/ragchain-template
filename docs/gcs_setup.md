# Google Cloud Storage (GCS) Setup for Production

## Overview

Google Cloud Storage (GCS) is the recommended storage service for production due to several advantages:

- **Reliability**: 99.99% uptime SLA
- **Security**: Encryption at rest and in transit
- **Scalability**: No data size limitations
- **Performance**: CDN and high-speed access
- **Management**: Versioning, lifecycle management

## Installation

### 1. Install Dependencies

```bash
# Install google-cloud-storage
uv add google-cloud-storage

# Or install all optional dependencies
uv add ".[gcs]"
```

### 2. Setup Google Cloud Project

```bash
# Install Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 3. Create GCS Bucket

```bash
# Create bucket
gsutil mb gs://your-data-bucket

# Enable versioning (recommended)
gsutil versioning set on gs://your-data-bucket

# Set lifecycle management (cost optimization)
gsutil lifecycle set lifecycle.json gs://your-data-bucket
```

Example `lifecycle.json`:
```json
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {
        "age": 365,
        "isLive": true
      }
    }
  ]
}
```

### 4. Setup Authentication

#### Method 1: Service Account (recommended for production)

```bash
# Create service account
gcloud iam service-accounts create ragchain-sa \
    --display-name="RAGChain Service Account"

# Create key file
gcloud iam service-accounts keys create ragchain-sa-key.json \
    --iam-account=ragchain-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/ragchain-sa-key.json"
```

#### Method 2: Application Default Credentials (for development)

```bash
gcloud auth application-default login
```

### 5. Setup IAM Permissions

```bash
# Grant service account access to bucket
gsutil iam ch serviceAccount:ragchain-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com:objectAdmin gs://your-data-bucket
```

## Usage

### 1. GCS-Only Storage (recommended for production)

```python
from src.utils.pipeline.data_version_manager import DataVersionManager

# Create DVM for GCS
dvm = DataVersionManager(
    storage_type="gcs",
    gcs_bucket="your-data-bucket",
    gcs_prefix="ragchain-data",
    project_id="your-project-id",
    data_version="latest"
)

# Create new version
new_version = dvm.create_new_version(
    source_files=["data/source1.txt", "data/source2.txt"],
    increment_type="minor"
)

# List available versions
versions = dvm.list_available_versions()
print(f"Available versions: {versions}")

# Get data paths
data_path = dvm.get_data_version_path("v1.1")
index_path = dvm.get_index_path_for_version("v1.1")
```

### 2. Hybrid Storage (local + GCS)

```python
# Create DVM for hybrid storage
dvm = DataVersionManager(
    base_data_dir="data",
    base_index_dir="artifacts",
    storage_type="hybrid",
    gcs_bucket="your-data-bucket",
    gcs_prefix="ragchain-data",
    project_id="your-project-id"
)

# Create version locally
new_version = dvm.create_new_version(source_files, "minor")

# Upload to GCS
uploaded_files = dvm.upload_to_gcs(source_files, new_version)

# Download from GCS
downloaded_files = dvm.download_from_gcs(new_version, "temp_download")
```

### 3. Lineage Management

```python
# Create lineage record
lineage_record = dvm.create_lineage_record(
    index_path=str(index_path),
    data_version="v1.1",
    files_used=source_files,
    parameters={
        "chunk_size": 1000,
        "embedding_model": "text-embedding-ada-002",
        "index_type": "faiss"
    }
)

# Read lineage
lineage = dvm.get_lineage_for_index(str(index_path))
```

## Production Best Practices

### 1. Security

- Use Service Account instead of Application Default Credentials
- Set appropriate IAM permissions (principle of least privilege)
- Use VPC Service Controls if necessary
- Enable Cloud Audit Logs

### 2. Performance

- Use Regional bucket close to your application
- Use Transfer Service for large data volumes
- Configure CORS if necessary

### 3. Cost Optimization

- Use lifecycle management to delete old data
- Use appropriate Storage Classes (Standard, Nearline, Coldline)
- Monitor usage with Cloud Monitoring

### 4. Monitoring

```python
# Setup logging
import logging
logging.basicConfig(level=logging.INFO)

# Use Cloud Monitoring
from google.cloud import monitoring_v3
client = monitoring_v3.MetricServiceClient()
```

### 5. Backup Strategy

- Set up cross-region replication for critical data
- Use bucket versioning for data protection
- Implement regular backup verification

## Integration with RAG-Chain

### 1. Data Ingestion with GCS

```python
from src.components.ingestion import DataIngestionPipeline

# Create pipeline with GCS storage
pipeline = DataIngestionPipeline(
    model_config_path="configs/model_config.yaml",
    environment_config_path="config.yaml",
    storage_type="gcs",
    gcs_bucket="your-data-bucket",
    project_id="your-project-id",
    data_version="latest"
)

# Run ingestion
lineage_record = pipeline.run()
```

### 2. Building FAISS Index with GCS

```bash
# Build index using GCS storage
python scripts/build_faiss_index.py \
    --storage-type gcs \
    --gcs-bucket your-data-bucket \
    --project-id your-project-id \
    --data-version latest
```

### 3. Loading Vectorstore from GCS

```python
from src.utils.pipeline.vectorstore_manager import load_vectorstore
from src.utils.config.app_config import AppConfig

cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")

# Load from GCS
vectorstore = load_vectorstore(
    cfg, 
    data_version="latest",
    storage_type="gcs",
    gcs_bucket="your-data-bucket",
    project_id="your-project-id"
)
```

## Troubleshooting

### Common Issues

#### 1. Authentication Error
```
google.auth.exceptions.DefaultCredentialsError
```

**Solution**:
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set correctly
- Verify service account has proper permissions
- Check if gcloud is authenticated: `gcloud auth list`

#### 2. Bucket Access Denied
```
403 Forbidden: Access denied
```

**Solution**:
- Check IAM permissions for the service account
- Verify bucket exists: `gsutil ls gs://your-data-bucket`
- Ensure correct project ID is set

#### 3. Slow Upload/Download
**Solution**:
- Use regional buckets
- Enable parallel uploads: `gsutil -m cp`
- Check network connectivity

#### 4. High Costs
**Solution**:
- Implement lifecycle policies
- Use appropriate storage classes
- Monitor usage regularly

## Configuration Examples

### config.yaml for GCS
```yaml
openai:
  token: "your-openai-api-key"

gcs:
  bucket: "your-data-bucket"
  project_id: "your-project-id"
  prefix: "ragchain-data"

mlflow:
  tracking_uri: "http://localhost:5000"
  experiment_name: "ragchain-production"
```

### Environment Variables
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GCS_BUCKET="your-data-bucket"
```

## Monitoring and Alerting

### Cloud Monitoring Setup
```python
from google.cloud import monitoring_v3

def setup_monitoring():
    client = monitoring_v3.MetricServiceClient()
    
    # Create custom metrics for RAG performance
    descriptor = monitoring_v3.MetricDescriptor(
        type_="custom.googleapis.com/ragchain/query_latency",
        metric_kind=monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
        value_type=monitoring_v3.MetricDescriptor.ValueType.DOUBLE,
        description="RAG query latency in seconds"
    )
    
    project_name = f"projects/{PROJECT_ID}"
    client.create_metric_descriptor(
        name=project_name, 
        metric_descriptor=descriptor
    )
```

### Alerting Policies
- Set up alerts for high error rates
- Monitor storage costs
- Track query performance
- Alert on authentication failures

This completes the comprehensive GCS setup guide for production deployment of RAG-Chain. 