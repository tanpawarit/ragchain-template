# ragchain-chatbot (Typhoon)

RAG Chain Chatbot Project

เส้นทาง Online-Serving (ตอบผู้ใช้แบบ real-time)
• เรียกเพียง RAGChainRunner.answer()
• ใช้ FAISS index ที่สร้างไว้แล้ว (โหลดครั้งเดียวตอน start-up)
• ไม่รัน DeepEval เพราะการวัดผลใช้เวลาหลักวินาทีและต้องมี ground-truth → ทำแบบ batch/offline แทน
• MLflow logging เฉพาะ metadata เร็ว ๆ เช่น question, latency, model-version แล้วส่งต่อไป async/queue เพื่อไม่บล็อกคำตอบ
เส้นทาง Offline (Batch / Ops)
• Job Ingestion – รัน DataIngestionPipeline.run_pipeline() เป็น periodic task (เช่น Airflow, GitHub Actions) เพื่อ:
– ดึงไฟล์ใหม่ → สร้าง/อัปเดต FAISS → อัปโหลด index ไปที่ S3 / GCS
– log params+metrics+artifact ไปยัง MLflow Tracking Server ที่รันแยกเครื่อง
• Job Evaluation – รัน EvaluationPipeline.run() ทุกคืนหรือทุกครั้งที่เปลี่ยนเวอร์ชัน index / LLM
– โหลด vectorstore ล่าสุด → ยิงคำถามชุดมาตรฐาน → บันทึก score ด้วย MLflow
– ค่า metric เหล่านี้ใช้ทำแดชบอร์ดคุณภาพ, alert ถ้าประสิทธิภาพตก
การจัดวางสถาปัตยกรรม
• MLflow Tracking Server อยู่หลัง DB (e.g. Postgres) + object-storage สำหรับ artifacts
• API/chatbot container ​mount หรือโหลด index จาก object-storage ระหว่าง start-up
• ใช้ environment variables (หรือ Vault) ใส่ API keys แทนที่ไฟล์ .env ใน code
• มี CI/CD pipeline ที่รัน unit-tests, lint, ติด label “model-version”, push Docker image, deploy ผ่าน Kubernetes / ECS

# nightly DAG
with MLflowTracker(experiment_name="rag_prod") as t:
    # 1) อัปเดต index
    ingestion = DataIngestionPipeline(cfg, mlflow_tracker=t)
    vs = ingestion.get_or_create_vectorstore()

    # 2) วัดผล
    evaluator = EvaluationPipeline(cfg, vectorstore=vs, mlflow_tracker=t)
    evaluator.run(questions=test_qs, ground_truth_docs=gt_docs)

# image build & deploy happens separately
– หลัง job เสร็จ MLflow UI/Databricks ช่วยดู timeline ของ metrics, artifacts
– Container API จะ wget index ล่าสุดจาก S3 ณ start-up (หรือ mount ผ่าน volume) แล้วพร้อมตอบคำถาม

สรุป : ใน production จะ “แยก” เส้นทาง serving และ evaluation ออกจากกัน — เส้นทางตอบผู้ใช้ต้องเร็ว, เส้นทางวัดผล/สร้าง index ทำเป็นงาน batch และใช้ MLflow เพื่อเก็บร่องรอยทั้งหมดให้ตรวจสอบย้อนหลังได้ง่าย.