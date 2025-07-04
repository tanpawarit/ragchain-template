#!/usr/bin/env python3
"""
ตัวอย่างการใช้งาน RAG พื้นฐาน
การสร้างแชทบอทขายของแบบง่ายๆ
"""

from src.components.ragchain_runner import RAGChainRunner
from src.utils.config.app_config import AppConfig
from src.utils.pipeline.vectorstore_manager import load_vectorstore


def main():
    """ตัวอย่างการใช้งาน RAG แบบพื้นฐาน"""
    print("🤖 ตัวอย่างการใช้งาน RAG Chatbot")
    print("=" * 50)

    # 1. โหลดการตั้งค่า
    print("📋 กำลังโหลดการตั้งค่า...")
    cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")
    print(f"✅ ใช้โมเดล: {cfg.llm_model_name}")
    print(f"✅ ใช้ embedding: {cfg.embedding_model_name}")

    # 2. โหลด vectorstore
    print("\n📚 กำลังโหลดฐานข้อมูล...")
    vectorstore = load_vectorstore(cfg)
    print("✅ โหลดฐานข้อมูลสำเร็จ")

    # 3. สร้าง RAG runner
    print("\n🔧 กำลังสร้างระบบ RAG...")
    rag = RAGChainRunner(cfg, vectorstore=vectorstore)
    print("✅ ระบบ RAG พร้อมใช้งาน")

    # 4. ทดสอบคำถาม
    print("\n💬 ทดสอบการตอบคำถาม")
    print("-" * 30)

    # ตัวอย่างคำถามสำหรับแชทบอทขายของ
    test_questions = ["มีคอร์สอะไรบ้าง?", "ราคาเท่าไหร่?", "มีโปรโมชั่นไหม?", "จะสมัครยังไง?"]

    for question in test_questions:
        print(f"\n❓ คำถาม: {question}")
        try:
            answer = rag.answer(question)
            print(f"🤖 ตอบ: {answer}")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")
        print("-" * 30)

    # 5. โหมดสนทนา
    print("\n🎯 เข้าสู่โหมดสนทนา (พิมพ์ 'quit' เพื่อออก)")
    while True:
        try:
            question = input("\n👤 คุณ: ").strip()
            if question.lower() in ["quit", "exit", "ออก"]:
                print("👋 ขอบคุณที่ใช้บริการ!")
                break

            if question:
                answer = rag.answer(question)
                print(f"🤖 เรา: {answer}")
        except KeyboardInterrupt:
            print("\n👋 ขอบคุณที่ใช้บริการ!")
            break
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")


if __name__ == "__main__":
    main()
