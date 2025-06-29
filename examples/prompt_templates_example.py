#!/usr/bin/env python3
"""
ตัวอย่างการใช้งาน Prompt Templates
แสดงวิธีการจัดการและใช้งาน prompt templates
"""

from src.prompts.prompt_manager import PromptManager


def main():
    """ตัวอย่างการใช้งาน Prompt Templates"""
    print("📝 ตัวอย่างการใช้งาน Prompt Templates")
    print("=" * 50)

    # 1. สร้าง PromptManager
    print("🔧 สร้าง Prompt Manager...")
    pm = PromptManager()
    print("✅ Prompt Manager พร้อมใช้งาน")

    # 2. ดู templates ที่มีอยู่
    print("\n📋 Templates ที่มีอยู่:")
    try:
        templates = pm.list_available_templates()
        if templates:
            for template_name, versions in templates.items():
                print(f"   📝 {template_name}")
                for version in versions:
                    print(f"      • {version}")
        else:
            print("   (ไม่พบ templates)")
    except Exception as e:
        print(f"❌ ไม่สามารถดู templates ได้: {e}")
        return

    # 3. โหลด template
    print("\n📖 โหลด template...")
    try:
        # โหลด sales support template
        template = pm.get_template("sales_support", "v1")
        print("✅ โหลด sales_support template สำเร็จ")

        # แสดงส่วนหัวของ template
        lines = template.split("\n")
        print("📄 ตัวอย่าง template (10 บรรทัดแรก):")
        for i, line in enumerate(lines[:10], 1):
            print(f"   {i:2d}. {line}")
        if len(lines) > 10:
            print(f"   ... (อีก {len(lines) - 10} บรรทัด)")

    except Exception as e:
        print(f"❌ ไม่สามารถโหลด template ได้: {e}")
        return

    # 4. ใช้งาน template พร้อมตัวแปร
    print("\n🔧 ใช้งาน template พร้อมตัวแปร...")

    # ตัวอย่างข้อมูล
    sample_context = """
คอร์สการลงทุนของ Investic:

1. คอร์สพื้นฐาน (2,990 บาท)
   - เรียนรู้พื้นฐานการลงทุน
   - กลยุทธ์การลงทุนเบื้องต้น
   - เวลาเรียน 20 ชั่วโมง

2. คอร์สขั้นสูง (5,990 บาท)  
   - การวิเคราะห์หุ้นเชิงลึก
   - การจัดการพอร์ตการลงทุน
   - เวลาเรียน 40 ชั่วโมง

โปรโมชั่นพิเศษ:
- ลด 20% สำหรับสมาชิกใหม่
- ลด 30% เมื่อซื้อ 2 คอร์สขึ้นไป
    """.strip()

    sample_questions = [
        "มีคอร์สอะไรบ้าง?",
        "ราคาเท่าไหร่?",
        "มีส่วนลดไหม?",
        "คอร์สพื้นฐานเรียนอะไรบ้าง?",
    ]

    for question in sample_questions:
        print(f"\n❓ คำถาม: {question}")
        try:
            # ใช้ template พร้อมตัวแปร
            formatted_prompt = pm.format_template(
                "sales_support", "v1", context=sample_context, question=question
            )

            print("✅ สร้าง prompt สำเร็จ")
            print("📝 Prompt ที่สร้างขึ้น:")

            # แสดงเฉพาะส่วนท้ายของ prompt (ส่วนที่มีคำถาม)
            lines = formatted_prompt.split("\n")
            context_start = -1
            question_start = -1

            for i, line in enumerate(lines):
                if "KNOWLEDGE BASE" in line or "Context" in line:
                    context_start = i
                elif "CUSTOMER QUESTION" in line or "Question" in line:
                    question_start = i

            if context_start > 0:
                print("   ...")
                for line in lines[context_start : context_start + 3]:
                    print(f"   {line}")
                print("   [context ที่ใส่เข้าไป]")

            if question_start > 0:
                for line in lines[question_start : question_start + 3]:
                    print(f"   {line}")
                print("   [คำถามที่ใส่เข้าไป]")

        except Exception as e:
            print(f"❌ ไม่สามารถใช้ template ได้: {e}")

        print("-" * 30)

    # 5. ตัวอย่างการสร้าง template ใหม่
    print("\n📝 ตัวอย่างการสร้าง Template ใหม่:")
    print("💡 หากต้องการสร้าง template ใหม่ ให้สร้างไฟล์ YAML ใน src/prompts/templates/")

    example_template = """
# ตัวอย่าง: simple_qa_v1.yaml
template: |
  คุณเป็นผู้ช่วยที่เป็นมิตรและช่วยเหลือ
  
  ใช้ข้อมูลต่อไปนี้เพื่อตอบคำถาม:
  {context}
  
  คำถาม: {question}
  
  คำตอบ:

metadata:
  description: "Template แบบง่ายสำหรับ Q&A"
  author: "Your Name"
  created_date: "2024-01-15"
    """.strip()

    print("📄 ตัวอย่าง template ใหม่:")
    for line in example_template.split("\n"):
        print(f"   {line}")

    print("\n🎯 ขั้นตอนการสร้าง template ใหม่:")
    print("   1. สร้างไฟล์ .yaml ใน src/prompts/templates/")
    print("   2. ตั้งชื่อตามรูปแบบ: {ชื่อ}_{เวอร์ชัน}.yaml")
    print("   3. เพิ่ม template และ metadata")
    print("   4. อัพเดท configs/model_config.yaml")
    print("   5. ทดสอบการใช้งาน")

    print("\n🎉 ตัวอย่างการใช้งาน Prompt Templates เสร็จสมบูรณ์!")
    print("💡 ตอนนี้คุณสามารถจัดการ prompt templates ได้แล้ว")


if __name__ == "__main__":
    main()
