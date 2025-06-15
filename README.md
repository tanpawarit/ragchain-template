# ragchain-chatbot (Typhoon)

RAG Chain Chatbot Project

## Project Structure

```
typhoon/
├── .venv/
├── artifacts/
│   └── faiss_product_index/
│       ├── index.faiss
│       └── index.pkl
├── configs/
│   └── config.yaml
├── data/
│   └── raw/
│       └── product_data.txt
├── notebooks/
│   ├── extraction.ipynb
│   └── test.ipynb
├── src/
│   └── typhoon/  #<-- ชื่อโปรเจกต์เป็น main package
│       ├── __init__.py
│       ├── components/
│       │   ├── __init__.py
│       │   ├── data_ingestion.py
│       │   ├── indexing.py
│       │   └── retrieval.py
│       ├── utils/
│       │   ├── __init__.py
│       │   └── common.py      # (รวม logger และ function ช่วยเหลืออื่นๆ)
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── training_pipeline.py  # Pipeline สำหรับสร้าง index
│       │   └── prediction_pipeline.py# Pipeline สำหรับการ query
│       ├── config/
│       │   ├── __init__.py
│       │   └── configuration.py # (ย้าย ConfigManager มาไว้ที่นี่)
│       └── constants/
│           └── __init__.py
├── .gitignore
├── .python-version
├── main.py                # (เปลี่ยนชื่อจาก hello.py เป็นตัวรันหลัก)
├── pyproject.toml
├── README.md
└── uv.lock
```
