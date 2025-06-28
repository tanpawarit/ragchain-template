from __future__ import annotations

import os
import time
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from src.utils.config.app_config import AppConfig
from src.utils.logger import get_logger
from src.utils.pipeline.data_version_manager import DataVersionManager
from src.utils.pipeline.mlflow_tracker import MLflowTracker

logger = get_logger(__name__)


def load_vectorstore(
    cfg: AppConfig,
    data_version: str = "latest",
    mlflow_tracker: Optional[MLflowTracker] = None,
) -> FAISS:
    """Load a FAISS vectorstore from the specified data version.

    Args:
        cfg: The application configuration.
        data_version: The data version to load (e.g., 'v1.0.0', 'latest').
        mlflow_tracker: Optional MLflow tracker for logging.

    Returns:
        The loaded FAISS vectorstore.

    Raises:
        FileNotFoundError: If the index for the specified version does not exist.
    """
    dvm = DataVersionManager(
        base_data_dir=os.path.dirname(cfg.data_folder),
        base_index_dir=os.path.dirname(cfg.faiss_index_path),
    )

    # Get index path and handle both Path and str types
    index_dir = dvm.get_index_path_for_version(data_version)
    if isinstance(index_dir, str):
        # For GCS storage, construct the full path
        faiss_index_path = f"{index_dir}/faiss_product_index"
    else:
        # For local storage, use Path operations
        faiss_index_path = str(index_dir / "faiss_product_index")

    if not os.path.exists(faiss_index_path):
        raise FileNotFoundError(
            f"FAISS index not found for data version '{data_version}'. "
            f"Looked in: {faiss_index_path}. "
            f"Please run the ingestion pipeline first (e.g., 'scripts/build_faiss_index.py')."
        )

    logger.info(f"Loading FAISS index from: {faiss_index_path}")
    start_time = time.time()

    embeddings = OpenAIEmbeddings(
        model=cfg.embedding_model_name, api_key=SecretStr(cfg.openai_token)
    )
    vectorstore = FAISS.load_local(
        str(faiss_index_path), embeddings, allow_dangerous_deserialization=True
    )

    load_time = time.time() - start_time
    logger.info(f"Successfully loaded vectorstore in {load_time:.2f} seconds.")

    if mlflow_tracker:
        try:
            lineage_info = dvm.get_lineage_for_index(str(faiss_index_path))
            if lineage_info:
                mlflow_tracker.log_params(
                    {
                        "vectorstore_load_time_seconds": f"{load_time:.2f}",
                        "vectorstore_data_version": lineage_info.get(
                            "data_version", "unknown"
                        ),
                        "vectorstore_creation_time": lineage_info.get(
                            "creation_time", "unknown"
                        ),
                    }
                )
                logger.info("Logged vectorstore lineage to MLflow.")
            else:
                mlflow_tracker.log_params(
                    {
                        "vectorstore_load_time_seconds": f"{load_time:.2f}",
                        "vectorstore_data_version": data_version,
                    }
                )
        except Exception as e:
            logger.warning(f"Could not log lineage info: {e}")
            mlflow_tracker.log_params(
                {
                    "vectorstore_load_time_seconds": f"{load_time:.2f}",
                    "vectorstore_data_version": data_version,
                }
            )

    return vectorstore
