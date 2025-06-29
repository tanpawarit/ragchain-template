#!/usr/bin/env python3
"""
ตัวอย่างการ Ingest ข้อมูล
แสดงวิธีการประมวลผลและสร้าง index จากเอกสาร
"""

import os

from src.components.ingestion import DataIngestionPipeline
from src.utils.config.app_config import AppConfig


def main():
    """ตัวอย่างการ ingest ข้อมูล"""
    print("📚 ตัวอย่างการ Ingest ข้อมูล")
    print("=" * 50)

    # 1. ตรวจสอบไฟล์ข้อมูล
    print("📋 ตรวจสอบไฟล์ข้อมูล...")

    cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")

    # ตรวจสอบว่ามีไฟล์ข้อมูลหรือไม่
    data_folder = cfg.data_folder
    missing_files = []

    for filename in cfg.file_names:
        file_path = os.path.join(data_folder, filename)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ {filename} ({file_size:,} bytes)")
        else:
            missing_files.append(filename)
            print(f"❌ {filename} (ไม่พบไฟล์)")

    if missing_files:
        print(f"\n⚠️  ไม่พบไฟล์: {', '.join(missing_files)}")
        print("💡 กรุณาเพิ่มไฟล์ข้อมูลในโฟลเดอร์ data/raw/")
        return

    # 2. สร้าง pipeline
    print("\n🔧 สร้าง Data Ingestion Pipeline...")
    pipeline = DataIngestionPipeline(cfg=cfg, data_version="latest")
    print("✅ Pipeline พร้อมใช้งาน")

    # 3. โหลดเอกสาร
    print("\n📖 กำลังโหลดเอกสาร...")
    try:
        documents = pipeline.load_documents()
        print(f"✅ โหลดเอกสารสำเร็จ: {len(documents)} เอกสาร")

        # แสดงข้อมูลเอกสาร
        total_chars = sum(len(doc.page_content) for doc in documents)
        print(f"📊 ข้อมูลทั้งหมด: {total_chars:,} ตัวอักษร")

    except Exception as e:
        print(f"❌ ไม่สามารถโหลดเอกสารได้: {e}")
        return

    # 4. แบ่งเอกสารเป็นชิ้นเล็ก (Chunking)
    print("\n✂️  กำลังแบ่งเอกสาร...")

    # ตัวอย่างการตั้งค่า chunking
    chunking_params = {
        "chunk_size": 1000,  # ขนาดแต่ละชิ้น
        "chunk_overlap": 200,  # ส่วนที่ซ้อนทับ
        "use_semantic_chunking": True,  # ใช้ semantic chunking
    }

    try:
        chunks = pipeline.chunk_documents(documents, **chunking_params)
        print(f"✅ แบ่งเอกสารสำเร็จ: {len(chunks)} ชิ้น")

        # แสดงตัวอย่างชิ้นแรก
        if chunks:
            first_chunk = chunks[0].page_content
            print(f"📝 ตัวอย่างชิ้นแรก ({len(first_chunk)} ตัวอักษร):")
            print(f"   {first_chunk[:200]}...")

    except Exception as e:
        print(f"❌ ไม่สามารถแบ่งเอกสารได้: {e}")
        return

    # 5. สร้าง FAISS index
    print("\n🔍 กำลังสร้าง FAISS index...")
    try:
        pipeline.create_and_save_vectorstore(chunks)
        print("✅ สร้าง FAISS index สำเร็จ")
        print(f"📁 บันทึกที่: {pipeline.faiss_index_path}")

    except Exception as e:
        print(f"❌ ไม่สามารถสร้าง index ได้: {e}")
        return

    # 6. ทดสอบการค้นหา
    print("\n🔍 ทดสอบการค้นหา...")
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
        from pydantic import SecretStr

        # โหลด index ที่สร้างขึ้น
        embeddings = OpenAIEmbeddings(
            model=cfg.embedding_model_name, api_key=SecretStr(cfg.openai_token)
        )
        vectorstore = FAISS.load_local(
            pipeline.faiss_index_path, embeddings, allow_dangerous_deserialization=True
        )

        # ทดสอบค้นหา
        test_query = "มีคอร์สอะไรบ้าง"
        results = vectorstore.similarity_search(test_query, k=3)

        print(f"🔍 ค้นหา: '{test_query}'")
        print(f"📊 พบ {len(results)} ผลลัพธ์:")

        for i, result in enumerate(results, 1):
            content = result.page_content[:150] + "..."
            print(f"   {i}. {content}")

    except Exception as e:
        print(f"❌ ไม่สามารถทดสอบการค้นหาได้: {e}")

    print("\n🎉 การ ingest ข้อมูลเสร็จสมบูรณ์!")
    print("💡 ตอนนี้คุณสามารถใช้ระบบ RAG ได้แล้ว")


if __name__ == "__main__":
    main()
