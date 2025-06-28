import os

from src.utils.logger import get_logger
from src.utils.pipeline.data_version_manager import DataVersionManager

"""
ตัวอย่างการใช้งาน DataVersionManager กับ GCS สำหรับ Production

การตั้งค่าที่จำเป็น:
1. Google Cloud Project
2. GCS Bucket
3. Service Account หรือ Application Default Credentials
4. google-cloud-storage package
"""

logger = get_logger(__name__)


def setup_gcs_credentials():
    """
    ตั้งค่า GCS credentials

    วิธีที่ 1: ใช้ Service Account Key
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

    วิธีที่ 2: ใช้ Application Default Credentials
    gcloud auth application-default login
    """
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.info("Using Application Default Credentials")
        logger.info("Run 'gcloud auth application-default login' if not set up")
    else:
        logger.info(
            f"Using Service Account: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}"
        )


def create_production_dvm():
    """
    สร้าง DataVersionManager สำหรับ production

    ตัวเลือก:
    1. GCS-only: เก็บข้อมูลทั้งหมดใน GCS
    2. Hybrid: เก็บข้อมูลใน local และ GCS
    """

    # ตั้งค่า GCS
    project_id = "your-gcp-project-id"  # เปลี่ยนเป็น project ID ของคุณ
    bucket_name = "your-data-bucket"  # เปลี่ยนเป็นชื่อ bucket ของคุณ

    # ตัวเลือก 1: GCS-only (แนะนำสำหรับ production)
    dvm_gcs = DataVersionManager(
        storage_type="gcs",
        gcs_bucket=bucket_name,
        gcs_prefix="ragchain-data",
        project_id=project_id,
        data_version="latest",
    )

    # ตัวเลือก 2: Hybrid (เก็บทั้ง local และ GCS)
    dvm_hybrid = DataVersionManager(
        base_data_dir="data",
        base_index_dir="artifacts",
        storage_type="hybrid",
        gcs_bucket=bucket_name,
        gcs_prefix="ragchain-data",
        project_id=project_id,
        data_version="latest",
    )

    return dvm_gcs, dvm_hybrid


def example_gcs_workflow():
    """ตัวอย่างการใช้งาน GCS workflow"""

    # ตั้งค่า credentials
    setup_gcs_credentials()

    # สร้าง DVM
    dvm, _ = create_production_dvm()

    # 1. สร้างเวอร์ชันข้อมูลใหม่
    source_files = ["data/raw/source1.txt", "data/raw/source2.txt"]

    new_version = dvm.create_new_version(
        source_files=source_files, increment_type="minor"
    )
    logger.info(f"Created new version: {new_version}")

    # 2. ดูรายการเวอร์ชันที่มี
    versions = dvm.list_available_versions()
    logger.info(f"Available versions: {versions}")

    # 3. รับเส้นทางข้อมูล
    data_path = dvm.get_data_version_path("v1.1")
    index_path = dvm.get_index_path_for_version("v1.1")

    logger.info(f"Data path: {data_path}")
    logger.info(f"Index path: {index_path}")

    # 4. สร้าง lineage record
    lineage_record = dvm.create_lineage_record(
        index_path=str(index_path),
        data_version="v1.1",
        files_used=source_files,
        parameters={
            "chunk_size": 1000,
            "embedding_model": "text-embedding-ada-002",
            "index_type": "faiss",
        },
    )

    logger.info(f"Created lineage record: {lineage_record['creation_time']}")

    # 5. อ่าน lineage
    lineage = dvm.get_lineage_for_index(str(index_path))
    if lineage:
        logger.info(f"Found lineage for {index_path}")


def example_hybrid_workflow():
    """ตัวอย่างการใช้งาน Hybrid workflow (local + GCS)"""

    setup_gcs_credentials()

    # สร้าง hybrid DVM
    _, dvm = create_production_dvm()

    # 1. สร้างเวอร์ชันใน local
    source_files = ["data/raw/local_source.txt"]
    new_version = dvm.create_new_version(source_files, "minor")

    # 2. อัปโหลดไปยัง GCS
    uploaded_files = dvm.upload_to_gcs(source_files, new_version)
    logger.info(f"Uploaded to GCS: {uploaded_files}")

    # 3. ดาวน์โหลดจาก GCS
    downloaded_files = dvm.download_from_gcs(new_version, "temp_download")
    logger.info(f"Downloaded from GCS: {downloaded_files}")


def production_best_practices():
    """Best practices สำหรับ production"""

    logger.info("=== Production Best Practices ===")

    # 1. ใช้ GCS สำหรับ production
    logger.info("1. ใช้ GCS สำหรับ production เพื่อความน่าเชื่อถือ")

    # 2. ตั้งค่า credentials อย่างปลอดภัย
    logger.info("2. ใช้ Service Account Key แทน Application Default Credentials")

    # 3. ตั้งค่า bucket permissions
    logger.info("3. ตั้งค่า IAM permissions ให้เหมาะสม")

    # 4. ใช้ versioning
    logger.info("4. เปิดใช้ GCS bucket versioning")

    # 5. ตั้งค่า lifecycle management
    logger.info("5. ตั้งค่า lifecycle management เพื่อลดค่าใช้จ่าย")

    # 6. Monitoring และ logging
    logger.info("6. ตั้งค่า monitoring และ logging")

    # 7. Backup strategy
    logger.info("7. มี backup strategy ที่เหมาะสม")


if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    try:
        logger.info("=== GCS Workflow Example ===")
        example_gcs_workflow()

        logger.info("\n=== Hybrid Workflow Example ===")
        example_hybrid_workflow()

        logger.info("\n=== Best Practices ===")
        production_best_practices()

    except Exception as e:
        logger.error(f"Error in example: {e}")
        logger.info("Make sure to:")
        logger.info("1. Set up GCS credentials")
        logger.info("2. Update project_id and bucket_name")
        logger.info("3. Install google-cloud-storage: uv add google-cloud-storage")
