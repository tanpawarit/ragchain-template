# การจัดการ Prompt

## ภาพรวม

ระบบ Prompt Management ช่วยจัดการเทมเพลต prompt แบบมีเวอร์ชัน

## โครงสร้าง

```
src/prompts/
├── prompt_manager.py          # ตัวจัดการ prompt
└── templates/                 # เทมเพลต prompt
    └── sales_support_v1.yaml  # ตัวอย่าง
```

## การใช้งาน

### 1. โหลด Prompt

```python
from src.prompts import PromptManager

pm = PromptManager()

# โหลดเวอร์ชันล่าสุด
template = pm.get_template("sales_support")

# โหลดเวอร์ชันเฉพาะ
template = pm.get_template("sales_support", "v1")
```

### 2. ใช้ Prompt

```python
# Format พร้อมตัวแปร
result = pm.format_template(
    "sales_support", "v1",
    context="บริบทจากเอกสาร",
    question="คำถามของผู้ใช้"
)
```

### 3. สร้าง Prompt ใหม่

สร้างไฟล์ `sales_support_v2.yaml`:

```yaml
template: |
  ### บทบาท ###
  คุณเป็นผู้ช่วยขายที่เชี่ยวชาญ
  
  ### คำแนะนำ ###
  - ตอบเป็นภาษาไทย
  - ใช้ข้อมูลจากบริบท
  - สุภาพและเป็นมิตร
  
  ### บริบท ###
  {context}
  
  ### คำถาม ###
  {question}
  
  ### คำตอบ ###

metadata:
  description: "เทมเพลตสำหรับงานขาย"
  author: "ชื่อผู้เขียน"
  created_date: "2024-01-15"
```

### 4. ตั้งค่าใน Config

แก้ไข `configs/model_config.yaml`:

```yaml
prompt_config:
  template_name: "sales_support"
  version: "v2"  # ใช้เวอร์ชันใหม่
```

## Best Practices

1. **ตั้งชื่อเวอร์ชันชัดเจน** - v1, v2, v3
2. **เก็บเวอร์ชันเก่า** - สำหรับ rollback
3. **ทดสอบก่อนใช้** - ทำ A/B testing
4. **เขียน metadata** - อธิบายการเปลี่ยนแปลง

## ตัวอย่าง Template

### แบบพื้นฐาน
```yaml
template: |
  ตอบคำถามต่อไปนี้โดยใช้บริบทที่ให้มา
  
  บริบท: {context}
  คำถาม: {question}
  
  คำตอบ:
```

### แบบภาษาไทย
```yaml
template: |
  ### บทบาท ###
  คุณเป็นผู้ช่วยที่เชี่ยวชาญ
  
  ### คำแนะนำ ###
  - ตอบเป็นภาษาไทย
  - ใช้ข้อมูลจากบริบท
  - หากไม่ทราบ ให้บอกตรงๆ
  
  ### บริบท ###
  {context}
  
  ### คำถาม ###
  {question}
  
  ### คำตอบ ###
```

## การแก้ปัญหา

**ไม่พบ Template**
```python
# ตรวจสอบว่ามี template หรือไม่
if pm.template_exists("template_name", "v1"):
    print("มี template")
else:
    print("ไม่มี template")
```

**Template ผิดรูปแบบ**
- ตรวจสอบ YAML syntax
- ตรวจสอบ {variable} placeholders
- ตรวจสอบ metadata section 