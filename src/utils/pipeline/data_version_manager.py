"""
Data Version Manager สำหรับจัดการเวอร์ชันข้อมูล, index และ data lineage
"""

import os
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataVersionManager:
    """
    จัดการเวอร์ชันข้อมูล, index และ data lineage
    
    คลาสนี้ช่วยในการ:
    1. จัดการเวอร์ชันข้อมูลดิบ (.txt) ในโฟลเดอร์ data/raw/v{version}/
    2. เชื่อมโยง FAISS index กับเวอร์ชันข้อมูลที่ใช้สร้าง
    3. บันทึกข้อมูล lineage เพื่อติดตามว่า index ถูกสร้างจากข้อมูลเวอร์ชันใด
    """
    
    def __init__(
        self, 
        base_data_dir: str,
        base_index_dir: str,
        data_version: str = "latest",
        gcs_path: Optional[str] = None
    ) -> None:
        """
        สร้าง DataVersionManager
        
        Parameters
        ----------
        base_data_dir : str
            ไดเรกทอรีหลักสำหรับข้อมูล (เช่น 'data/')
        base_index_dir : str
            ไดเรกทอรีหลักสำหรับ index (เช่น 'artifacts/')
        data_version : str
            เวอร์ชันข้อมูลที่ต้องการใช้ (เช่น 'v1.0', 'v1.1', 'latest')
        gcs_path : Optional[str]
            เส้นทาง GCS หากใช้ข้อมูลจาก Google Cloud Storage
        """
        self.base_data_dir = Path(base_data_dir)
        self.base_index_dir = Path(base_index_dir)
        self.data_version = data_version
        self.gcs_path = gcs_path
        
        # สร้างไดเรกทอรีหลักหากยังไม่มี
        os.makedirs(self.base_data_dir, exist_ok=True)
        os.makedirs(self.base_index_dir, exist_ok=True)
        
        # สร้างไดเรกทอรี raw/ หากยังไม่มี
        self.raw_dir = self.base_data_dir / "raw"
        os.makedirs(self.raw_dir, exist_ok=True)
        
        # ตรวจสอบและสร้างไดเรกทอรีเวอร์ชัน
        self._initialize_version_directories()
        
    def _initialize_version_directories(self) -> None:
        """สร้างไดเรกทอรีเวอร์ชันหากยังไม่มี และตรวจสอบเวอร์ชัน 'latest'"""
        # ตรวจสอบว่ามีไดเรกทอรีเวอร์ชันหรือไม่
        version_dirs = [d for d in os.listdir(self.raw_dir) 
                       if os.path.isdir(os.path.join(self.raw_dir, d)) and d.startswith('v')]
        
        # ถ้าไม่มีไดเรกทอรีเวอร์ชัน ให้สร้าง v1.0
        if not version_dirs:
            os.makedirs(os.path.join(self.raw_dir, "v1.0"), exist_ok=True)
            # สร้าง symlink สำหรับ latest
            latest_link = os.path.join(self.raw_dir, "latest")
            if os.path.exists(latest_link):
                os.remove(latest_link)
            os.symlink("v1.0", latest_link, target_is_directory=True)
            logger.info(f"Created initial version directory v1.0 and set it as 'latest'")
        
        # ถ้าไม่มี symlink latest ให้สร้างและชี้ไปที่เวอร์ชันล่าสุด
        latest_link = os.path.join(self.raw_dir, "latest")
        if not os.path.exists(latest_link):
            # เรียงเวอร์ชันและเลือกเวอร์ชันล่าสุด
            version_dirs.sort(key=lambda x: [int(n) for n in x.replace('v', '').split('.')])
            latest_version = version_dirs[-1]
            os.symlink(latest_version, latest_link, target_is_directory=True)
            logger.info(f"Set 'latest' to point to {latest_version}")
    
    def get_data_version_path(self, version: Optional[str] = None) -> Path:
        """
        รับเส้นทางไดเรกทอรีสำหรับเวอร์ชันข้อมูลที่ระบุ
        
        Parameters
        ----------
        version : Optional[str]
            เวอร์ชันที่ต้องการ (ถ้าไม่ระบุจะใช้เวอร์ชันที่ตั้งไว้ตอนสร้างอ็อบเจกต์)
            
        Returns
        -------
        Path
            เส้นทางไดเรกทอรีของเวอร์ชันข้อมูล
        """
        version = version or self.data_version
        version_dir = self.raw_dir / version
        
        if not os.path.exists(version_dir):
            raise ValueError(f"Data version '{version}' does not exist")
        
        return version_dir
    
    def get_index_path_for_version(self, version: Optional[str] = None) -> Path:
        """
        รับเส้นทาง index สำหรับเวอร์ชันข้อมูลที่ระบุ
        
        Parameters
        ----------
        version : Optional[str]
            เวอร์ชันข้อมูลที่ต้องการ (ถ้าไม่ระบุจะใช้เวอร์ชันที่ตั้งไว้ตอนสร้างอ็อบเจกต์)
            
        Returns
        -------
        Path
            เส้นทางไดเรกทอรีของ index สำหรับเวอร์ชันข้อมูลที่ระบุ
        """
        version = version or self.data_version
        # ถ้าเป็น 'latest' ให้อ่านจาก symlink
        if version == "latest":
            target = os.readlink(os.path.join(self.raw_dir, "latest"))
            version = target
        
        index_dir = self.base_index_dir / f"faiss_index_{version}"
        os.makedirs(index_dir, exist_ok=True)
        
        return index_dir
    
    def list_available_versions(self) -> List[str]:
        """
        แสดงรายการเวอร์ชันข้อมูลที่มีอยู่
        
        Returns
        -------
        List[str]
            รายการเวอร์ชันข้อมูลที่มีอยู่
        """
        version_dirs = [d for d in os.listdir(self.raw_dir) 
                       if os.path.isdir(os.path.join(self.raw_dir, d)) and d.startswith('v')]
        version_dirs.sort(key=lambda x: [int(n) for n in x.replace('v', '').split('.')])
        return version_dirs
    
    def create_new_version(self, source_files: List[str], increment_type: str = "minor") -> str:
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
            major, minor = map(int, latest.replace('v', '').split('.'))
            
            if increment_type == "major":
                new_version = f"v{major + 1}.0"
            else:  # minor
                new_version = f"v{major}.{minor + 1}"
        
        # สร้างไดเรกทอรีเวอร์ชันใหม่
        new_version_dir = os.path.join(self.raw_dir, new_version)
        os.makedirs(new_version_dir, exist_ok=True)
        
        # คัดลอกไฟล์
        for src_file in source_files:
            if os.path.exists(src_file):
                dest_file = os.path.join(new_version_dir, os.path.basename(src_file))
                shutil.copy2(src_file, dest_file)
                logger.info(f"Copied {src_file} to {dest_file}")
            else:
                logger.warning(f"Source file {src_file} does not exist")
        
        # อัปเดต symlink latest
        latest_link = os.path.join(self.raw_dir, "latest")
        if os.path.exists(latest_link):
            os.remove(latest_link)
        os.symlink(new_version, latest_link, target_is_directory=True)
        
        logger.info(f"Created new data version {new_version} and updated 'latest' to point to it")
        return new_version
    
    def create_lineage_record(self, 
                             index_path: str, 
                             data_version: str,
                             files_used: List[str],
                             parameters: Dict[str, Any]) -> Dict[str, Any]:
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
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                
                file_info = {
                    "file_name": os.path.basename(file_path),
                    "file_path": str(file_path),
                    "md5_hash": file_hash,
                    "size_bytes": os.path.getsize(file_path),
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                }
                file_metadata.append(file_info)
        
        # สร้างบันทึก lineage
        lineage_record = {
            "index_path": index_path,
            "data_version": data_version,
            "creation_time": datetime.now().isoformat(),
            "files": file_metadata,
            "parameters": parameters,
            "source_type": "local" if not self.gcs_path else "gcs",
            "gcs_path": self.gcs_path
        }
        
        # บันทึกไฟล์ lineage
        lineage_file = os.path.join(os.path.dirname(index_path), "lineage.json")
        with open(lineage_file, 'w', encoding='utf-8') as f:
            json.dump(lineage_record, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created lineage record at {lineage_file}")
        return lineage_record
    
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
        lineage_file = os.path.join(os.path.dirname(index_path), "lineage.json")
        if os.path.exists(lineage_file):
            with open(lineage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    # สำหรับรองรับ GCS ในอนาคต
    def download_from_gcs(self, gcs_path: str, data_version: str) -> List[str]:
        """
        ดาวน์โหลดข้อมูลจาก GCS ตามเวอร์ชันที่ระบุ
        
        Parameters
        ----------
        gcs_path : str
            เส้นทาง GCS เช่น 'gs://your-bucket/data/raw'
        data_version : str
            เวอร์ชันข้อมูล เช่น 'v1.1'
            
        Returns
        -------
        List[str]
            รายการเส้นทางไฟล์ที่ดาวน์โหลด
        """
        # ตรวจสอบว่ามีการติดตั้ง google-cloud-storage หรือไม่
        try:
            from google.cloud import storage
        except ImportError:
            logger.error("google-cloud-storage is not installed. Run 'pip install google-cloud-storage'")
            return []
        
        logger.info(f"Downloading data from GCS: {gcs_path}/{data_version}")
        
        # แยกชื่อบัคเก็ตและเส้นทาง
        bucket_name = gcs_path.replace("gs://", "").split("/")[0]
        prefix = "/".join(gcs_path.replace("gs://", "").split("/")[1:])
        
        if not prefix.endswith("/"):
            prefix += "/"
        
        # เพิ่มเวอร์ชันเข้าไปในเส้นทาง
        version_prefix = f"{prefix}{data_version}/"
        
        # สร้างไคลเอนต์
        client = storage.Client()
        
        # ดึงบัคเก็ต
        bucket = client.bucket(bucket_name)
        
        # สร้างไดเรกทอรีเป้าหมาย
        target_dir = self.get_data_version_path(data_version)
        os.makedirs(target_dir, exist_ok=True)
        
        # ดาวน์โหลดไฟล์
        downloaded_files = []
        for blob in bucket.list_blobs(prefix=version_prefix):
            # สร้างเส้นทางไฟล์ในเครื่อง
            local_path = os.path.join(target_dir, os.path.basename(blob.name))
            
            # ดาวน์โหลดไฟล์
            blob.download_to_filename(local_path)
            downloaded_files.append(local_path)
            logger.info(f"Downloaded {blob.name} to {local_path}")
        
        return downloaded_files
