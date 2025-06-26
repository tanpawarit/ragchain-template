#!/usr/bin/env python
"""
Script for creating a new data version using DataVersionManager
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional

# Add project root to sys.path to enable importing from src
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.pipeline.data_version_manager import DataVersionManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """
    Create a new data version from specified files
    """
    parser = argparse.ArgumentParser(description="Create a new data version for RAG pipeline")
    parser.add_argument(
        "--files", 
        nargs="+", 
        required=True,
        help="List of files to copy to the new version (e.g., data/raw/*.txt)"
    )
    parser.add_argument(
        "--inc", 
        choices=["major", "minor"], 
        default="minor",
        help="Version increment type (major: v2.0, minor: v1.1)"
    )
    parser.add_argument(
        "--base-data-dir", 
        default="data",
        help="Base directory for data (default: data)"
    )
    parser.add_argument(
        "--base-index-dir", 
        default="artifacts",
        help="Base directory for index (default: artifacts)"
    )
    parser.add_argument(
        "--gcs-path", 
        default=None,
        help="GCS path if using data from Google Cloud Storage (e.g., gs://bucket/data)"
    )
    args = parser.parse_args()

    # Check if specified files exist
    missing_files: List[str] = []
    for file_path in args.files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"The following files were not found: {', '.join(missing_files)}")
        sys.exit(1)

    # Create DataVersionManager
    dvm = DataVersionManager(
        base_data_dir=args.base_data_dir, 
        base_index_dir=args.base_index_dir,
        gcs_path=args.gcs_path
    )
    
    try:
        # Create new version
        new_ver = dvm.create_new_version(args.files, increment_type=args.inc)
        logger.info(f"✅ Successfully created new data version {new_ver}")
        print(f"✅ Successfully created new data version {new_ver}")
        
        # Show list of available versions
        versions = dvm.list_available_versions()
        logger.info(f"All available versions: {', '.join(versions)}")
        print(f"All available versions: {', '.join(versions)}")
        
        # Show path of latest version
        latest_path = dvm.get_data_version_path("latest")
        print(f"Latest version path: {latest_path}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


# ===== Example =====
# Create a new data version
# ./scripts/create_data_version.py --files data/raw/*.txt
