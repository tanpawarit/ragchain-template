import os
import time
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# from src.utils.config_manager import get_config  # retained for back-compat
from src.utils.app_config import AppConfig
from src.utils.mlflow_tracker import MLflowTracker
from src.utils.logger import get_logger

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
        model_config_path : Optional[str]
            Path to the configuration file. If None, the default config path is used.
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
        self.faiss_index_path = cfg.faiss_index_path
        self.data_folder = cfg.data_folder
        self.file_names = cfg.file_names


        self.openai_token = cfg.openai_token
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.faiss_index_path), exist_ok=True)
        os.makedirs(self.data_folder, exist_ok=True)
        
        # Initialize embedding model
        try:
            self.embeddings = OpenAIEmbeddings(model=self.embedding_model_name, openai_api_key=self.openai_token)
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
                logger.info(f"Loaded document from {file_path}")
            except Exception as e:
                logger.error(f"Error loading document {file_path}: {e}")
                raise
        
        if not documents:
            logger.warning("No documents were loaded")
            
        return documents
    
    def chunk_documents(self, documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200, 
                       use_semantic_chunking: bool = True, breakpoint_threshold_type: str = "percentile") -> List[Document]:
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
        breakpoint_threshold_type : str
            The threshold type for semantic chunking. Options include "percentile", 
            "standard_deviation", "interquartile", "gradient".
            
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
                    breakpoint_threshold_type=breakpoint_threshold_type
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
            logger.debug(f"Chunking completed in {time.time() - start_time:.2f} seconds")
            # TODO: refactor
            # คุณสามารถวนลูปดูความยาวของแต่ละ chunk ได้
            for i, chunk in enumerate(chunks):
                # สำหรับ RecursiveCharacterTextSplitter, len(chunk.page_content) จะให้จำนวนตัวอักษร
                print(f"Chunk {i+1} length (characters): {len(chunk.page_content)}")

                # หากต้องการนับเป็น tokens (ซึ่ง LLM สนใจมากกว่า)
                # คุณจะต้องใช้ tokenizer ของโมเดลนั้นๆ
                # ตัวอย่างสำหรับ OpenAI (ต้องติดตั้ง tiktoken: pip install tiktoken)
                import tiktoken
                tokenizer = tiktoken.encoding_for_model(self.embedding_model_name) # หรือ gpt-3.5-turbo, gpt-4o
                num_tokens = len(tokenizer.encode(chunk.page_content))
                print(f"Chunk {i+1} length (tokens): {num_tokens}")

            # สถิติโดยรวม
            average_chunk_length_chars = sum(len(c.page_content) for c in chunks) / len(chunks)
            print(f"Average chunk length (characters): {average_chunk_length_chars:.2f}")
 
            average_chunk_length_tokens = sum(len(tokenizer.encode(c.page_content)) for c in chunks) / len(chunks)
            print(f"Average chunk length (tokens): {average_chunk_length_tokens:.2f}")

            logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error chunking documents: {e}")
            raise
    
    def load_vectorstore(self) -> FAISS:
        """
        Load an existing FAISS vectorstore if it exists.
        
        Returns
        -------
        FAISS
            The loaded FAISS vectorstore.
            
        Raises
        ------
        FileNotFoundError
            If the FAISS index does not exist.
        """
        faiss_index_dir = os.path.dirname(self.faiss_index_path)
        
        if not os.path.exists(self.faiss_index_path):
            raise FileNotFoundError(f"FAISS index not found at {self.faiss_index_path}")
            
        try:
            start_time = time.time()
            vectorstore = FAISS.load_local(faiss_index_dir, self.embeddings, allow_dangerous_deserialization=True)
            logger.info(f"Loaded existing FAISS index from {self.faiss_index_path}")
            logger.debug(f"Loading completed in {time.time() - start_time:.2f} seconds")
            return vectorstore
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            raise RuntimeError(f"Failed to load FAISS index: {e}")
    
    def create_embeddings_and_index(self, chunks: List[Document]) -> Tuple[List[str], FAISS]:
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
            faiss_index_dir = os.path.dirname(self.faiss_index_path)
            vectorstore = None
            
            # Check if FAISS index files already exist
            index_file = os.path.join(faiss_index_dir, "index.faiss")
            docstore_file = os.path.join(faiss_index_dir, "index.pkl")
            
            if os.path.exists(index_file) and os.path.exists(docstore_file):
                logger.info(f"Found existing FAISS index files at {faiss_index_dir}, loading instead of creating new one")
                # Load existing vectorstore
                vectorstore = FAISS.load_local(faiss_index_dir, self.embeddings, allow_dangerous_deserialization=True)
                logger.debug(f"Loaded existing index in {time.time() - start_time:.2f} seconds")
            else:
                # If no existing index, create a new one
                logger.info("No existing FAISS index found, creating new one")
                vectorstore = FAISS.from_documents(documents=chunks, embedding=self.embeddings)
                
                # Save the vectorstore locally
                vectorstore.save_local(faiss_index_dir)
                
                logger.info(f"Created and saved FAISS index with {len(chunks)} vectors using LangChain's FAISS")
                logger.debug(f"Embedding and indexing completed in {time.time() - start_time:.2f} seconds")
            
            # Extract text from chunks for return value consistency
            texts = [doc.page_content for doc in chunks]
            
            return texts, vectorstore
        except Exception as e:
            logger.error(f"Error creating embeddings or index: {e}")
            raise RuntimeError(f"Failed to create embeddings or index: {e}")
    
    def run_pipeline(self, chunk_size: int = 1000, chunk_overlap: int = 200, 
                   use_semantic_chunking: bool = True, breakpoint_threshold_type: str = "percentile") -> Dict[str, Any]:
        """
        Run the complete data ingestion pipeline.
        
        Parameters
        ----------
        chunk_size : int
            The size of each chunk in characters.
        chunk_overlap : int
            The overlap between chunks in characters.
        use_semantic_chunking : bool
            Whether to use semantic chunking instead of character-based chunking.
        breakpoint_threshold_type : str
            The threshold type for semantic chunking.
            
        Returns
        -------
        Dict[str, Any]
            A dictionary containing the results of the pipeline run, including the vectorstore.
        """
        start_time = time.time()
        
        try:
            # Load documents
            documents = self.load_documents()
            
            # Chunk documents
            chunks = self.chunk_documents(
                documents, 
                chunk_size=chunk_size, 
                chunk_overlap=chunk_overlap,
                use_semantic_chunking=use_semantic_chunking,
                breakpoint_threshold_type=breakpoint_threshold_type
            )
            
            # Create embeddings and index
            texts, vectorstore = self.create_embeddings_and_index(chunks)
            
            result: Dict[str, Any] = {
                "documents": documents,
                "chunks": chunks,
                "texts": texts,
                "vectorstore": vectorstore,
                "index_path": self.faiss_index_path,
                "processing_time": time.time() - start_time
            }
            
            # MLflow logging ---------------------------------------------------
            if self.mlflow_tracker:
                self.mlflow_tracker.log_params({
                    "embedding_model": self.embedding_model_name,
                    "semantic_chunking": use_semantic_chunking,
                    "breakpoint_type": breakpoint_threshold_type,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                })
                self.mlflow_tracker.log_metrics({
                    "num_documents": len(documents),
                    "num_chunks": len(chunks),
                    "ingest_time_sec": result["processing_time"],
                })
                self.mlflow_tracker.log_artifact(result["index_path"])  # faiss dir

            logger.info(
                f"Data ingestion pipeline completed in {result['processing_time']:.2f} seconds",
            )
            return result
        except Exception as e:
            logger.error(f"Error in data ingestion pipeline: {e}")
            raise


    def get_or_create_vectorstore(self, chunk_size: int = 1000, chunk_overlap: int = 200, 
                          use_semantic_chunking: bool = True, breakpoint_threshold_type: str = "percentile") -> FAISS:
        """
        Get an existing vectorstore if it exists, or create a new one by running the pipeline.
        
        This method provides a dynamic approach to vectorstore management:
        - If a FAISS index already exists at the configured path, it loads and returns it
        - If no index exists, it runs the full pipeline to create one
        
        Parameters
        ----------
        chunk_size : int
            The size of each chunk in characters (used only if creating a new index).
        chunk_overlap : int
            The overlap between chunks in characters (used only if creating a new index).
        use_semantic_chunking : bool
            Whether to use semantic chunking instead of character-based chunking (used only if creating a new index).
        breakpoint_threshold_type : str
            The threshold type for semantic chunking (used only if creating a new index).
            
        Returns
        -------
        FAISS
            The vectorstore, either loaded from existing index or newly created.
        """
        faiss_index_dir = os.path.dirname(self.faiss_index_path)
        
        # Check if FAISS index directory exists and contains the necessary files
        index_file = os.path.join(faiss_index_dir, "index.faiss")
        docstore_file = os.path.join(faiss_index_dir, "index.pkl")
        
        if os.path.exists(index_file) and os.path.exists(docstore_file):
            logger.info(f"Found existing FAISS index files at {faiss_index_dir}, loading them")
            try:
                start_time = time.time()
                vectorstore = FAISS.load_local(faiss_index_dir, self.embeddings, allow_dangerous_deserialization=True)
                logger.info(f"Successfully loaded existing FAISS index in {time.time() - start_time:.2f} seconds")
                return vectorstore
            except Exception as e:
                logger.warning(f"Failed to load existing FAISS index: {e}. Will create a new one.")
                # If loading fails, continue to create a new index
        else:
            logger.info(f"FAISS index files not found at {faiss_index_dir} or directory is empty")
        
        # If no index exists or loading failed, run the full pipeline
        logger.info("Running full pipeline to create a new FAISS index")
        result = self.run_pipeline(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            use_semantic_chunking=use_semantic_chunking,
            breakpoint_threshold_type=breakpoint_threshold_type
        )
        
        return result["vectorstore"]

