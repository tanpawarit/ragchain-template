# การตั้งค่า Google Cloud Storage (GCS) สำหรับ Production

## ภาพรวม

Google Cloud Storage (GCS) เป็นบริการจัดเก็บข้อมูลที่แนะนำสำหรับ production เพราะมีข้อดีหลายประการ:

- **ความน่าเชื่อถือ**: 99.99% uptime SLA
- **ความปลอดภัย**: Encryption at rest และ in transit
- **การขยายตัว**: ไม่มีข้อจำกัดเรื่องขนาดข้อมูล
- **ประสิทธิภาพ**: CDN และความเร็วสูง
- **การจัดการ**: Versioning, lifecycle management

## การติดตั้ง

### 1. ติดตั้ง Dependencies

```bash
# ติดตั้ง google-cloud-storage
uv add google-cloud-storage

# หรือติดตั้ง optional dependencies ทั้งหมด
uv add ".[gcs]"
```

### 2. ตั้งค่า Google Cloud Project

```bash
# ติดตั้ง Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Login และตั้งค่า project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 3. สร้าง GCS Bucket

```bash
# สร้าง bucket
gsutil mb gs://your-data-bucket

# ตั้งค่า versioning (แนะนำ)
gsutil versioning set on gs://your-data-bucket

# ตั้งค่า lifecycle management (ลดค่าใช้จ่าย)
gsutil lifecycle set lifecycle.json gs://your-data-bucket
```

ตัวอย่าง `lifecycle.json`:
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

### 4. ตั้งค่า Authentication

#### วิธีที่ 1: Service Account (แนะนำสำหรับ production)

```bash
# สร้าง service account
gcloud iam service-accounts create ragchain-sa \
    --display-name="RAGChain Service Account"

# สร้าง key file
gcloud iam service-accounts keys create ragchain-sa-key.json \
    --iam-account=ragchain-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# ตั้งค่า environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/ragchain-sa-key.json"
```

#### วิธีที่ 2: Application Default Credentials (สำหรับ development)

```bash
gcloud auth application-default login
```

### 5. ตั้งค่า IAM Permissions

```bash
# ให้สิทธิ์ service account เข้าถึง bucket
gsutil iam ch serviceAccount:ragchain-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com:objectAdmin gs://your-data-bucket
```

## การใช้งาน

### 1. GCS-Only Storage (แนะนำสำหรับ production)

```python
from src.utils.pipeline.data_version_manager import DataVersionManager

# สร้าง DVM สำหรับ GCS
dvm = DataVersionManager(
    storage_type="gcs",
    gcs_bucket="your-data-bucket",
    gcs_prefix="ragchain-data",
    project_id="your-project-id",
    data_version="latest"
)

# สร้างเวอร์ชันใหม่
new_version = dvm.create_new_version(
    source_files=["data/source1.txt", "data/source2.txt"],
    increment_type="minor"
)

# ดูรายการเวอร์ชัน
versions = dvm.list_available_versions()
print(f"Available versions: {versions}")

# รับเส้นทางข้อมูล
data_path = dvm.get_data_version_path("v1.1")
index_path = dvm.get_index_path_for_version("v1.1")
```

### 2. Hybrid Storage (local + GCS)

```python
# สร้าง DVM สำหรับ hybrid storage
dvm = DataVersionManager(
    base_data_dir="data",
    base_index_dir="artifacts",
    storage_type="hybrid",
    gcs_bucket="your-data-bucket",
    gcs_prefix="ragchain-data",
    project_id="your-project-id"
)

# สร้างเวอร์ชันใน local
new_version = dvm.create_new_version(source_files, "minor")

# อัปโหลดไปยัง GCS
uploaded_files = dvm.upload_to_gcs(source_files, new_version)

# ดาวน์โหลดจาก GCS
downloaded_files = dvm.download_from_gcs(new_version, "temp_download")
```

### 3. การจัดการ Lineage

```python
# สร้าง lineage record
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

# อ่าน lineage
lineage = dvm.get_lineage_for_index(str(index_path))
```

## Production Best Practices

### 1. Security

- ใช้ Service Account แทน Application Default Credentials
- ตั้งค่า IAM permissions ให้เหมาะสม (principle of least privilege)
- ใช้ VPC Service Controls หากจำเป็น
- เปิดใช้ Cloud Audit Logs

### 2. Performance

- ใช้ Regional bucket ที่ใกล้กับ application
- ใช้ Transfer Service สำหรับข้อมูลจำนวนมาก
- ตั้งค่า CORS หากจำเป็น

### 3. Cost Optimization

- ใช้ lifecycle management เพื่อลบข้อมูลเก่า
- ใช้ Storage Classes ที่เหมาะสม (Standard, Nearline, Coldline)
- Monitor usage ด้วย Cloud Monitoring

### 4. Monitoring

```python
# ตั้งค่า logging
import logging
logging.basicConfig(level=logging.INFO)

# ใช้ Cloud Monitoring
from google.cloud import monitoring_v3
client = monitoring_v3.MetricServiceClient()
```

### 5. Backup Strategy

- ใช้ GCS versioning
- ตั้งค่า cross-region replication
- ใช้ Cloud Storage Transfer Service สำหรับ backup

## การแก้ไขปัญหา

### 1. Authentication Errors

```bash
# ตรวจสอบ credentials
gcloud auth list

# ตรวจสอบ service account
gcloud iam service-accounts list

# ตรวจสอบ permissions
gsutil iam get gs://your-data-bucket
```

### 2. Permission Errors

```bash
# ให้สิทธิ์เพิ่มเติม
gsutil iam ch serviceAccount:ragchain-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com:storage.admin gs://your-data-bucket
```

### 3. Network Issues

```bash
# ตรวจสอบ connectivity
gsutil ls gs://your-data-bucket

# ตรวจสอบ quota
gcloud compute regions describe YOUR_REGION
```

## ตัวอย่างการใช้งานจริง

ดูไฟล์ `examples/production_gcs_setup.py` สำหรับตัวอย่างการใช้งานที่สมบูรณ์

## การอัปเกรดจาก Local Storage

หากคุณมีข้อมูลใน local storage และต้องการย้ายไป GCS:

```python
# 1. สร้าง hybrid DVM
dvm = DataVersionManager(
    base_data_dir="data",
    base_index_dir="artifacts",
    storage_type="hybrid",
    gcs_bucket="your-data-bucket",
    gcs_prefix="ragchain-data",
    project_id="your-project-id"
)

# 2. อัปโหลดข้อมูลที่มีอยู่
versions = dvm.list_available_versions()
for version in versions:
    data_path = dvm.get_data_version_path(version)
    if isinstance(data_path, Path):  # local path
        files = list(data_path.glob("*.txt"))
        dvm.upload_to_gcs([str(f) for f in files], version)

# 3. เปลี่ยนเป็น GCS-only
dvm_gcs = DataVersionManager(
    storage_type="gcs",
    gcs_bucket="your-data-bucket",
    gcs_prefix="ragchain-data",
    project_id="your-project-id"
)
```

## ข้อสรุป

การใช้ GCS สำหรับ production จะช่วยให้ระบบมีความน่าเชื่อถือ ปลอดภัย และขยายตัวได้ดี ตาม best practices ที่แนะนำข้างต้นจะช่วยให้การใช้งานมีประสิทธิภาพและประหยัดค่าใช้จ่าย 