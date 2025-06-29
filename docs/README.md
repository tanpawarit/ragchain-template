# RAG-Chain Chatbot Documentation

คู่มือการใช้งาน RAG-Chain Chatbot ระบบแชทบอทที่ใช้ AI สำหรับงานขายและซัพพอร์ต

## 📚 คู่มือหลัก

### เริ่มต้นใช้งาน
- **[Quick Start](quickstart.md)** - เริ่มใช้งานใน 5 นาที
- **[GCS Setup](gcs_setup.md)** - ตั้งค่า Google Cloud Storage

### คู่มือการใช้งาน
- **[การประเมินระบบ](evaluation.md)** - วิธีประเมิน RAG system
- **[การจัดการ Prompt](prompts.md)** - จัดการเทมเพลต prompt
- **[แก้ปัญหา](troubleshooting.md)** - แก้ปัญหาที่พบบ่อย

## 🚀 เริ่มต้นด่วน

```bash
# ติดตั้ง
uv sync

# ตั้งค่า
cp config.example.yaml config.yaml
# แก้ไข config.yaml ใส่ OpenAI API key

# รัน
python scripts/create_data_version.py --files data/raw/*.txt --inc minor
python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking
python -m src.components.ragchain
```

## 🏗️ โครงสร้างโปรเจกต์

```
ragchain-chatbot/
├── src/                    # โค้ดหลัก
│   ├── components/         # RAG pipeline
│   ├── prompts/           # จัดการ prompt
│   └── utils/             # เครื่องมือช่วย
├── evaluation/            # ประเมินระบบ
├── scripts/              # สคริปต์ช่วย
├── configs/              # ไฟล์ config
└── docs/                 # คู่มือทั้งหมด
```

## 💡 Tips

- **ใหม่กับ RAG?** เริ่มที่ [Quick Start](quickstart.md)
- **ใช้ Production?** ดู [GCS Setup](gcs_setup.md)
- **มีปัญหา?** ไปที่ [Troubleshooting](troubleshooting.md)
- **ต้องการประเมิน?** ดู [Evaluation](evaluation.md)

## 🔗 ลิงก์ที่เป็นประโยชน์

- [GitHub Repository](https://github.com/your-org/ragchain-chatbot)
- [Issues & Bug Reports](https://github.com/your-org/ragchain-chatbot/issues) 