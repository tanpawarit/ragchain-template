#!/usr/bin/env python
"""
Script for building FAISS index from the latest data version or a specified version
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to sys.path to enable importing from src
sys.path.append(str(Path(__file__).parent.parent))

from src.components.ingestion import DataIngestionPipeline
from src.utils.config.app_config import AppConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """
    Build FAISS index from the latest data version or a specified version
    """
    parser = argparse.ArgumentParser(description="Build FAISS index for RAG pipeline")
    parser.add_argument(
        "--model-config", 
        default="configs/model_config.yaml",
        help="Path to model config file (default: configs/model_config.yaml)"
    )
    parser.add_argument(
        "--env-config", 
        default="configs/environment.yaml",
        help="Path to environment config file (default: configs/environment.yaml)"
    )
    parser.add_argument(
        "--data-version", 
        default="latest",
        help="Data version to use (default: latest)"
    )
    parser.add_argument(
        "--gcs-path", 
        default=None,
        help="GCS path if using data from Google Cloud Storage (e.g., gs://bucket/data)"
    )
    parser.add_argument(
        "--chunk-size", 
        type=int, 
        default=1000,
        help="Chunk size when using RecursiveCharacterTextSplitter (default: 1000)"
    )
    parser.add_argument(
        "--chunk-overlap", 
        type=int, 
        default=200,
        help="Chunk overlap when using RecursiveCharacterTextSplitter (default: 200)"
    )
    parser.add_argument(
        "--use-semantic-chunking", 
        action="store_true",
        help="Use semantic chunking instead of character-based chunking"
    )
    args = parser.parse_args()

    # Check if config files exist
    if not os.path.exists(args.model_config):
        logger.error(f"Model config file not found: {args.model_config}")
        sys.exit(1)
    
    if not os.path.exists(args.env_config):
        logger.error(f"Environment config file not found: {args.env_config}")
        sys.exit(1)

    try:
        # Create pipeline
        logger.info(f"Creating DataIngestionPipeline for data version {args.data_version}")
        pipe = DataIngestionPipeline(
            model_config_path=args.model_config,
            environment_config_path=args.env_config,
            data_version=args.data_version,
            gcs_path=args.gcs_path,
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
        
        print(f"\n✅ FAISS index build process completed successfully for data version '{args.data_version}'.")
        print(f"   Index saved at: {pipe.faiss_index_path}")
        logger.info(f"FAISS index created successfully: {pipe.faiss_index_path}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# ===== Example =====
# สร้าง FAISS index
# ./scripts/build_faiss_index.py --data-version latest --use-semantic-chunking