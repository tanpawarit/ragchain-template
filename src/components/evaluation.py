from __future__ import annotations

"""Evaluation pipeline that wraps **DeepEval** and optionally logs to MLflow."""

from typing import List, Optional, Dict, Any

from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from src.utils.app_config import AppConfig
from src.utils.mlflow_tracker import MLflowTracker
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EvaluationPipeline: 
    """Run DeepEval evaluation on a given retriever / vectorstore."""

    def __init__(
        self,
        cfg: AppConfig,
        *,
        vectorstore: VectorStore,
        mlflow_tracker: Optional[MLflowTracker] = None,
    ) -> None:
        self.cfg = cfg
        self.vectorstore = vectorstore
        self.mlflow_tracker = mlflow_tracker

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(
        self,
        *,
        questions: List[str],
        ground_truth_docs: List[Document],
    ) -> Dict[str, Any]:
        """Execute DeepEval retrieval evaluation.

        Parameters
        ----------
        questions : list[str]
            List of questions to query the retriever.
        ground_truth_docs : list[Document]
            Expected relevant documents for each question.
        """
        if len(questions) != len(ground_truth_docs):
            raise ValueError("questions and ground_truth_docs must be the same length")

        metric = AnswerRelevancyMetric()

        scores: List[float] = []
        for q, gt in zip(questions, ground_truth_docs):
            retrieved = self.vectorstore.similarity_search(q, k=self.cfg.retriever_k_value)
            score = evaluate(
                candidate_docs=retrieved,
                reference_docs=[gt],
                metrics=[metric],
            )[metric.name]
            scores.append(score)
            logger.info("Question '%s' → score %.3f", q, score)

        mean_score = sum(scores) / len(scores)

        if self.mlflow_tracker:
            self.mlflow_tracker.log_metrics({"deepeval_mean_answer_relevancy": mean_score})

        return {"scores": scores, "mean_score": mean_score}
