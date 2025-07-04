#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to sys.path to enable importing from src
sys.path.append(str(Path(__file__).parent.parent))

from src.components.ingestion import DataIngestionPipeline
from src.utils.logger import get_logger, setup_logging

"""
Script for building FAISS index from configured data files
"""

# Setup logging
setup_logging()
logger = get_logger(__name__)


def main() -> int:
    """
    Build FAISS index from configured data files
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

    try:
        # Create pipeline
        logger.info("Creating DataIngestionPipeline")
        pipe = DataIngestionPipeline(
            model_config_path=args.model_config,
            environment_config_path=args.env_config,
        )

        # Set parameters for chunking
        chunking_params: Dict[str, Any] = {
            "chunk_size": args.chunk_size,
            "chunk_overlap": args.chunk_overlap,
            "use_semantic_chunking": args.use_semantic_chunking,
        }

        # Run the entire pipeline with a single call
        logger.info("Starting the full data ingestion pipeline...")
        logger.info("Building FAISS index...")

        result = pipe.run(chunking_params=chunking_params)

        logger.info("Successfully built FAISS index")
        logger.info("   Index saved at: %s", result["index_path"])
        logger.info("   Documents processed: %s", result["num_documents"])
        logger.info("   Chunks created: %s", result["num_chunks"])

    except Exception as e:
        logger.error("Error: %s", e)
        return 1

    return 0


if __name__ == "__main__":
    main()

# ===== Examples =====
# Build FAISS index with character-based chunking
# python scripts/build_faiss_index.py

# Build FAISS index with semantic chunking
# python scripts/build_faiss_index.py --use-semantic-chunking

# Build FAISS index with custom chunk settings
# python scripts/build_faiss_index.py --chunk-size 800 --chunk-overlap 150
