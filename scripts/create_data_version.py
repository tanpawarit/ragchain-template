#!/usr/bin/env python

import argparse
import os
import sys
from pathlib import Path
from typing import List

# Add project root to sys.path to enable importing from src
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.utils.pipeline.data_version_manager import DataVersionManager

"""
Script for creating a new data version using DataVersionManager
"""

logger = get_logger(__name__)


def main() -> None:
    """
    Create a new data version from specified files
    """
    parser = argparse.ArgumentParser(
        description="Create a new data version for RAG pipeline"
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="List of files to copy to the new version (e.g., data/raw/*.txt)",
    )
    parser.add_argument(
        "--inc",
        choices=["major", "minor"],
        default="minor",
        help="Version increment type (major: v2.0, minor: v1.1)",
    )
    parser.add_argument(
        "--base-data-dir",
        default="data",
        help="Base directory for data (default: data)",
    )
    parser.add_argument(
        "--base-index-dir",
        default="artifacts",
        help="Base directory for index (default: artifacts)",
    )
    parser.add_argument(
        "--storage-type",
        choices=["local", "gcs", "hybrid"],
        default="local",
        help="Storage type (local, gcs, hybrid) - default: local",
    )
    parser.add_argument(
        "--gcs-bucket",
        default=None,
        help="GCS bucket name if using GCS storage",
    )
    parser.add_argument(
        "--gcs-prefix",
        default="data",
        help="GCS prefix for data (default: data)",
    )
    parser.add_argument(
        "--project-id",
        default=None,
        help="Google Cloud Project ID if using GCS",
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

    # Validate GCS parameters if needed
    if args.storage_type in ["gcs", "hybrid"]:
        if not args.gcs_bucket:
            logger.error("--gcs-bucket is required when using GCS storage")
            sys.exit(1)
        if not args.project_id:
            logger.error("--project-id is required when using GCS storage")
            sys.exit(1)

    # Create DataVersionManager
    try:
        if args.storage_type == "local":
            dvm = DataVersionManager(
                base_data_dir=args.base_data_dir,
                base_index_dir=args.base_index_dir,
                storage_type="local",
            )
        elif args.storage_type == "gcs":
            dvm = DataVersionManager(
                storage_type="gcs",
                gcs_bucket=args.gcs_bucket,
                gcs_prefix=args.gcs_prefix,
                project_id=args.project_id,
            )
        else:  # hybrid
            dvm = DataVersionManager(
                base_data_dir=args.base_data_dir,
                base_index_dir=args.base_index_dir,
                storage_type="hybrid",
                gcs_bucket=args.gcs_bucket,
                gcs_prefix=args.gcs_prefix,
                project_id=args.project_id,
            )

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


# ===== Examples =====
# Create a new data version (local storage)
# python scripts/create_data_version.py --files data/raw/*.txt

# Create a new data version (GCS storage)
# python scripts/create_data_version.py --files data/raw/*.txt --storage-type gcs --gcs-bucket my-bucket --project-id my-project

# Create a new data version (hybrid storage)
# python scripts/create_data_version.py --files data/raw/*.txt --storage-type hybrid --gcs-bucket my-bucket --project-id my-project
