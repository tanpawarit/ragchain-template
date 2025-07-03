import os
import time
from typing import Any, Dict, List, Literal, Optional

import tiktoken
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import SecretStr

# from src.utils.config_manager import get_config  # retained for back-compat
from src.utils.config.app_config import AppConfig
from src.utils.logger import get_logger
from src.utils.pipeline.data_version_manager import DataVersionManager
from src.utils.pipeline.mlflow_tracker import MLflowTracker

logger = get_logger(__name__)


class DataIngestionPipeline:
    """
    This class handles loading documents from files, chunking them into smaller pieces,
    generating embeddings, and creating a FAISS index for efficient retrieval.

    It supports Data Versioning, Index Versioning, and Data Lineage via DataVersionManager.
    """

    def __init__(
        self,
        cfg: Optional[AppConfig] = None,
        *,
        model_config_path: Optional[str] = None,
        environment_config_path: Optional[str] = None,
        mlflow_tracker: Optional[MLflowTracker] = None,
        data_version: str = "latest",
        storage_type: str = "local",
        gcs_bucket: Optional[str] = None,
        gcs_prefix: str = "data",
        project_id: Optional[str] = None,
    ) -> None:
        """
        Initialize the data ingestion pipeline.

        Parameters
        ----------
        cfg : Optional[AppConfig]
            AppConfig object. If None, will be created from config paths.
        model_config_path : Optional[str]
            Path to the model configuration file. Required if cfg is None.
        environment_config_path : Optional[str]
            Path to the environment configuration file. Required if cfg is None.
        mlflow_tracker : Optional[MLflowTracker]
            MLflow tracker for logging experiments. If None, no logging will be performed.
        data_version : str
            The data version to use (e.g., 'v1.0', 'v1.1', 'latest')
        storage_type : str
            The type of storage to use ("local", "gcs", "hybrid")
        gcs_bucket : Optional[str]
            GCS bucket name (e.g., 'my-data-bucket')
        gcs_prefix : str
            Prefix for data in GCS (e.g., 'data')
        project_id : Optional[str]
            Google Cloud Project ID
        """
        # ------------------------------------------------------------------
        # Configuration handling
        # ------------------------------------------------------------------
        if cfg is None:
            if model_config_path is None or environment_config_path is None:
                raise ValueError("Either `cfg` or both config paths must be provided")
            cfg = AppConfig.from_files(model_config_path, environment_config_path)
        self.cfg = cfg
        self.mlflow_tracker = mlflow_tracker

        self.embedding_model_name = cfg.embedding_model_name
        self.base_faiss_index_path = cfg.faiss_index_path
        self.data_folder = cfg.data_folder
        self.file_names = cfg.file_names
        self.openai_token = cfg.openai_token

        # Create DataVersionManager
        self.data_version = data_version
        self.storage_type = storage_type

        if storage_type == "local":
            self.version_manager = DataVersionManager(
                base_data_dir=os.path.dirname(self.data_folder),
                base_index_dir=os.path.dirname(self.base_faiss_index_path),
                storage_type="local",
                data_version=data_version,
            )
        elif storage_type == "gcs":
            if not gcs_bucket or not project_id:
                raise ValueError(
                    "gcs_bucket and project_id are required for GCS storage"
                )
            self.version_manager = DataVersionManager(
                storage_type="gcs",
                gcs_bucket=gcs_bucket,
                gcs_prefix=gcs_prefix,
                project_id=project_id,
                data_version=data_version,
            )
        else:  # hybrid
            if not gcs_bucket or not project_id:
                raise ValueError(
                    "gcs_bucket and project_id are required for hybrid storage"
                )
            self.version_manager = DataVersionManager(
                base_data_dir=os.path.dirname(self.data_folder),
                base_index_dir=os.path.dirname(self.base_faiss_index_path),
                storage_type="hybrid",
                gcs_bucket=gcs_bucket,
                gcs_prefix=gcs_prefix,
                project_id=project_id,
                data_version=data_version,
            )

        # Set index path based on data version
        index_dir = self.version_manager.get_index_path_for_version(data_version)
        if isinstance(index_dir, str):
            # For GCS storage
            self.faiss_index_path = f"{index_dir}/faiss_product_index"
        else:
            # For local storage
            self.faiss_index_path = str(
                index_dir / os.path.basename(self.base_faiss_index_path)
            )

        # Ensure directories exist (for local storage)
        if storage_type in ["local", "hybrid"]:
            os.makedirs(os.path.dirname(self.faiss_index_path), exist_ok=True)
            os.makedirs(self.data_folder, exist_ok=True)

        # Initialize embedding model
        try:
            self.embeddings = OpenAIEmbeddings(
                model=self.embedding_model_name, api_key=SecretStr(self.openai_token)
            )
            logger.info(f"Initialized embedding model: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise

    def load_documents(self) -> List[Document]:
        """
        Load documents from the specified files using the current data version.

        Returns
        -------
        List[Document]
            A list of loaded documents.

        Raises
        ------
        FileNotFoundError
            If any of the specified files cannot be found.
        """
        documents: List[Document] = []
        loaded_files: List[str] = []

        # Retrieve the directory path for the desired data version
        version_dir = self.version_manager.get_data_version_path(self.data_version)

        # If using GCS and data needs to be downloaded
        if self.storage_type == "gcs":
            downloaded_files = self.version_manager.download_from_gcs(self.data_version)
            if downloaded_files:
                # Use downloaded files
                for file_path in downloaded_files:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        doc = Document(
                            page_content=content, metadata={"source": file_path}
                        )
                        documents.append(doc)
                        loaded_files.append(file_path)
                        logger.info(
                            f"Loaded document from {file_path} (downloaded from GCS)"
                        )
                    except Exception as e:
                        logger.error(f"Error loading document {file_path}: {e}")
                        raise
        else:
            # Use local files
            for file_name in self.file_names:
                if isinstance(version_dir, str):
                    # For GCS storage
                    file_path = f"{version_dir}/{file_name}"
                else:
                    # For local storage
                    file_path = str(version_dir / file_name)

                try:
                    if not os.path.exists(file_path):
                        logger.warning(
                            f"File not found in version {self.data_version}: {file_path}"
                        )
                        continue

                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    doc = Document(page_content=content, metadata={"source": file_path})
                    documents.append(doc)
                    loaded_files.append(file_path)
                    logger.info(
                        f"Loaded document from {file_path} (version {self.data_version})"
                    )
                except Exception as e:
                    logger.error(f"Error loading document {file_path}: {e}")
                    raise

        if not documents:
            logger.warning(f"No documents were loaded for version {self.data_version}")

        # Store the list of loaded files for lineage creation
        self.loaded_files = loaded_files

        return documents

    def chunk_documents(
        self,
        documents: List[Document],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        use_semantic_chunking: bool = True,
        breakpoint_threshold_type: Literal[
            "percentile", "standard_deviation", "interquartile", "gradient"
        ] = "percentile",
    ) -> List[Document]:
        """
        Split documents into smaller chunks for processing.

        Parameters
        ----------
        documents : List[Document]
            The documents to chunk.
        chunk_size : int
            The size of each chunk in characters (used only with RecursiveCharacterTextSplitter).
        chunk_overlap : int
            The overlap between chunks in characters (used only with RecursiveCharacterTextSplitter).
        use_semantic_chunking : bool
            Whether to use semantic chunking instead of character-based chunking.
        breakpoint_threshold_type : Literal["percentile", "standard_deviation", "interquartile", "gradient"]
            The threshold type for semantic chunking.

        Returns
        -------
        List[Document]
            A list of document chunks.
        """
        start_time = time.time()

        try:
            if use_semantic_chunking:
                text_splitter = SemanticChunker(
                    embeddings=self.embeddings,
                    breakpoint_threshold_type=breakpoint_threshold_type,
                )
            else:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    length_function=len,
                    is_separator_regex=False,
                )

            chunks = text_splitter.split_documents(documents)

            logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
            logger.debug(
                f"Chunking completed in {time.time() - start_time:.2f} seconds"
            )

            tokenizer = tiktoken.encoding_for_model(
                self.embedding_model_name
            )  # e.g., gpt-3.5-turbo, gpt-4o

            total_chars = sum(len(c.page_content) for c in chunks)
            total_tokens = sum(len(tokenizer.encode(c.page_content)) for c in chunks)

            average_chunk_length_chars = total_chars / len(chunks)
            average_chunk_length_tokens = total_tokens / len(chunks)

            logger.info("Chunking statistics:")
            logger.info(f"  Total chunks: {len(chunks)}")
            logger.info(
                f"  Average chunk length (characters): {average_chunk_length_chars:.2f}"
            )
            logger.info(
                f"  Average chunk length (tokens): {average_chunk_length_tokens:.2f}"
            )

            # Log details of each chunk in debug mode only
            for i, chunk in enumerate(chunks):
                char_count = len(chunk.page_content)
                token_count = len(tokenizer.encode(chunk.page_content))
                logger.debug(f"Chunk {i + 1}: {char_count} chars, {token_count} tokens")

            logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error chunking documents: {e}")
            raise

    def create_and_save_vectorstore(self, chunks: List[Document]) -> None:
        """
        Create embeddings for document chunks and build a FAISS index using LangChain's FAISS implementation.
        If an index already exists at the specified path, it will be loaded instead of creating a new one.

        Parameters
        ----------
        chunks : List[Document]
            The document chunks to embed.

        Returns
        -------
        Tuple[List[str], FAISS]
            A tuple containing the document contents and the FAISS vectorstore.

        Raises
        ------
        RuntimeError
            If embedding creation fails.
        """
        start_time = time.time()

        try:
            faiss_index_dir = self.faiss_index_path

            # This method's responsibility is to create and save the index.
            # It will overwrite any existing index at the location.
            logger.info("Creating new FAISS index from provided chunks...")
            vectorstore = FAISS.from_documents(
                documents=chunks, embedding=self.embeddings
            )

            # Save the vectorstore locally to the correct directory
            vectorstore.save_local(faiss_index_dir)

            logger.info(
                f"Successfully created and saved new FAISS index with {len(chunks)} vectors to {faiss_index_dir}"
            )
            logger.debug(
                f"Embedding and indexing completed in {time.time() - start_time:.2f} seconds"
            )

            return
        except Exception as e:
            logger.error(f"Error creating embeddings or index: {e}")
            raise RuntimeError(f"Failed to create embeddings or index: {e}")

    def run(self, chunking_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete data ingestion pipeline: load, chunk, create index, and save.

        Args:
            chunking_params: A dictionary of parameters for the chunking process.

        Returns:
            Dict[str, Any]: The lineage record containing metadata about the ingestion process.
        """
        start_time = time.time()
        logger.info("Starting data ingestion pipeline...")
        try:
            documents = self.load_documents()
            logger.info(f"Loaded {len(documents)} documents.")

            chunks = self.chunk_documents(documents, **chunking_params)
            logger.info(f"Created {len(chunks)} chunks.")

            self.create_and_save_vectorstore(chunks)
            logger.info(f"Created and saved vectorstore to {self.faiss_index_path}")

            # Create and save lineage record
            lineage_record = self.version_manager.create_lineage_record(
                index_path=self.faiss_index_path,
                data_version=self.data_version,
                files_used=self.loaded_files,
                parameters=chunking_params,
            )
            logger.info(f"Created lineage record: {lineage_record['lineage_id']}")

            # Log data to MLflow (if available)
            if self.mlflow_tracker:
                # Log parameters and metrics
                self.mlflow_tracker.log_params(chunking_params)
                self.mlflow_tracker.log_metrics(
                    {
                        "num_documents": float(len(documents)),
                        "num_chunks": float(len(chunks)),
                        "ingest_time_sec": time.time() - start_time,
                    }
                )
                # Log data_version as a parameter
                self.mlflow_tracker.log_params({"data_version": self.data_version})

                # Log artifacts
                self.mlflow_tracker.log_artifact(self.faiss_index_path)

                # Log lineage file if it exists
                lineage_file = os.path.join(
                    os.path.dirname(self.faiss_index_path), "lineage.json"
                )
                if os.path.exists(lineage_file):
                    self.mlflow_tracker.log_artifact(lineage_file)

                logger.info("Logged artifacts and metrics to MLflow.")

            logger.info(
                f"Data ingestion pipeline completed in {time.time() - start_time:.2f} seconds for data version {self.data_version}"
            )

            return lineage_record

        except Exception as e:
            logger.error(f"Error during data ingestion pipeline: {e}")
            raise
