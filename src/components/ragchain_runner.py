from __future__ import annotations

from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from src.utils.config.app_config import AppConfig
from src.utils.logger import get_logger
from src.utils.pipeline.mlflow_tracker import MLflowTracker

"""High-level RAG chain runner.

It stitches together:
• Vectorstore retriever (built or loaded via DataIngestionPipeline)
• Prompt template from YAML config
• OpenAI ChatGPT endpoint (ChatOpenAI)

Use :class:`RAGChainRunner` programmatically or via the convenience
``python -m src.components.ragchain`` CLI (see ragchain.py).
"""

logger = get_logger(__name__)


class RAGChainRunner:
    """Create and invoke a RAG chain with minimal boilerplate."""

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
        """Return RAG answer for *question*.

        Args:
            question: The user's question
            user_id: Optional user identifier for tracking

        Returns:
            The generated answer
        """
        import time

        start_time = time.time()

        # ดึงเอกสารที่เกี่ยวข้อง (สำหรับการบันทึก)
        retrieved_docs = self.retriever.get_relevant_documents(question)

        # สร้างคำตอบ
        reply: str = self.chain.invoke(question)

        # คำนวณเวลาที่ใช้
        latency = time.time() - start_time

        # บันทึกข้อมูลใน MLflow
        if self.tracker:
            # Only log essential data - save storage space
            params = {
                "question": question[
                    :200
                ],  # Store only first 200 characters of the question
            }

            # Add user ID if available
            if user_id:
                params["user_id"] = user_id

            self.tracker.log_params(params)

            # Log model and retriever data (only once per day)
            from datetime import datetime

            today = datetime.now().strftime("%Y-%m-%d")
            config_logged_key = f"config_logged_{today}"

            # Check if config has been logged today already
            import mlflow

            try:
                # Try to fetch runs that have logged config for today
                runs = mlflow.search_runs(
                    filter_string=f"params.{config_logged_key} = 'true'",
                    order_by=["start_time DESC"],
                    max_results=1,
                )
                config_logged_today = len(runs) > 0
            except Exception:
                config_logged_today = False

            # Log config data only for the first run of the day
            if not config_logged_today:
                self.tracker.log_params(
                    {
                        config_logged_key: "true",
                        "llm_model": self.cfg.llm_model_name,
                        "embedding_model": self.cfg.embedding_model_name,
                        "retriever_k": self.cfg.retriever_k_value,
                        "retriever_search_type": self.cfg.retriever_search_type,
                        "prompt_template_name": self.cfg.prompt_template_name,
                        "prompt_template_version": self.cfg.prompt_template_version
                        or "latest",
                    }
                )

            # Only log essential metrics
            self.tracker.log_metrics(
                {
                    "latency": latency,
                    "num_retrieved_docs": len(retrieved_docs),
                }
            )

        return reply
