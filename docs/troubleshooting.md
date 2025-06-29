# การแก้ปัญหา

## ปัญหาที่พบบ่อย

### 1. API Key Error

**อาการ**: `openai.AuthenticationError`

**แก้ไข**:
```bash
# ตรวจสอบ API key ใน config.yaml
cat config.yaml

# ตรวจสอบ credits ใน OpenAI dashboard
# https://platform.openai.com/usage
```

### 2. Memory Error

**อาการ**: `MemoryError` หรือ `OOM killed`

**แก้ไข**:
```yaml
# ลด chunk_size ใน config
chunk_size: 500  # จาก 1000
chunk_overlap: 100  # จาก 200

# หรือใช้ model เล็กกว่า
models:
  embedding: "text-embedding-3-small"
  llm: "gpt-3.5-turbo"
```

### 3. Import Error

**อาการ**: `ModuleNotFoundError`

**แก้ไข**:
```bash
# ติดตั้ง dependencies ใหม่
uv sync

# หรือใช้ pip
pip install -r requirements.txt
```

### 4. FAISS Index Error

**อาการ**: `RuntimeError: Error in faiss`

**แก้ไข**:
```bash
# สร้าง index ใหม่
python scripts/build_faiss_index.py --data-version latest

# ตรวจสอบว่าไฟล์ index มีอยู่
ls -la artifacts/
```

### 5. Data Version Error

**อาการ**: `FileNotFoundError: Data version not found`

**แก้ไข**:
```bash
# ตรวจสอบเวอร์ชันที่มี
python -c "from src.utils.pipeline.data_version_manager import DataVersionManager; print(DataVersionManager().list_available_versions())"

# สร้างเวอร์ชันใหม่
python scripts/create_data_version.py --files data/raw/*.txt --inc minor
```

### 6. MLflow Connection Error

**อาการ**: `ConnectionError: MLflow tracking server`

**แก้ไข**:
```bash
# เริ่ม MLflow server
mlflow ui --port 5000 &

# หรือใช้ local file store
# แก้ไข config.yaml
mlflow:
  tracking_uri: "file:./mlruns"
```

### 7. Thai Language Issues

**อาการ**: ตัวอักษรไทยแสดงผิด

**แก้ไข**:
```python
# ตั้งค่า encoding
import locale
locale.setlocale(locale.LC_ALL, 'th_TH.UTF-8')

# ใช้ semantic chunking สำหรับภาษาไทย
python scripts/build_faiss_index.py --use-semantic-chunking
```

## การ Debug

### 1. เปิด Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. ตรวจสอบ Config

```python
from src.utils.config.app_config import AppConfig

cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")
print(cfg)
```

### 3. ทดสอบ Components แยก

```python
# ทดสอบ embedding
from src.utils.config.app_config import AppConfig
cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")

from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model=cfg.embedding_model_name)
result = embeddings.embed_query("test")
print(f"Embedding dimension: {len(result)}")

# ทดสอบ LLM
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model=cfg.llm_model_name)
result = llm.invoke("Hello")
print(result.content)
```

## Performance Issues

### 1. Slow Response

**สาเหตุ**:
- Index ใหญ่เกินไป
- k_value สูงเกินไป
- Network latency

**แก้ไข**:
```yaml
# ลด k_value
retriever:
  k_value: 3  # จาก 5

# ใช้ model เร็วกว่า
models:
  llm: "gpt-3.5-turbo"  # แทน gpt-4
```

### 2. High API Costs

**แก้ไข**:
```yaml
# ใช้ model ถูกกว่า
models:
  embedding: "text-embedding-3-small"
  llm: "gpt-3.5-turbo"

# ลด chunk size
chunk_size: 800
```

## การขอความช่วยเหลือ

1. **ตรวจสอบ logs** - ดู error message ทั้งหมด
2. **ลอง minimal example** - ทดสอบแค่ส่วนที่มีปัญหา
3. **เช็ค version** - ตรวจสอบเวอร์ชัน dependencies
4. **สร้าง issue** - ใน GitHub repository พร้อม error logs 