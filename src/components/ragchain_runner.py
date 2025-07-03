from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Optional

import mlflow
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from src.utils.config.app_config import AppConfig
from src.utils.logger import get_logger
from src.utils.pipeline.mlflow_tracker import MLflowTracker

"""High-level RAG chain runner with production-ready MLflow tracking.

It stitches together:
• Vectorstore retriever (built or loaded via DataIngestionPipeline)
• Prompt template from YAML config
• OpenAI ChatGPT endpoint (ChatOpenAI)
• Production-grade MLflow tracking with separate runs per query

Use :class:`RAGChainRunner` programmatically or via the convenience
``python -m src.components.ragchain`` CLI (see ragchain.py).
"""

logger = get_logger(__name__)


class RAGChainRunner:
    """Create and invoke a RAG chain with production-ready tracking."""

    def __init__(
        self,
        cfg: AppConfig,
        *,
        mlflow_tracker: Optional[MLflowTracker] = None,
        vectorstore: FAISS,
    ) -> None:
        self.cfg = cfg
        self.tracker = mlflow_tracker

        # ------------------------------------------------------------------
        # Vectorstore & retriever
        # ------------------------------------------------------------------

        self.vectorstore = vectorstore
        self.retriever = vectorstore.as_retriever(
            search_type=cfg.retriever_search_type,
            search_kwargs={"k": cfg.retriever_k_value},
        )

        # ------------------------------------------------------------------
        # LLM + Prompt
        # ------------------------------------------------------------------
        self.llm = ChatOpenAI(
            model=cfg.llm_model_name,  # Using the model specified in model_config.yaml
            api_key=SecretStr(cfg.openai_token),
            temperature=0,
        )
        prompt = ChatPromptTemplate.from_template(cfg.prompt_template)

        # ------------------------------------------------------------------
        # Chain definition
        # ------------------------------------------------------------------
        self.chain = (
            RunnableParallel(context=self.retriever, question=RunnablePassthrough())
            | prompt
            | self.llm
            | StrOutputParser()
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def answer(self, question: str, user_id: Optional[str] = None) -> str:
        """Return RAG answer for *question* with production-ready tracking.

        Args:
            question: The user's question
            user_id: Optional user identifier for tracking

        Returns:
            The generated answer
        """
        start_time = time.time()

        # Generate answer and capture intermediate results for logging
        retrieved_docs = []

        def capture_retriever_output(question_str: str) -> dict:
            docs = self.retriever.invoke(question_str)
            retrieved_docs.extend(docs)  # Store for logging
            return {"context": docs, "question": question_str}

        # Create chain with document capture
        chain_with_capture = (
            RunnableLambda(capture_retriever_output)
            | ChatPromptTemplate.from_template(self.cfg.prompt_template)
            | self.llm
            | StrOutputParser()
        )

        reply = chain_with_capture.invoke(question)

        # Calculate latency
        latency = time.time() - start_time

        # Production-ready MLflow tracking with separate run per query
        if self.tracker:
            self._log_query_to_mlflow(
                question=question,
                reply=reply,
                retrieved_docs=retrieved_docs,
                latency=latency,
                user_id=user_id,
            )

        return reply

    def _log_query_to_mlflow(
        self,
        question: str,
        reply: str,
        retrieved_docs: list,
        latency: float,
        user_id: Optional[str] = None,
    ) -> None:
        """Log query data to MLflow with production best practices.

        Creates a separate run for each query to enable proper tracking,
        debugging, and analysis of individual interactions.
        """
        try:
            # Create a new run for each query (Production Best Practice)
            run_name = f"rag_query_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"

            with mlflow.start_run(run_name=run_name, nested=True) as query_run:
                # Log query-specific parameters
                query_params = {
                    "question": question[:500],  # Truncate for MLflow compatibility
                    "question_length": len(question),
                    "user_id": user_id or "anonymous",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": getattr(self, "_session_id", "default"),
                }
                mlflow.log_params(query_params)

                # Log model configuration
                mlflow.log_params(
                    {
                        "llm_model": self.cfg.llm_model_name,
                        "embedding_model": self.cfg.embedding_model_name,
                        "retriever_k": self.cfg.retriever_k_value,
                        "retriever_search_type": self.cfg.retriever_search_type,
                        "prompt_template_name": self.cfg.prompt_template_name,
                        "prompt_template_version": self.cfg.prompt_template_version
                        or "latest",
                    }
                )

                # Log performance metrics
                mlflow.log_metrics(
                    {
                        "latency_seconds": latency,
                        "num_retrieved_docs": len(retrieved_docs),
                        "answer_length": len(reply),
                        "avg_doc_length": sum(
                            len(doc.page_content) for doc in retrieved_docs
                        )
                        / max(len(retrieved_docs), 1),
                    }
                )

                # Log retrieved documents as artifacts (for debugging and analysis)
                if retrieved_docs:
                    docs_summary = [
                        {
                            "content": doc.page_content[:200] + "..."
                            if len(doc.page_content) > 200
                            else doc.page_content,
                            "metadata": doc.metadata,
                            "score": getattr(doc, "score", None),
                            "length": len(doc.page_content),
                        }
                        for doc in retrieved_docs
                    ]
                    mlflow.log_text(
                        json.dumps(docs_summary, indent=2, ensure_ascii=False),
                        "retrieved_docs.json",
                    )

                # Log the answer as artifact
                mlflow.log_text(reply, "answer.txt")

                # Log the full question-answer pair for analysis
                qa_pair = {
                    "question": question,
                    "answer": reply,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                }
                mlflow.log_text(
                    json.dumps(qa_pair, indent=2, ensure_ascii=False), "qa_pair.json"
                )

                logger.info(f"Logged query to MLflow run: {query_run.info.run_id}")

        except Exception as e:
            # Don't let MLflow errors break the main functionality
            logger.warning(f"Failed to log to MLflow: {e}")
            # Continue without MLflow logging

    def set_session_id(self, session_id: str) -> None:
        """Set session ID for tracking multiple queries in a session."""
        self._session_id = session_id