# =========== example ===========
# ---------- กรณีเริ่มต้นใช้งานครั้งแรก (ยังไม่มี index) ----------
# from src.components.ingestion import DataIngestionPipeline
# # สร้าง pipeline
# pipeline = DataIngestionPipeline()
# # รัน pipeline เต็มรูปแบบ (โหลดเอกสาร, แบ่งชิ้น, สร้าง embeddings และ index)
# result = pipeline.run_pipeline()
# # ดึง vectorstore มาใช้
# vectorstore = result["vectorstore"]
# # ตัวอย่างการใช้งาน vectorstore เพื่อค้นหาเอกสารที่เกี่ยวข้อง
# docs = vectorstore.similarity_search("คำถามหรือคีย์เวิร์ดที่ต้องการค้นหา", k=4)

# ---------- กรณีมี index อยู่แล้ว และต้องการใช้งานอย่างรวดเร็ว ----------
# from src.components.ingestion import DataIngestionPipeline
# # สร้าง pipeline
# pipeline = DataIngestionPipeline()
# # โหลด vectorstore โดยตรง (เร็วกว่าเพราะไม่ต้องโหลดเอกสารและแบ่งชิ้น)
# try:
#     vectorstore = pipeline.load_vectorstore()
#     # ใช้งาน vectorstore
#     docs = vectorstore.similarity_search("คำถามหรือคีย์เวิร์ดที่ต้องการค้นหา", k=4)
# except FileNotFoundError:
#     print("ไม่พบ index ต้องสร้างใหม่ก่อน")
    
# ---------- วิธีใหม่ที่ dynamic กว่า (ใช้ get_or_create_vectorstore) ----------
# from src.components.ingestion import DataIngestionPipeline
# # สร้าง pipeline
# pipeline = DataIngestionPipeline()
# # ใช้เมธอด get_or_create_vectorstore ซึ่งจะโหลด vectorstore ถ้ามีอยู่แล้ว หรือสร้างใหม่ถ้ายังไม่มี
# vectorstore = pipeline.get_or_create_vectorstore()
# # ใช้งาน vectorstore ได้เลย โดยไม่ต้องกังวลว่า index จะมีอยู่หรือไม่
# docs = vectorstore.similarity_search("คำถามหรือคีย์เวิร์ดที่ต้องการค้นหา", k=4)