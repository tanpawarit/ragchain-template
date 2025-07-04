import os
import time
from typing import Any, Dict, List, Literal, Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import SecretStr

from src.utils.config.app_config import AppConfig
from src.utils.logger import get_logger
from src.utils.pipeline.mlflow_tracker import MLflowTracker

logger = get_logger(__name__)


class DataIngestionPipeline:
    """
    This class handles loading documents from files, chunking them into smaller pieces,
    generating embeddings, and creating a FAISS index for efficient retrieval.
    """

    def __init__(
        self,
        cfg: Optional[AppConfig] = None,
        *,
        model_config_path: Optional[str] = None,
        environment_config_path: Optional[str] = None,
        mlflow_tracker: Optional[MLflowTracker] = None,
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
        """
        # Configuration handling
        if cfg is None:
            if model_config_path is None or environment_config_path is None:
                raise ValueError("Either `cfg` or both config paths must be provided")
            cfg = AppConfig.from_files(model_config_path, environment_config_path)

        self.cfg = cfg
        self.mlflow_tracker = mlflow_tracker

        # Configuration properties
        self.embedding_model_name = cfg.embedding_model_name
        self.faiss_index_path = cfg.faiss_index_path
        self.data_folder = cfg.data_folder
        self.file_names = cfg.file_names
        self.openai_token = cfg.openai_token
        self.loaded_files: List[str] = []

        # Ensure directories exist
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
        Load documents from the specified files.

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

        for file_name in self.file_names:
            file_path = os.path.join(self.data_folder, file_name)

            try:
                if not os.path.exists(file_path):
                    logger.warning(f"File not found: {file_path}")
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                doc = Document(page_content=content, metadata={"source": file_path})
                documents.append(doc)
                loaded_files.append(file_path)
                logger.info(f"Loaded document from {file_path}")

            except Exception as e:
                logger.error(f"Error loading document {file_path}: {e}")
                raise

        self.loaded_files = loaded_files

        if not documents:
            raise FileNotFoundError("No documents were loaded")

        logger.info(f"Successfully loaded {len(documents)} documents")
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
        Chunk documents into smaller pieces for better retrieval performance.

        Parameters
        ----------
        documents : List[Document]
            The documents to chunk.
        chunk_size : int
            Maximum size of each chunk (for character-based chunking).
        chunk_overlap : int
            Overlap between chunks (for character-based chunking).
        use_semantic_chunking : bool
            Whether to use semantic chunking instead of character-based chunking.
        breakpoint_threshold_type : Literal
            Type of breakpoint threshold for semantic chunking.

        Returns
        -------
        List[Document]
            A list of chunked documents.

        Raises
        ------
        RuntimeError
            If chunking fails.
        """
        if not documents:
            raise ValueError("No documents provided for chunking")

        logger.info(f"Starting to chunk {len(documents)} documents")
        start_time = time.time()

        try:
            if use_semantic_chunking:
                logger.info("Using semantic chunking...")
                text_splitter = SemanticChunker(
                    embeddings=self.embeddings,
                    breakpoint_threshold_type=breakpoint_threshold_type,
                )
                chunks = text_splitter.split_documents(documents)
            else:
                logger.info("Using character-based chunking...")
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    length_function=len,
                )
                chunks = text_splitter.split_documents(documents)

            chunk_time = time.time() - start_time
            logger.info(
                f"Successfully chunked {len(documents)} documents into {len(chunks)} chunks in {chunk_time:.2f} seconds"
            )

            return chunks
        except Exception as e:
            logger.error(f"Error chunking documents: {e}")
            raise

    def create_and_save_vectorstore(self, chunks: List[Document]) -> None:
        """
        Create embeddings for document chunks and build a FAISS index.

        Parameters
        ----------
        chunks : List[Document]
            The document chunks to embed.

        Raises
        ------
        RuntimeError
            If embedding creation fails.
        """
        start_time = time.time()

        try:
            logger.info("Creating new FAISS index from provided chunks...")
            vectorstore = FAISS.from_documents(
                documents=chunks, embedding=self.embeddings
            )

            # Save the vectorstore
            vectorstore.save_local(self.faiss_index_path)

            logger.info(
                f"Successfully created and saved FAISS index with {len(chunks)} vectors to {self.faiss_index_path}"
            )
            logger.debug(
                f"Embedding and indexing completed in {time.time() - start_time:.2f} seconds"
            )

        except Exception as e:
            logger.error(f"Error creating embeddings or index: {e}")
            raise RuntimeError(f"Failed to create embeddings or index: {e}")

    def run(self, chunking_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete data ingestion pipeline: load, chunk, create index, and save.

        Args:
            chunking_params: A dictionary of parameters for the chunking process.

        Returns:
            Dict[str, Any]: A summary of the ingestion process.
        """
        start_time = time.time()
        logger.info("Starting data ingestion pipeline...")

        try:
            # Load documents
            documents = self.load_documents()
            logger.info(f"Loaded {len(documents)} documents.")

            # Chunk documents
            chunks = self.chunk_documents(documents, **chunking_params)
            logger.info(f"Created {len(chunks)} chunks.")

            # Create and save vectorstore
            self.create_and_save_vectorstore(chunks)
            logger.info(f"Created and saved vectorstore to {self.faiss_index_path}")

            # Log to MLflow if tracker is available
            if self.mlflow_tracker:
                self.mlflow_tracker.log_params(
                    {
                        "num_documents": len(documents),
                        "num_chunks": len(chunks),
                        "index_path": self.faiss_index_path,
                        "files_used": self.loaded_files,
                        **chunking_params,
                    }
                )

            pipeline_time = time.time() - start_time
            logger.info(
                f"Data ingestion pipeline completed in {pipeline_time:.2f} seconds"
            )

            return {
                "num_documents": len(documents),
                "num_chunks": len(chunks),
                "index_path": self.faiss_index_path,
                "files_used": self.loaded_files,
                "pipeline_time": pipeline_time,
                "parameters": chunking_params,
            }

        except Exception as e:
            logger.error(f"Data ingestion pipeline failed: {e}")
            raise
