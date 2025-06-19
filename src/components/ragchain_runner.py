from __future__ import annotations

"""High-level RAG chain runner.

It stitches together:
• Vectorstore retriever (built or loaded via DataIngestionPipeline)
• Prompt template from YAML config
• OpenAI ChatGPT endpoint (ChatOpenAI)

Use :class:`RAGChainRunner` programmatically or via the convenience
``python -m src.components.ragchain`` CLI (see ragchain.py).
"""

from typing import Optional

from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

from src.components.ingestion import DataIngestionPipeline
from src.utils.app_config import AppConfig
from src.utils.mlflow_tracker import MLflowTracker
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RAGChainRunner: 
    """Create and invoke a RAG chain with minimal boilerplate."""

    def __init__(
        self,
        cfg: AppConfig,
        *,
        mlflow_tracker: Optional[MLflowTracker] = None,
        vectorstore: Optional[FAISS] = None,
    ) -> None:
        self.cfg = cfg
        self.tracker = mlflow_tracker

        # ------------------------------------------------------------------
        # Vectorstore & retriever
        # ------------------------------------------------------------------
        if vectorstore is None:
            ingestion = DataIngestionPipeline(cfg, mlflow_tracker=mlflow_tracker)
            vectorstore = ingestion.get_or_create_vectorstore()
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
            openai_api_key=cfg.openai_token,
            temperature=0,
            max_tokens=1024
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
    def answer(self, question: str) -> str:
        """Return RAG answer for *question*."""
        reply: str = self.chain.invoke(question)
        if self.tracker:
            self.tracker.log_params({"question": question})
        return reply
