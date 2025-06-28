"""
Data Version Manager สำหรับจัดการเวอร์ชันข้อมูล, index และ data lineage
รองรับทั้ง Local Storage และ Google Cloud Storage (GCS)
"""

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataVersionManager:
    """
    จัดการเวอร์ชันข้อมูล, index และ data lineage

    คลาสนี้ช่วยในการ:
    1. จัดการเวอร์ชันข้อมูลดิบ (.txt) ในโฟลเดอร์ data/raw/v{version}/
    2. เชื่อมโยง FAISS index กับเวอร์ชันข้อมูลที่ใช้สร้าง
    3. บันทึกข้อมูล lineage เพื่อติดตามว่า index ถูกสร้างจากข้อมูลเวอร์ชันใด
    4. รองรับการเก็บข้อมูลทั้งใน Local Storage และ Google Cloud Storage
    """

    def __init__(
        self,
        base_data_dir: Optional[str] = None,
        base_index_dir: Optional[str] = None,
        data_version: str = "latest",
        gcs_bucket: Optional[str] = None,
        gcs_prefix: str = "data",
        storage_type: str = "local",  # "local", "gcs", "hybrid"
        project_id: Optional[str] = None,
    ) -> None:
        """
        สร้าง DataVersionManager

        Parameters
        ----------
        base_data_dir : Optional[str]
            ไดเรกทอรีหลักสำหรับข้อมูล (เช่น 'data/') - ใช้เฉพาะเมื่อ storage_type เป็น "local" หรือ "hybrid"
        base_index_dir : Optional[str]
            ไดเรกทอรีหลักสำหรับ index (เช่น 'artifacts/') - ใช้เฉพาะเมื่อ storage_type เป็น "local" หรือ "hybrid"
        data_version : str
            เวอร์ชันข้อมูลที่ต้องการใช้ (เช่น 'v1.0', 'v1.1', 'latest')
        gcs_bucket : Optional[str]
            ชื่อ GCS bucket (เช่น 'my-data-bucket')
        gcs_prefix : str
            Prefix สำหรับข้อมูลใน GCS (เช่น 'data')
        storage_type : str
            ประเภทการจัดเก็บข้อมูล ("local", "gcs", "hybrid")
        project_id : Optional[str]
            Google Cloud Project ID
        """
        self.storage_type = storage_type
        self.data_version = data_version
        self.gcs_bucket = gcs_bucket
        self.gcs_prefix = gcs_prefix
        self.project_id = project_id

        # ตรวจสอบ storage type
        if storage_type not in ["local", "gcs", "hybrid"]:
            raise ValueError("storage_type must be 'local', 'gcs', or 'hybrid'")

        # สำหรับ local storage
        if storage_type in ["local", "hybrid"]:
            if not base_data_dir or not base_index_dir:
                raise ValueError(
                    "base_data_dir and base_index_dir are required for local storage"
                )

            self.base_data_dir = Path(base_data_dir)
            self.base_index_dir = Path(base_index_dir)

            # สร้างไดเรกทอรีหลักหากยังไม่มี
            self.base_data_dir.mkdir(parents=True, exist_ok=True)
            self.base_index_dir.mkdir(parents=True, exist_ok=True)

            # สร้างไดเรกทอรี raw/ หากยังไม่มี
            self.raw_dir = self.base_data_dir / "raw"
            self.raw_dir.mkdir(exist_ok=True)

            # ตรวจสอบและสร้างไดเรกทอรีเวอร์ชัน
            self._initialize_version_directories()

        # สำหรับ GCS storage
        if storage_type in ["gcs", "hybrid"]:
            if not gcs_bucket:
                raise ValueError("gcs_bucket is required for GCS storage")

            # ตรวจสอบ GCS credentials
            self._validate_gcs_setup()

    def _validate_gcs_setup(self) -> None:
        """ตรวจสอบการตั้งค่า GCS"""
        try:
            from google.auth.exceptions import DefaultCredentialsError
            from google.cloud import storage  # type: ignore

            # ตรวจสอบ credentials
            try:
                client = storage.Client(project=self.project_id)
                # ทดสอบการเข้าถึง bucket
                bucket = client.bucket(self.gcs_bucket)
                if not bucket.exists():
                    logger.warning(f"GCS bucket '{self.gcs_bucket}' does not exist")
                else:
                    logger.info(f"GCS bucket '{self.gcs_bucket}' is accessible")
            except DefaultCredentialsError:
                logger.error(
                    "GCS credentials not found. Please set up authentication:\n"
                    "1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable\n"
                    "2. Or use 'gcloud auth application-default login'"
                )
                raise

        except ImportError:
            logger.error(
                "google-cloud-storage is not installed. "
                "Install it with: uv add google-cloud-storage"
            )
            raise

    def _create_symlink(self, target: str, link_path: str) -> bool:
        """
        สร้าง symlink พร้อม error handling

        Parameters
        ----------
        target : str
            เป้าหมายของ symlink
        link_path : str
            เส้นทางของ symlink ที่จะสร้าง

        Returns
        -------
        bool
            True ถ้าสร้างสำเร็จ, False ถ้าไม่สำเร็จ
        """
        try:
            # ลบ symlink เดิมหากมี
            if os.path.exists(link_path):
                if os.path.islink(link_path):
                    os.unlink(link_path)
                else:
                    os.remove(link_path)

            # สร้าง symlink ใหม่
            os.symlink(target, link_path, target_is_directory=True)
            return True
        except OSError as e:
            logger.warning(f"Could not create symlink {link_path} -> {target}: {e}")
            # บน Windows หรือระบบที่ไม่รองรับ symlink ให้คัดลอกแทน
            try:
                if os.path.isdir(target):
                    shutil.copytree(target, link_path, dirs_exist_ok=True)
                    logger.info(
                        f"Copied directory {target} to {link_path} instead of symlink"
                    )
                    return True
                else:
                    shutil.copy2(target, link_path)
                    logger.info(
                        f"Copied file {target} to {link_path} instead of symlink"
                    )
                    return True
            except Exception as copy_error:
                logger.error(f"Failed to copy {target} to {link_path}: {copy_error}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error creating symlink {link_path}: {e}")
            return False

    def _initialize_version_directories(self) -> None:
        """สร้างไดเรกทอรีเวอร์ชันหากยังไม่มี และตรวจสอบเวอร์ชัน 'latest'"""
        # ตรวจสอบว่ามีไดเรกทอรีเวอร์ชันหรือไม่
        version_dirs = [
            d for d in self.raw_dir.iterdir() if d.is_dir() and d.name.startswith("v")
        ]

        # ถ้าไม่มีไดเรกทอรีเวอร์ชัน ให้สร้าง v1.0
        if not version_dirs:
            (self.raw_dir / "v1.0").mkdir(exist_ok=True)
            # สร้าง symlink สำหรับ latest
            latest_link = self.raw_dir / "latest"
            if self._create_symlink("v1.0", str(latest_link)):
                logger.info(
                    "Created initial version directory v1.0 and set it as 'latest'"
                )
            else:
                logger.error("Failed to create 'latest' symlink")

        # ถ้าไม่มี symlink latest ให้สร้างและชี้ไปที่เวอร์ชันล่าสุด
        latest_link = self.raw_dir / "latest"
        if not latest_link.exists():
            # เรียงเวอร์ชันและเลือกเวอร์ชันล่าสุด
            version_dirs = [
                d
                for d in self.raw_dir.iterdir()
                if d.is_dir() and d.name.startswith("v")
            ]
            version_dirs.sort(
                key=lambda x: [int(n) for n in x.name.replace("v", "").split(".")]
            )
            if version_dirs:
                latest_version = version_dirs[-1].name
                if self._create_symlink(latest_version, str(latest_link)):
                    logger.info(f"Set 'latest' to point to {latest_version}")
                else:
                    logger.error(
                        f"Failed to create 'latest' symlink pointing to {latest_version}"
                    )

    def get_data_version_path(self, version: Optional[str] = None) -> Union[Path, str]:
        """
        รับเส้นทางไดเรกทอรีสำหรับเวอร์ชันข้อมูลที่ระบุ

        Parameters
        ----------
        version : Optional[str]
            เวอร์ชันที่ต้องการ (ถ้าไม่ระบุจะใช้เวอร์ชันที่ตั้งไว้ตอนสร้างอ็อบเจกต์)

        Returns
        -------
        Union[Path, str]
            เส้นทางไดเรกทอรีของเวอร์ชันข้อมูล
        """
        version = version or self.data_version

        if self.storage_type == "gcs":
            # สำหรับ GCS
            return f"gs://{self.gcs_bucket}/{self.gcs_prefix}/raw/{version}"
        else:
            # สำหรับ local storage
            version_dir = self.raw_dir / version
            if not version_dir.exists():
                raise ValueError(f"Data version '{version}' does not exist")
            return version_dir

    def get_index_path_for_version(
        self, version: Optional[str] = None
    ) -> Union[Path, str]:
        """
        รับเส้นทาง index สำหรับเวอร์ชันข้อมูลที่ระบุ

        Parameters
        ----------
        version : Optional[str]
            เวอร์ชันข้อมูลที่ต้องการ (ถ้าไม่ระบุจะใช้เวอร์ชันที่ตั้งไว้ตอนสร้างอ็อบเจกต์)

        Returns
        -------
        Union[Path, str]
            เส้นทางไดเรกทอรีของ index สำหรับเวอร์ชันข้อมูลที่ระบุ
        """
        version = version or self.data_version

        if self.storage_type == "gcs":
            # สำหรับ GCS
            return (
                f"gs://{self.gcs_bucket}/{self.gcs_prefix}/index/faiss_index_{version}"
            )
        else:
            # สำหรับ local storage
            # ถ้าเป็น 'latest' ให้อ่านจาก symlink
            if version == "latest":
                latest_link = self.raw_dir / "latest"
                if latest_link.exists():
                    if latest_link.is_symlink():
                        target = os.readlink(str(latest_link))
                        version = os.path.basename(target)
                    else:
                        # ถ้าไม่ใช่ symlink ให้ใช้ชื่อไดเรกทอรี
                        version = latest_link.name
                else:
                    raise ValueError("'latest' symlink does not exist")

            index_dir = self.base_index_dir / f"faiss_index_{version}"
            index_dir.mkdir(parents=True, exist_ok=True)
            return index_dir

    def list_available_versions(self) -> List[str]:
        """
        แสดงรายการเวอร์ชันข้อมูลที่มีอยู่

        Returns
        -------
        List[str]
            รายการเวอร์ชันข้อมูลที่มีอยู่
        """
        if self.storage_type == "gcs":
            return self._list_gcs_versions()
        else:
            return self._list_local_versions()

    def _list_local_versions(self) -> List[str]:
        """แสดงรายการเวอร์ชันข้อมูลใน local storage"""
        version_dirs = [
            d.name
            for d in self.raw_dir.iterdir()
            if d.is_dir() and d.name.startswith("v")
        ]
        version_dirs.sort(key=lambda x: [int(n) for n in x.replace("v", "").split(".")])
        return version_dirs

    def _list_gcs_versions(self) -> List[str]:
        """แสดงรายการเวอร์ชันข้อมูลใน GCS"""
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.gcs_bucket)

            # หา prefix สำหรับ raw data
            raw_prefix = f"{self.gcs_prefix}/raw/"

            # หาเวอร์ชันทั้งหมด
            versions = set()
            for blob in bucket.list_blobs(prefix=raw_prefix, delimiter="/"):
                if blob.name.endswith("/"):
                    # เอาเฉพาะชื่อเวอร์ชัน
                    version_name = blob.name.replace(raw_prefix, "").rstrip("/")
                    if version_name.startswith("v"):
                        versions.add(version_name)

            version_list = list(versions)
            version_list.sort(
                key=lambda x: [int(n) for n in x.replace("v", "").split(".")]
            )
            return version_list

        except Exception as e:
            logger.error(f"Error listing GCS versions: {e}")
            return []

    def create_new_version(
        self, source_files: List[str], increment_type: str = "minor"
    ) -> str:
        """
        สร้างเวอร์ชันข้อมูลใหม่โดยคัดลอกไฟล์จากแหล่งที่มา

        Parameters
        ----------
        source_files : List[str]
            รายการเส้นทางไฟล์ต้นฉบับที่ต้องการคัดลอก
        increment_type : str
            ประเภทการเพิ่มเวอร์ชัน ("major" หรือ "minor")

        Returns
        -------
        str
            เวอร์ชันใหม่ที่สร้าง (เช่น "v1.1")
        """
        # หาเวอร์ชันล่าสุด
        versions = self.list_available_versions()
        if not versions:
            new_version = "v1.0"
        else:
            latest = versions[-1]
            major, minor = map(int, latest.replace("v", "").split("."))

            if increment_type == "major":
                new_version = f"v{major + 1}.0"
            else:  # minor
                new_version = f"v{major}.{minor + 1}"

        # สร้างเวอร์ชันใหม่ตาม storage type
        if self.storage_type == "gcs":
            self._create_gcs_version(new_version, source_files)
        else:
            self._create_local_version(new_version, source_files)

        logger.info(f"Created new data version {new_version}")
        return new_version

    def _create_local_version(self, new_version: str, source_files: List[str]) -> None:
        """สร้างเวอร์ชันใหม่ใน local storage"""
        # สร้างไดเรกทอรีเวอร์ชันใหม่
        new_version_dir = self.raw_dir / new_version
        new_version_dir.mkdir(exist_ok=True)

        # คัดลอกไฟล์
        for src_file in source_files:
            src_path = Path(src_file)
            if src_path.exists():
                dest_file = new_version_dir / src_path.name
                shutil.copy2(src_path, dest_file)
                logger.info(f"Copied {src_file} to {dest_file}")
            else:
                logger.warning(f"Source file {src_file} does not exist")

        # อัปเดต symlink latest
        latest_link = self.raw_dir / "latest"
        if not self._create_symlink(new_version, str(latest_link)):
            logger.error(f"Failed to update 'latest' symlink to point to {new_version}")

    def _create_gcs_version(self, new_version: str, source_files: List[str]) -> None:
        """สร้างเวอร์ชันใหม่ใน GCS"""
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.gcs_bucket)

            # อัปโหลดไฟล์
            for src_file in source_files:
                src_path = Path(src_file)
                if src_path.exists():
                    # สร้าง blob name
                    blob_name = f"{self.gcs_prefix}/raw/{new_version}/{src_path.name}"
                    blob = bucket.blob(blob_name)

                    # อัปโหลดไฟล์
                    blob.upload_from_filename(str(src_path))
                    logger.info(
                        f"Uploaded {src_file} to gs://{self.gcs_bucket}/{blob_name}"
                    )
                else:
                    logger.warning(f"Source file {src_file} does not exist")

        except Exception as e:
            logger.error(f"Error creating GCS version {new_version}: {e}")
            raise

    def create_lineage_record(
        self,
        index_path: str,
        data_version: str,
        files_used: List[str],
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        สร้างบันทึก lineage ที่เชื่อมโยง index กับข้อมูลต้นทาง

        Parameters
        ----------
        index_path : str
            เส้นทางของ index ที่สร้าง
        data_version : str
            เวอร์ชันข้อมูลที่ใช้สร้าง index
        files_used : List[str]
            รายการไฟล์ที่ใช้สร้าง index
        parameters : Dict[str, Any]
            พารามิเตอร์ที่ใช้ในการสร้าง index

        Returns
        -------
        Dict[str, Any]
            ข้อมูล lineage ที่สร้าง
        """
        # สร้างข้อมูล file metadata
        file_metadata = []
        for file_path in files_used:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                with open(file_path_obj, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()

                file_info = {
                    "file_name": file_path_obj.name,
                    "file_path": str(file_path_obj),
                    "md5_hash": file_hash,
                    "size_bytes": file_path_obj.stat().st_size,
                    "last_modified": datetime.fromtimestamp(
                        file_path_obj.stat().st_mtime
                    ).isoformat(),
                }
                file_metadata.append(file_info)

        # สร้างบันทึก lineage
        lineage_record = {
            "index_path": index_path,
            "data_version": data_version,
            "creation_time": datetime.now().isoformat(),
            "files": file_metadata,
            "parameters": parameters,
            "storage_type": self.storage_type,
            "gcs_bucket": self.gcs_bucket,
            "gcs_prefix": self.gcs_prefix,
        }

        # บันทึกไฟล์ lineage
        if self.storage_type == "gcs":
            self._save_gcs_lineage(lineage_record, index_path)
        else:
            self._save_local_lineage(lineage_record, index_path)

        logger.info(f"Created lineage record for {index_path}")
        return lineage_record

    def _save_local_lineage(
        self, lineage_record: Dict[str, Any], index_path: str
    ) -> None:
        """บันทึก lineage ใน local storage"""
        lineage_file = Path(index_path).parent / "lineage.json"
        with open(lineage_file, "w", encoding="utf-8") as f:
            json.dump(lineage_record, f, indent=2, ensure_ascii=False)

    def _save_gcs_lineage(
        self, lineage_record: Dict[str, Any], index_path: str
    ) -> None:
        """บันทึก lineage ใน GCS"""
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.gcs_bucket)

            # สร้าง blob name สำหรับ lineage
            index_path_str = str(index_path)
            if index_path_str.startswith(f"gs://{self.gcs_bucket}/"):
                relative_path = index_path_str.replace(f"gs://{self.gcs_bucket}/", "")
            else:
                relative_path = index_path_str

            lineage_blob_name = f"{os.path.dirname(relative_path)}/lineage.json"
            blob = bucket.blob(lineage_blob_name)

            # อัปโหลด lineage record
            blob.upload_from_string(
                json.dumps(lineage_record, indent=2, ensure_ascii=False),
                content_type="application/json",
            )

        except Exception as e:
            logger.error(f"Error saving GCS lineage: {e}")
            raise

    def get_lineage_for_index(self, index_path: str) -> Optional[Dict[str, Any]]:
        """
        อ่านข้อมูล lineage สำหรับ index ที่ระบุ

        Parameters
        ----------
        index_path : str
            เส้นทางของ index

        Returns
        -------
        Optional[Dict[str, Any]]
            ข้อมูล lineage หรือ None ถ้าไม่พบ
        """
        if self.storage_type == "gcs":
            return self._get_gcs_lineage(index_path)
        else:
            return self._get_local_lineage(index_path)

    def _get_local_lineage(self, index_path: str) -> Optional[Dict[str, Any]]:
        """อ่าน lineage จาก local storage"""
        lineage_file = Path(index_path).parent / "lineage.json"
        if lineage_file.exists():
            with open(lineage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _get_gcs_lineage(self, index_path: str) -> Optional[Dict[str, Any]]:
        """อ่าน lineage จาก GCS"""
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.gcs_bucket)

            # สร้าง blob name สำหรับ lineage
            index_path_str = str(index_path)
            if index_path_str.startswith(f"gs://{self.gcs_bucket}/"):
                relative_path = index_path_str.replace(f"gs://{self.gcs_bucket}/", "")
            else:
                relative_path = index_path_str

            lineage_blob_name = f"{os.path.dirname(relative_path)}/lineage.json"
            blob = bucket.blob(lineage_blob_name)

            if blob.exists():
                content = blob.download_as_text()
                return json.loads(content)
            return None

        except Exception as e:
            logger.error(f"Error reading GCS lineage: {e}")
            return None

    def download_from_gcs(
        self, data_version: str, local_dir: Optional[str] = None
    ) -> List[str]:
        """
        ดาวน์โหลดข้อมูลจาก GCS ตามเวอร์ชันที่ระบุ

        Parameters
        ----------
        data_version : str
            เวอร์ชันข้อมูล เช่น 'v1.1'
        local_dir : Optional[str]
            ไดเรกทอรีปลายทาง (ถ้าไม่ระบุจะใช้ base_data_dir)

        Returns
        -------
        List[str]
            รายการเส้นทางไฟล์ที่ดาวน์โหลด
        """
        if self.storage_type not in ["gcs", "hybrid"]:
            raise ValueError("GCS download is only available for GCS or hybrid storage")

        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.gcs_bucket)

            # สร้างไดเรกทอรีปลายทาง
            if local_dir:
                target_dir = Path(local_dir)
            else:
                # สำหรับ hybrid storage ใช้ local path
                if self.storage_type == "hybrid":
                    target_dir = self.raw_dir / data_version
                else:
                    # สำหรับ GCS-only storage สร้าง temporary directory
                    target_dir = Path(f"/tmp/gcs_download_{data_version}")

            target_dir.mkdir(parents=True, exist_ok=True)

            # หา prefix สำหรับเวอร์ชัน
            version_prefix = f"{self.gcs_prefix}/raw/{data_version}/"

            # ดาวน์โหลดไฟล์
            downloaded_files = []
            for blob in bucket.list_blobs(prefix=version_prefix):
                # สร้างเส้นทางไฟล์ในเครื่อง
                local_path = target_dir / Path(blob.name).name

                # ดาวน์โหลดไฟล์
                blob.download_to_filename(str(local_path))
                downloaded_files.append(str(local_path))
                logger.info(f"Downloaded {blob.name} to {local_path}")

            return downloaded_files

        except Exception as e:
            logger.error(f"Error downloading from GCS: {e}")
            return []

    def upload_to_gcs(self, local_files: List[str], data_version: str) -> List[str]:
        """
        อัปโหลดไฟล์จาก local storage ไปยัง GCS

        Parameters
        ----------
        local_files : List[str]
            รายการเส้นทางไฟล์ในเครื่อง
        data_version : str
            เวอร์ชันข้อมูลที่ต้องการอัปโหลด

        Returns
        -------
        List[str]
            รายการ GCS paths ที่อัปโหลด
        """
        if self.storage_type not in ["gcs", "hybrid"]:
            raise ValueError("GCS upload is only available for GCS or hybrid storage")

        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.gcs_bucket)

            uploaded_files = []
            for local_file in local_files:
                local_path = Path(local_file)
                if local_path.exists():
                    # สร้าง blob name
                    blob_name = (
                        f"{self.gcs_prefix}/raw/{data_version}/{local_path.name}"
                    )
                    blob = bucket.blob(blob_name)

                    # อัปโหลดไฟล์
                    blob.upload_from_filename(str(local_path))
                    uploaded_files.append(f"gs://{self.gcs_bucket}/{blob_name}")
                    logger.info(
                        f"Uploaded {local_file} to gs://{self.gcs_bucket}/{blob_name}"
                    )
                else:
                    logger.warning(f"Local file {local_file} does not exist")

            return uploaded_files

        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            return []
