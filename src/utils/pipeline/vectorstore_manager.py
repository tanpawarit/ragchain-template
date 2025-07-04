from __future__ import annotations

import os
import time
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from src.utils.config.app_config import AppConfig
from src.utils.logger import get_logger
from src.utils.pipeline.mlflow_tracker import MLflowTracker

logger = get_logger(__name__)


def load_vectorstore(
    cfg: AppConfig,
    mlflow_tracker: Optional[MLflowTracker] = None,
) -> FAISS:
    """Load a FAISS vectorstore from the configured path.

    Args:
        cfg: The application configuration.
        mlflow_tracker: Optional MLflow tracker for logging.

    Returns:
        The loaded FAISS vectorstore.

    Raises:
        FileNotFoundError: If the index does not exist.
    """
    faiss_index_path = cfg.faiss_index_path

    if not os.path.exists(faiss_index_path):
        raise FileNotFoundError(
            f"FAISS index not found at: {faiss_index_path}. "
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
        mlflow_tracker.log_params(
            {
                "vectorstore_load_time_seconds": f"{load_time:.2f}",
                "vectorstore_index_path": faiss_index_path,
            }
        )

    return vectorstore
