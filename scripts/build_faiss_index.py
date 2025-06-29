#!/usr/bin/env python

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to sys.path to enable importing from src
sys.path.append(str(Path(__file__).parent.parent))

from src.components.ingestion import DataIngestionPipeline
from src.utils.logger import get_logger

"""
Script for building FAISS index from the latest data version or a specified version
"""

logger = get_logger(__name__)


def main() -> None:
    """
    Build FAISS index from the latest data version or a specified version
    """
    parser = argparse.ArgumentParser(description="Build FAISS index for RAG pipeline")
    parser.add_argument(
        "--model-config",
        default="configs/model_config.yaml",
        help="Path to model config file (default: configs/model_config.yaml)",
    )
    parser.add_argument(
        "--env-config",
        default="config.yaml",
        help="Path to environment config file (default: config.yaml)",
    )
    parser.add_argument(
        "--data-version", default="latest", help="Data version to use (default: latest)"
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
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Chunk size when using RecursiveCharacterTextSplitter (default: 1000)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Chunk overlap when using RecursiveCharacterTextSplitter (default: 200)",
    )
    parser.add_argument(
        "--use-semantic-chunking",
        action="store_true",
        help="Use semantic chunking instead of character-based chunking",
    )
    args = parser.parse_args()

    # Check if config files exist
    if not os.path.exists(args.model_config):
        logger.error(f"Model config file not found: {args.model_config}")
        sys.exit(1)

    if not os.path.exists(args.env_config):
        logger.error(f"Environment config file not found: {args.env_config}")
        sys.exit(1)

    # Validate GCS parameters if needed
    if args.storage_type in ["gcs", "hybrid"]:
        if not args.gcs_bucket:
            logger.error("--gcs-bucket is required when using GCS storage")
            sys.exit(1)
        if not args.project_id:
            logger.error("--project-id is required when using GCS storage")
            sys.exit(1)

    try:
        # Create pipeline
        logger.info(
            f"Creating DataIngestionPipeline for data version {args.data_version}"
        )
        pipe = DataIngestionPipeline(
            model_config_path=args.model_config,
            environment_config_path=args.env_config,
            data_version=args.data_version,
            storage_type=args.storage_type,
            gcs_bucket=args.gcs_bucket,
            gcs_prefix=args.gcs_prefix,
            project_id=args.project_id,
        )

        # Set parameters for chunking
        chunking_params: Dict[str, Any] = {
            "chunk_size": args.chunk_size,
            "chunk_overlap": args.chunk_overlap,
            "use_semantic_chunking": args.use_semantic_chunking,
        }

        # Run the entire pipeline with a single call
        logger.info("Starting the full data ingestion pipeline...")
        print(f"Building FAISS index for data version {args.data_version}...")

        pipe.run(chunking_params=chunking_params)

        print(
            f"\n✅ FAISS index build process completed successfully for data version '{args.data_version}'."
        )
        print(f"   Index saved at: {pipe.faiss_index_path}")
        logger.info(f"FAISS index created successfully: {pipe.faiss_index_path}")

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# ===== Examples =====
# Build FAISS index (local storage)
# python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking

# Build FAISS index (GCS storage)
# python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking --storage-type gcs --gcs-bucket my-bucket --project-id my-project

# Build FAISS index (hybrid storage)
# python scripts/build_faiss_index.py --data-version latest --use-semantic-chunking --storage-type hybrid --gcs-bucket my-bucket --project-id my-project
