"""
Data Version Manager for managing data versions, indexes, and data lineage.
Supports both Local Storage and Google Cloud Storage (GCS).
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
    Manages data versions, indexes, and data lineage.

    This class assists with:
    1. Managing raw data versions (.txt) in the `data/raw/v{version}/` folder.
    2. Associating FAISS indexes with the data version used for their creation.
    3. Recording lineage information to track which data version an index was built from.
    4. Supporting data storage in both Local Storage and Google Cloud Storage.
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
        Initializes the DataVersionManager.

        Parameters
        ----------
        base_data_dir : Optional[str]
            The base directory for data (e.g., 'data/') - used only when `storage_type` is "local" or "hybrid".
        base_index_dir : Optional[str]
            The base directory for indexes (e.g., 'artifacts/') - used only when `storage_type` is "local" or "hybrid".
        data_version : str
            The data version to use (e.g., 'v1.0', 'v1.1', 'latest').
        gcs_bucket : Optional[str]
            The GCS bucket name (e.g., 'my-data-bucket').
        gcs_prefix : str
            The prefix for data in GCS (e.g., 'data').
        storage_type : str
            The type of data storage to use ("local", "gcs", "hybrid").
        project_id : Optional[str]
            Google Cloud Project ID.
        """
        self.storage_type = storage_type
        self.data_version = data_version
        self.gcs_bucket = gcs_bucket
        self.gcs_prefix = gcs_prefix
        self.project_id = project_id

        # Validate storage type
        if storage_type not in ["local", "gcs", "hybrid"]:
            raise ValueError("storage_type must be 'local', 'gcs', or 'hybrid'")

        # For local storage
        if storage_type in ["local", "hybrid"]:
            if not base_data_dir or not base_index_dir:
                raise ValueError(
                    "base_data_dir and base_index_dir are required for local storage"
                )

            self.base_data_dir = Path(base_data_dir)
            self.base_index_dir = Path(base_index_dir)

            # Create base directories if they don't exist
            self.base_data_dir.mkdir(parents=True, exist_ok=True)
            self.base_index_dir.mkdir(parents=True, exist_ok=True)

            # Create raw/ directory if it doesn't exist
            self.raw_dir = self.base_data_dir / "raw"
            self.raw_dir.mkdir(exist_ok=True)

            # Check and create version directories
            self._initialize_version_directories()

        # For GCS storage
        if storage_type in ["gcs", "hybrid"]:
            if not gcs_bucket:
                raise ValueError("gcs_bucket is required for GCS storage")

            # Validate GCS credentials
            self._validate_gcs_setup()

    def _validate_gcs_setup(self) -> None:
        """
        Validates the GCS setup.
        """
        try:
            from google.auth.exceptions import DefaultCredentialsError
            from google.cloud import storage  # type: ignore

            # Check credentials
            try:
                client = storage.Client(project=self.project_id)
                # Test bucket access
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
        Creates a symlink with error handling.

        Parameters
        ----------
        target : str
            The target of the symlink.
        link_path : str
            The path where the symlink will be created.

        Returns
        -------
        bool
            True if successfully created, False otherwise.
        """
        try:
            # Remove existing symlink if it exists
            if os.path.exists(link_path):
                if os.path.islink(link_path):
                    os.unlink(link_path)
                else:
                    os.remove(link_path)

            # Create new symlink
            os.symlink(target, link_path, target_is_directory=True)
            return True
        except OSError as e:
            logger.warning(f"Could not create symlink {link_path} -> {target}: {e}")
            # On Windows or systems that don't support symlinks, copy instead
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
        """
        Initializes version directories if they don't exist and ensures 'latest' symlink is set.
        Also initializes corresponding index directory structure.
        """
        # Check if any version directories exist
        version_dirs = [
            d for d in self.raw_dir.iterdir() if d.is_dir() and d.name.startswith("v")
        ]

        # If no version directories exist, create v1.0
        if not version_dirs:
            (self.raw_dir / "v1.0").mkdir(exist_ok=True)
            # Create symlink for latest
            latest_link = self.raw_dir / "latest"
            if self._create_symlink("v1.0", str(latest_link)):
                logger.info(
                    "Created initial version directory v1.0 and set it as 'latest'"
                )
            else:
                logger.error("Failed to create 'latest' symlink")

        # If 'latest' symlink doesn't exist, create it and point to the latest version
        latest_link = self.raw_dir / "latest"
        if not latest_link.exists():
            # Sort versions and select the latest one
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

        # Initialize corresponding index directory structure
        self._initialize_index_directories()

    def _initialize_index_directories(self) -> None:
        """
        Initializes index directory structure to match data version structure.
        Creates index directories for existing data versions and sets up symlinks.
        """
        try:
            # Get all available data versions
            data_versions = self.list_available_versions()
            
            if not data_versions:
                logger.warning("No data versions found, skipping index directory initialization")
                return
            
            # Create index directories for each data version
            for version in data_versions:
                index_version_dir = self.base_index_dir / version
                if not index_version_dir.exists():
                    index_version_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created index directory for version {version}: {index_version_dir}")
            
            # Create/update 'latest' symlink for index directory
            latest_data_version = data_versions[-1]  # Last in sorted list
            index_latest_link = self.base_index_dir / "latest"
            
            if self._create_symlink(latest_data_version, str(index_latest_link)):
                logger.info(f"Set index 'latest' to point to {latest_data_version}")
            else:
                logger.warning(f"Failed to create index 'latest' symlink to {latest_data_version}")
                
        except Exception as e:
            logger.warning(f"Failed to initialize index directories: {e}")

    def get_data_version_path(self, version: Optional[str] = None) -> Union[Path, str]:
        """
        Retrieves the directory path for the specified data version.

        Parameters
        ----------
        version : Optional[str]
            The desired version (if None, uses the version set during object creation).

        Returns
        -------
        Union[Path, str]
            The directory path of the data version.
        """
        version = version or self.data_version

        if self.storage_type == "gcs":
            # For GCS
            return f"gs://{self.gcs_bucket}/{self.gcs_prefix}/raw/{version}"
        else:
            # For local storage
            version_dir = self.raw_dir / version
            if not version_dir.exists():
                raise ValueError(f"Data version '{version}' does not exist")
            return version_dir

    def get_index_path_for_version(
        self, version: Optional[str] = None
    ) -> Union[Path, str]:
        """
        Retrieves the index path for the specified data version.
        Automatically creates the index directory if it doesn't exist.

        Parameters
        ----------
        version : Optional[str]
            The desired version (if None, uses the version set during object creation).

        Returns
        -------
        Union[Path, str]
            The index path for the data version.

        Raises
        ------
        ValueError
            If the data version doesn't exist (for validation).
        """
        version = version or self.data_version

        if self.storage_type == "gcs":
            # For GCS
            return f"gs://{self.gcs_bucket}/{self.gcs_prefix}/indexes/{version}"
        else:
            # For local storage - Auto-create index directory structure
            index_dir = self.base_index_dir / version
            
            # Create the index directory if it doesn't exist
            if not index_dir.exists():
                logger.info(f"Creating index directory for version '{version}': {index_dir}")
                index_dir.mkdir(parents=True, exist_ok=True)
                
                # If this is the 'latest' version, also create/update the symlink
                if version == "latest":
                    # Find the actual latest data version to link to
                    try:
                        data_versions = self.list_available_versions()
                        if data_versions:
                            latest_data_version = data_versions[-1]
                            # Create a corresponding versioned index directory
                            versioned_index_dir = self.base_index_dir / latest_data_version
                            if not versioned_index_dir.exists():
                                versioned_index_dir.mkdir(parents=True, exist_ok=True)
                                logger.info(f"Created versioned index directory: {versioned_index_dir}")
                    except Exception as e:
                        logger.warning(f"Could not create versioned index directory: {e}")
                        
            return index_dir

    def list_available_versions(self) -> List[str]:
        """
        Lists all available data versions based on the storage type.

        Returns
        -------
        List[str]
            A list of available data version strings.
        """
        if self.storage_type == "gcs":
            return self._list_gcs_versions()
        else:
            return self._list_local_versions()

    def _list_local_versions(self) -> List[str]:
        """
        Lists available data versions in local storage.

        Returns
        -------
        List[str]
            A list of local data version strings.
        """
        versions = [
            d.name
            for d in self.raw_dir.iterdir()
            if d.is_dir() and d.name.startswith("v")
        ]
        versions.sort(key=lambda x: [int(n) for n in x.replace("v", "").split(".")])
        return versions

    def _list_gcs_versions(self) -> List[str]:
        """
        Lists available data versions in GCS.

        Returns
        -------
        List[str]
            A list of GCS data version strings.
        """
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.gcs_bucket)

            # Find prefix for raw data
            raw_prefix = f"{self.gcs_prefix}/raw/"

            # Find all versions
            versions = set()
            for blob in bucket.list_blobs(prefix=raw_prefix, delimiter="/"):
                if blob.name.endswith("/"):
                    # Extract version name
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
        Creates a new data version by copying specified source files.

        Parameters
        ----------
        source_files : List[str]
            A list of file paths to be included in the new version.
        increment_type : str
            Type of version increment ("major" for v2.0, "minor" for v1.1).

        Returns
        -------
        str
            The newly created version string (e.g., 'v1.2').

        Raises
        ------
        ValueError
            If `increment_type` is invalid or if `source_files` is empty.
        RuntimeError
            If there's an error during version creation.
        """
        if not source_files:
            raise ValueError("Source files list cannot be empty.")

        if increment_type not in ["major", "minor"]:
            raise ValueError("increment_type must be 'major' or 'minor'")

        # Determine the next version number
        current_versions = self.list_available_versions()
        if not current_versions:
            # If no versions exist, start from v1.0
            next_version = "v1.0"
        else:
            latest_version = current_versions[-1]
            major, minor = map(int, latest_version.replace("v", "").split("."))

            if increment_type == "major":
                next_version = f"v{major + 1}.0"
            else:  # minor
                next_version = f"v{major}.{minor + 1}"

        logger.info(f"Creating new data version: {next_version}")

        if self.storage_type == "gcs":
            self._create_gcs_version(next_version, source_files)
        else:
            self._create_local_version(next_version, source_files)

        return next_version

    def _create_local_version(self, new_version: str, source_files: List[str]) -> None:
        """
        Creates a new data version in local storage.
        Also creates corresponding index directory structure and updates symlinks.

        Parameters
        ----------
        new_version : str
            The new version string (e.g., 'v1.2').
        source_files : List[str]
            A list of file paths to copy to the new version.
        """
        # Create data version directory
        version_path = self.raw_dir / new_version
        version_path.mkdir(exist_ok=True)

        for src_file in source_files:
            dest_file = version_path / Path(src_file).name
            shutil.copy2(src_file, dest_file)
            logger.info(f"Copied {src_file} to {dest_file}")

        # Update 'latest' symlink to point to the new version
        latest_link = self.raw_dir / "latest"
        if self._create_symlink(new_version, str(latest_link)):
            logger.info(f"Set data 'latest' to point to {new_version}")
        else:
            logger.warning(f"Failed to update data 'latest' symlink to {new_version}")

        # Create corresponding index directory structure
        try:
            # Create versioned index directory
            index_version_dir = self.base_index_dir / new_version
            index_version_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created index directory for version {new_version}: {index_version_dir}")
            
            # Update/create 'latest' symlink for index directory
            index_latest_link = self.base_index_dir / "latest"
            if self._create_symlink(new_version, str(index_latest_link)):
                logger.info(f"Set index 'latest' to point to {new_version}")
            else:
                logger.warning(f"Failed to update index 'latest' symlink to {new_version}")
                
        except Exception as e:
            logger.warning(f"Failed to create index directory structure for {new_version}: {e}")

    def _create_gcs_version(self, new_version: str, source_files: List[str]) -> None:
        """
        Creates a new data version in GCS.

        Parameters
        ----------
        new_version : str
            The new version string (e.g., 'v1.2').
        source_files : List[str]
            A list of file paths to upload to the new version.
        """
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.gcs_bucket)

            # Upload files
            for src_file in source_files:
                src_path = Path(src_file)
                if src_path.exists():
                    # Create blob name
                    blob_name = f"{self.gcs_prefix}/raw/{new_version}/{src_path.name}"
                    blob = bucket.blob(blob_name)

                    # Upload file
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
        Creates a lineage record for an index, associating it with data version and parameters.

        Parameters
        ----------
        index_path : str
            The path to the FAISS index.
        data_version : str
            The data version used to create the index.
        files_used : List[str]
            A list of source files used to create the index.
        parameters : Dict[str, Any]
            A dictionary of parameters used during the ingestion process (e.g., chunking parameters).

        Returns
        -------
        Dict[str, Any]
            The created lineage record.
        """
        lineage_id = hashlib.md5(
            f"{index_path}-{data_version}-{json.dumps(files_used, sort_keys=True)}-{json.dumps(parameters, sort_keys=True)}".encode(
                "utf-8"
            )
        ).hexdigest()
        creation_time = datetime.now().isoformat()

        lineage_record = {
            "lineage_id": lineage_id,
            "index_path": index_path,
            "data_version": data_version,
            "files_used": files_used,
            "parameters": parameters,
            "created_at": creation_time,
        }

        if self.storage_type == "gcs":
            self._save_gcs_lineage(lineage_record, index_path)
        else:
            self._save_local_lineage(lineage_record, index_path)

        return lineage_record

    def _save_local_lineage(
        self, lineage_record: Dict[str, Any], index_path: str
    ) -> None:
        """
        Saves the lineage record to local storage.
        """
        lineage_file = Path(index_path).parent / "lineage.json"
        with open(lineage_file, "w", encoding="utf-8") as f:
            json.dump(lineage_record, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved lineage record to {lineage_file}")

    def _save_gcs_lineage(
        self, lineage_record: Dict[str, Any], index_path: str
    ) -> None:
        """
        Saves the lineage record to GCS.
        """
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.gcs_bucket)

            # Create blob name for lineage
            index_path_str = str(index_path)
            if index_path_str.startswith(f"gs://{self.gcs_bucket}/"):
                relative_path = index_path_str.replace(f"gs://{self.gcs_bucket}/", "")
            else:
                relative_path = index_path_str

            lineage_blob_name = f"{os.path.dirname(relative_path)}/lineage.json"
            blob = bucket.blob(lineage_blob_name)

            blob.upload_from_string(json.dumps(lineage_record, indent=4))
            logger.info(
                f"Saved lineage record to gs://{self.gcs_bucket}/{lineage_blob_name}"
            )

        except Exception as e:
            logger.error(f"Error saving GCS lineage: {e}")
            raise

    def get_lineage_for_index(self, index_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the lineage record for a given index path.

        Parameters
        ----------
        index_path : str
            The path to the FAISS index.

        Returns
        -------
        Optional[Dict[str, Any]]
            The lineage record, or None if not found.
        """
        if self.storage_type == "gcs":
            return self._get_gcs_lineage(index_path)
        else:
            return self._get_local_lineage(index_path)

    def _get_local_lineage(self, index_path: str) -> Optional[Dict[str, Any]]:
        """
        Reads the lineage from local storage.
        """
        lineage_file = Path(index_path).parent / "lineage.json"
        if lineage_file.exists():
            with open(lineage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _get_gcs_lineage(self, index_path: str) -> Optional[Dict[str, Any]]:
        """
        Reads the lineage from GCS.
        """
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.gcs_bucket)

            # Create blob name for lineage
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
        Downloads files for a specific data version from GCS to local storage.

        Parameters
        ----------
        data_version : str
            The data version to download.
        local_dir : Optional[str]
            The local directory to save the downloaded files. If None, a temporary directory or the raw data directory will be used.

        Returns
        -------
        List[str]
            A list of paths to the downloaded files.
        """
        if self.storage_type not in ["gcs", "hybrid"]:
            logger.warning(
                "Downloading from GCS is only supported for 'gcs' or 'hybrid' storage types. Skipping."
            )
            return []

        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.gcs_bucket)

            # Create destination directory
            if local_dir:
                target_dir = Path(local_dir)
            else:
                # For hybrid storage, use local path
                if self.storage_type == "hybrid":
                    target_dir = self.raw_dir / data_version
                else:
                    # For GCS-only storage, create a temporary directory
                    import tempfile

                    target_dir = Path(tempfile.mkdtemp(prefix="gcs_download_"))

            target_dir.mkdir(parents=True, exist_ok=True)

            # Find prefix for the version
            version_prefix = f"{self.gcs_prefix}/raw/{data_version}/"

            # Download files
            downloaded_files = []
            for blob in bucket.list_blobs(prefix=version_prefix):
                # Create local file path
                local_path = target_dir / Path(blob.name).name

                # Download file
                blob.download_to_filename(str(local_path))
                downloaded_files.append(str(local_path))
                logger.info(f"Downloaded {blob.name} to {local_path}")

            return downloaded_files

        except Exception as e:
            logger.error(f"Error downloading from GCS: {e}")
            return []

    def upload_to_gcs(self, local_files: List[str], data_version: str) -> List[str]:
        """
        Uploads files from local storage to GCS.

        Parameters
        ----------
        local_files : List[str]
            A list of local file paths to upload.
        data_version : str
            The data version to upload the files to.

        Returns
        -------
        List[str]
            A list of GCS paths of the uploaded files.
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
                    # Create blob name
                    blob_name = (
                        f"{self.gcs_prefix}/raw/{data_version}/{local_path.name}"
                    )
                    blob = bucket.blob(blob_name)

                    # Upload file
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
