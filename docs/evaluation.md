# การประเมินระบบ RAG

## ภาพรวม

ระบบ RAG-Chain มีเครื่องมือประเมินครบชุด ประกอบด้วย:

1. **Retriever Evaluation** - ประเมินการดึงข้อมูล
2. **Generator Evaluation** - ประเมินการสร้างคำตอบ  
3. **End-to-End Evaluation** - ประเมินระบบรวม

## โครงสร้าง

```
evaluation/
├── retriever_evaluation.py    # ประเมิน retriever
├── generator_evaluation.py    # ประเมิน generator
├── e2e_evaluation.py          # ประเมินแบบ end-to-end
├── metrics.py                 # เมตริกส์ต่างๆ
└── test_data/                 # ข้อมูลทดสอบ
    ├── golden_dataset_v1.json
    └── golden_dataset_v2.json
```

## การใช้งาน

### 1. ประเมิน Retriever

```python
from evaluation.retriever_evaluation import evaluate_retriever

results = evaluate_retriever(
    vectorstore=vectorstore,
    test_data=test_data,
    k_values=[3, 5, 10]
)
```

### 2. ประเมิน Generator

```python
from evaluation.generator_evaluation import evaluate_generator

results = evaluate_generator(
    rag_system=rag_system,
    test_data=test_data,
    metrics=["relevancy", "faithfulness"]
)
```

### 3. ประเมินแบบ End-to-End

```python
from evaluation.e2e_evaluation import evaluate_e2e_system

results = evaluate_e2e_system(
    test_data=test_data,
    rag_system=rag_system,
    evaluation_model="gpt-4o"
)
```

## เมตริกส์หลัก

### Retriever
- **Precision@K**: ความแม่นยำของเอกสารที่ดึงมา
- **Recall@K**: ความครอบคลุมของเอกสารที่เกี่ยวข้อง
- **MRR**: Mean Reciprocal Rank

### Generator
- **Relevancy**: ความเกี่ยวข้องของคำตอบ
- **Faithfulness**: ความถูกต้องตามบริบท
- **Answer Completeness**: ความสมบูรณ์ของคำตอบ

### End-to-End
- **Overall Accuracy**: ความถูกต้องโดยรวม
- **Response Time**: เวลาตอบสนอง
- **Cost per Query**: ต้นทุนต่อคำถาม

## การรันการประเมิน

```bash
# ประเมิน retriever
python evaluation/retriever_evaluation.py

# ประเมิน generator
python evaluation/generator_evaluation.py

# ประเมินแบบ end-to-end
python evaluation/e2e_evaluation.py
```

## ดูผลลัพธ์ใน MLflow

```bash
# เปิด MLflow UI
mlflow ui --port 5000

# เข้าดูที่ http://localhost:5000
```

## การเตรียมข้อมูลทดสอบ

สร้างไฟล์ JSON ตามรูปแบบ:

```json
[
  {
    "question": "คำถามทดสอบ",
    "expected_answer": "คำตอบที่คาดหวัง",
    "context": "บริบทที่เกี่ยวข้อง"
  }
]
```

## Tips สำหรับการประเมิน

1. **ใช้ข้อมูลทดสอบที่หลากหลาย** - ครอบคลุมกรณีต่างๆ
2. **ประเมินเป็นระยะ** - ติดตามการเปลี่ยนแปลง
3. **ใช้หลายเมตริกส์** - ไม่พึ่งแค่ตัวเดียว
4. **ทดสอบกับผู้ใช้จริง** - User acceptance testing 