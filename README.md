# ragchain-chatbot (Typhoon)

## Workflow End-to-End 5 เฟส

#### Problem Definition & Baseline
- เลือกโมเดลพื้นฐาน (Base Model): นำโมเดลสำเร็จรูปที่เก่งมากๆ มาใช้ก่อนเลย เช่น GPT-4o, Typhoon, Llama 3
- ทดสอบด้วย Prompt Engineering: ลองใช้ Zero-shot (สั่งงานตรงๆ) หรือ Few-shot (ยกตัวอย่างใน prompt) เพื่อทดสอบกับชุดข้อมูลวัดผล
- ประเมินผล: นี่คือการ eval ครั้งแรกของคุณ เพื่อดูว่าโมเดลพื้นฐานทำได้ดีแค่ไหนโดยไม่ต้องทำอะไรเพิ่มเลย
- MLflow + DeepEval Connection:
    - สร้าง Experiment ใหม่ เช่น faq-chatbot-project
    - Run แรกคือ "Baseline Run"
    - log_param: model_name="gpt-4o", method="few-shot"
    - mlflow.evaluate: ใช้กับชุดข้อมูลทดสอบเพื่อเก็บคะแนน Baseline นี้ไว้เป็น "มาตรฐานขั้นต่ำ" ที่ต้องเอาชนะให้ได้
    
#### Data Preparation
- สำหรับ Fine-tuning:
    - รวบรวมและสร้างชุดข้อมูลสำหรับการ Fine-tune (Instruction/Response pairs) 
    - ข้อมูลจัดรูปแบบเป็น JSONL
- สำหรับ RAG (Retrieval-Augmented Generation):
    - ทำความสะอาด, ตัดแบ่งเอกสาร (Chunking), แล้วนำไปแปลงเป็น Vector เพื่อเก็บใน Vector Database
- MLflow Connection:
    - ใช้ mlflow.log_artifact เพื่อบันทึกเวอร์ชันของชุดข้อมูลที่ผ่านการประมวลผลแล้ว เพื่อให้รู้ว่า Run ไหนใช้ข้อมูลเวอร์ชันใด

#### The Development Loop
- ลองยังไม่ Fine-tune (เน้น Prompt Engineering และ RAG)
    - ปรับปรุง Prompt: Prompt Engineering แบบต่างๆ
    - สร้าง/ปรับปรุงระบบ RAG: เปลี่ยน Embedding Model, ปรับขนาด Chunk, เปลี่ยนวิธี Retriever (search_type, k_value or rerank)
    - เปรียบเทียบผลลัพธ์กับ Baseline  
- MLflow Connection:
    - ทุกการเปลี่ยนแปลงคือ Run ใหม่
    - ใช้ log_param บันทึก Prompt Template, log_dict บันทึก Config ของ RAG
    - ใช้ mlflow + deepeval เพื่อเปรียบเทียบผลลัพธ์ของแต่ละ Run ในหน้า UI อย่างชัดเจน

#### Red Teaming (Advanced Evaluation)
- Safety & Security:
    - Apply and test with guardrails
    - Build based on OWASP Top 10: LLM & Generative AI Security Risks
- Robustness: ทดสอบกับ Input ที่มีคำผิด, ใช้ภาษาแปลกๆ, หรือเป็นกรณีที่คาดไม่ถึง (Edge Cases)
- MLflow Connection: 
    - สร้าง Experiment ใหม่สำหรับ "Safety & Robustness Testing" โดยเฉพาะ และใช้ mlflow + deepeval 

#### Deployment & Monitoring
- Infrastructure: cloud run service, posgres เก็บ log, หากใช้ model finetune ต้องมี gcs bucket เก็บ model
- MLflow Connection:
    - ใช้ MLflow Model Registry ในการจัดการ Lifecycle ของโมเดล (Staging -> Production)
    - Production service จะโหลดโมเดลจาก Model Registry (models:/my-chatbot/Production)
สรุป : ใน production จะ “แยก” เส้นทาง serving และ evaluation ออกจากกัน — เส้นทางตอบผู้ใช้ต้องเร็ว, เส้นทางวัดผล/สร้าง index ทำเป็นงาน batch และใช้ MLflow เพื่อเก็บร่องรอยทั้งหมดให้ตรวจสอบย้อนหลังได้ง่าย.