#!/usr/bin/env python3
"""
แชทบอทขายของแบบง่าย
พร้อมการติดตาม conversation และ user experience
"""

import time
from typing import Dict, List

from src.components.ragchain_runner import RAGChainRunner
from src.utils.config.app_config import AppConfig
from src.utils.pipeline.vectorstore_manager import load_vectorstore


class SimpleSalesChatbot:
    """แชทบอทขายของแบบง่าย"""

    def __init__(self):
        """เริ่มต้นแชทบอท"""
        print("🚀 กำลังเริ่มต้นแชทบอท...")

        # โหลดการตั้งค่า
        self.cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")

        # โหลดระบบ RAG
        vectorstore = load_vectorstore(self.cfg)
        self.rag = RAGChainRunner(self.cfg, vectorstore=vectorstore)

        # ข้อมูลสำหรับติดตาม
        self.conversation_history: List[Dict[str, str]] = []
        self.user_id = f"user_{int(time.time())}"

        print("✅ แชทบอทพร้อมใช้งาน!")

    def greet_user(self):
        """ทักทายผู้ใช้"""
        greeting = """
🎉 สวัสดีครับ! ยินดีต้อนรับสู่ Investic!

ผมคือ AI Assistant ที่จะช่วยให้คุณได้รู้จักคอร์สและบริการของเรา
คุณสามารถถามอะไรก็ได้เกี่ยวกับ:
• คอร์สที่มีอยู่
• ราคาและโปรโมชั่น  
• วิธีการสมัคร
• ข้อมูลเพิ่มเติม

💬 ลองถามผมดูสิครับ!
        """
        print(greeting)

    def get_quick_suggestions(self) -> List[str]:
        """คำแนะนำคำถามด่วน"""
        return [
            "มีคอร์สอะไรบ้าง?",
            "ราคาเท่าไหร่?",
            "มีส่วนลดไหม?",
            "จะสมัครยังไง?",
            "เรียนออนไลน์ได้ไหม?",
        ]

    def show_suggestions(self):
        """แสดงคำแนะนำคำถาม"""
        suggestions = self.get_quick_suggestions()
        print("\n💡 คำถามยอดนิยม:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        print("   หรือพิมพ์คำถามของคุณเองได้เลย!")

    def save_conversation(self, question: str, answer: str):
        """บันทึกการสนทนา"""
        self.conversation_history.append(
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "question": question,
                "answer": answer[:100] + "..." if len(answer) > 100 else answer,
            }
        )

    def get_answer(self, question: str) -> str:
        """ได้คำตอบจากระบบ RAG"""
        try:
            answer = self.rag.answer(question, user_id=self.user_id)
            self.save_conversation(question, answer)
            return answer
        except Exception as e:
            error_msg = f"ขออภัยครับ เกิดข้อผิดพลาด: {e}"
            self.save_conversation(question, error_msg)
            return error_msg

    def show_conversation_summary(self):
        """แสดงสรุปการสนทนา"""
        if not self.conversation_history:
            return

        print("\n📊 สรุปการสนทนา:")
        print(f"   จำนวนคำถาม: {len(self.conversation_history)}")
        print("   คำถามล่าสุด:")
        for conv in self.conversation_history[-3:]:  # แสดง 3 คำถามล่าสุด
            print(f"   • {conv['question']}")

    def run(self):
        """เริ่มการสนทนา"""
        self.greet_user()
        self.show_suggestions()

        print("\n" + "=" * 50)
        print("💬 เริ่มสนทนา (พิมพ์ 'quit' เพื่อออก)")
        print("=" * 50)

        while True:
            try:
                # รับคำถามจากผู้ใช้
                question = input("\n👤 คุณ: ").strip()

                # ตรวจสอบคำสั่งพิเศษ
                if question.lower() in ["quit", "exit", "ออก", "จบ"]:
                    break
                elif question.lower() in ["help", "ช่วย"]:
                    self.show_suggestions()
                    continue
                elif question.lower() in ["summary", "สรุป"]:
                    self.show_conversation_summary()
                    continue
                elif not question:
                    print("❓ กรุณาพิมพ์คำถามครับ")
                    continue

                # ตอบคำถาม
                print("🤖 เรา: ", end="", flush=True)
                answer = self.get_answer(question)
                print(answer)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาด: {e}")

        # จบการสนทนา
        self.show_conversation_summary()
        print("\n👋 ขอบคุณที่ใช้บริการ Investic!")
        print("🎯 หวังว่าจะได้เห็นคุณในคอร์สของเราเร็วๆ นี้!")


def main():
    """เริ่มต้นแชทบอท"""
    try:
        chatbot = SimpleSalesChatbot()
        chatbot.run()
    except Exception as e:
        print(f"❌ ไม่สามารถเริ่มแชทบอทได้: {e}")
        print("💡 ตรวจสอบการตั้งค่าและลองใหม่อีกครั้ง")


if __name__ == "__main__":
    main()
