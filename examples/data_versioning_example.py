#!/usr/bin/env python3
"""
ตัวอย่างการจัดการเวอร์ชันข้อมูล
แสดงวิธีการสร้างและจัดการเวอร์ชันข้อมูลต่างๆ
"""

import os

from src.utils.pipeline.data_version_manager import DataVersionManager


def main():
    """ตัวอย่างการจัดการเวอร์ชันข้อมูล"""
    print("📦 ตัวอย่างการจัดการเวอร์ชันข้อมูล")
    print("=" * 50)

    # 1. สร้าง DataVersionManager
    print("🔧 สร้าง Data Version Manager...")
    dvm = DataVersionManager(
        base_data_dir="data", base_index_dir="artifacts", storage_type="local"
    )
    print("✅ Data Version Manager พร้อมใช้งาน")

    # 2. ดูเวอร์ชันที่มีอยู่
    print("\n📋 เวอร์ชันข้อมูลที่มีอยู่:")
    try:
        versions = dvm.list_available_versions()
        if versions:
            for version in versions:
                print(f"   • {version}")
        else:
            print("   (ยังไม่มีเวอร์ชันข้อมูล)")
    except Exception as e:
        print(f"❌ ไม่สามารถดูเวอร์ชันได้: {e}")
        return

    # 3. ตรวจสอบไฟล์ข้อมูลต้นฉบับ
    print("\n📁 ตรวจสอบไฟล์ข้อมูลต้นฉบับ...")
    source_files = []
    data_folder = "data/raw"

    # ไฟล์ตัวอย่าง
    example_files = ["workshop.txt", "rerun.txt", "overall.txt"]

    for filename in example_files:
        file_path = os.path.join(data_folder, filename)
        if os.path.exists(file_path):
            source_files.append(file_path)
            file_size = os.path.getsize(file_path)
            print(f"✅ {filename} ({file_size:,} bytes)")
        else:
            print(f"❌ {filename} (ไม่พบไฟล์)")

    if not source_files:
        print("\n⚠️  ไม่พบไฟล์ข้อมูลต้นฉบับ")
        print("💡 กรุณาเพิ่มไฟล์ .txt ในโฟลเดอร์ data/raw/")

        # สร้างไฟล์ตัวอย่าง
        print("\n📝 สร้างไฟล์ตัวอย่าง...")
        os.makedirs(data_folder, exist_ok=True)

        sample_content = """
คอร์สเรียนการลงทุน - Investic

คอร์สของเรามีหลายระดับ:
1. คอร์สพื้นฐาน - ราคา 2,990 บาท
2. คอร์สขั้นสูง - ราคา 5,990 บาท  
3. คอร์ส VIP - ราคา 9,990 บาท

โปรโมชั่นพิเศษ:
- ลด 20% สำหรับสมาชิกใหม่
- ลด 30% เมื่อซื้อ 2 คอร์สขึ้นไป

วิธีสมัคร:
1. เข้าเว็บไซต์ www.investic.com
2. เลือกคอร์สที่ต้องการ
3. ชำระเงินผ่าน QR Code
4. เริ่มเรียนได้ทันที
        """.strip()

        sample_file = os.path.join(data_folder, "sample_course.txt")
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write(sample_content)

        source_files = [sample_file]
        print(f"✅ สร้างไฟล์ตัวอย่าง: {sample_file}")

    # 4. สร้างเวอร์ชันใหม่
    print(f"\n🆕 สร้างเวอร์ชันใหม่จาก {len(source_files)} ไฟล์...")
    try:
        new_version = dvm.create_new_version(
            source_files=source_files,
            increment_type="minor",  # เพิ่ม minor version
        )
        print(f"✅ สร้างเวอร์ชันใหม่: {new_version}")

    except Exception as e:
        print(f"❌ ไม่สามารถสร้างเวอร์ชันใหม่ได้: {e}")
        return

    # 5. ดูเส้นทางข้อมูลของเวอร์ชันต่างๆ
    print("\n📂 เส้นทางข้อมูลของแต่ละเวอร์ชัน:")
    versions = dvm.list_available_versions()

    for version in versions[-3:]:  # แสดง 3 เวอร์ชันล่าสุด
        try:
            data_path = dvm.get_data_version_path(version)
            index_path = dvm.get_index_path_for_version(version)
            print(f"   📦 {version}:")
            print(f"      ข้อมูล: {data_path}")
            print(f"      Index: {index_path}")
        except Exception as e:
            print(f"   ❌ {version}: {e}")

    # 6. ตัวอย่างการสร้าง lineage record
    print("\n📊 สร้างบันทึก Data Lineage...")
    try:
        index_path = str(dvm.get_index_path_for_version(new_version))

        lineage_record = dvm.create_lineage_record(
            index_path=index_path,
            data_version=new_version,
            files_used=source_files,
            parameters={
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "embedding_model": "text-embedding-3-small",
                "use_semantic_chunking": True,
            },
        )

        print("✅ สร้างบันทึก lineage สำเร็จ")
        print(f"   📝 Index: {lineage_record['index_path']}")
        print(f"   📦 Data Version: {lineage_record['data_version']}")
        print(f"   📁 Files: {len(lineage_record['files_used'])} ไฟล์")

    except Exception as e:
        print(f"❌ ไม่สามารถสร้าง lineage record ได้: {e}")

    # 7. ดูบันทึก lineage
    print("\n🔍 ดูบันทึก Data Lineage...")
    try:
        lineage = dvm.get_lineage_for_index(str(index_path))
        if lineage:
            print("✅ พบบันทึก lineage:")
            print(f"   📅 วันที่สร้าง: {lineage['created_at']}")
            print(f"   🔧 Parameters: {lineage['parameters']}")
        else:
            print("   (ไม่พบบันทึก lineage)")

    except Exception as e:
        print(f"❌ ไม่สามารถดู lineage ได้: {e}")

    print("\n🎉 ตัวอย่างการจัดการเวอร์ชันข้อมูลเสร็จสมบูรณ์!")
    print("💡 ตอนนี้คุณสามารถใช้เวอร์ชันข้อมูลต่างๆ ได้แล้ว")


if __name__ == "__main__":
    main()
