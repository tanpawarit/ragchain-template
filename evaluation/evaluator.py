"""
Evaluation module for RAG systems.

This module provides a unified interface for evaluating RAG components
without complex dependencies or configurations.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from openai import OpenAI

logger = logging.getLogger(__name__)


class RAGEvaluator:
    """
    A unified evaluator for RAG systems.

    This class provides methods to evaluate:
    - Retrieval quality (precision, recall, relevance)
    - Generation quality (relevance, coherence, accuracy)
    - End-to-end system performance
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        evaluation_model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
    ):
        """
        Initialize the evaluator.

        Args:
            openai_api_key: OpenAI API key (uses environment variable if None)
            evaluation_model: Model for LLM-based evaluation
            embedding_model: Model for embedding-based similarity
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.evaluation_model = evaluation_model
        self.embedding_model = embedding_model

    def evaluate_retrieval(
        self,
        vectorstore: Any,
        test_data: List[Dict[str, Any]],
        k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Evaluate retrieval performance.

        Args:
            vectorstore: Vector store to evaluate
            test_data: List of test cases with 'question' and 'ideal_context'
            k: Number of documents to retrieve
            similarity_threshold: Threshold for considering documents relevant

        Returns:
            Dictionary with evaluation results
        """
        results = []

        for item in test_data:
            question = item["question"]
            ideal_contexts = item.get("ideal_context", [])

            # Retrieve documents
            retrieved_docs = vectorstore.similarity_search(question, k=k)
            retrieved_texts = [doc.page_content for doc in retrieved_docs]

            # Calculate similarity-based metrics
            relevance_scores = []
            for retrieved_text in retrieved_texts:
                max_similarity = 0
                for ideal_context in ideal_contexts:
                    similarity = self._calculate_similarity(
                        retrieved_text, ideal_context
                    )
                    max_similarity = max(max_similarity, similarity)
                relevance_scores.append(max_similarity)

            # Calculate metrics
            relevant_count = sum(
                1 for score in relevance_scores if score > similarity_threshold
            )
            precision = relevant_count / len(retrieved_texts) if retrieved_texts else 0
            recall = (
                min(relevant_count / len(ideal_contexts), 1.0) if ideal_contexts else 0
            )
            f1_score = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0
            )

            results.append(
                {
                    "question": question,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1_score,
                    "avg_relevance": np.mean(relevance_scores)
                    if relevance_scores
                    else 0,
                    "retrieved_count": len(retrieved_texts),
                }
            )

        # Calculate averages
        avg_precision = np.mean([r["precision"] for r in results])
        avg_recall = np.mean([r["recall"] for r in results])
        avg_f1 = np.mean([r["f1_score"] for r in results])
        avg_relevance = np.mean([r["avg_relevance"] for r in results])

        return {
            "results": results,
            "summary": {
                "avg_precision": avg_precision,
                "avg_recall": avg_recall,
                "avg_f1_score": avg_f1,
                "avg_relevance": avg_relevance,
                "total_queries": len(results),
            },
        }

    def evaluate_generation(
        self, test_data: List[Dict[str, Any]], generator_fn: Any
    ) -> Dict[str, Any]:
        """
        Evaluate generation quality.

        Args:
            test_data: List of test cases with 'question' and 'ideal_answer'
            generator_fn: Function that takes a question and returns an answer

        Returns:
            Dictionary with evaluation results
        """
        results = []

        for item in test_data:
            question = item["question"]
            ideal_answer = item.get("ideal_answer", "")

            # Generate answer
            generated_answer = generator_fn(question)

            # Evaluate using LLM
            evaluation = self._evaluate_answer_quality(
                question, generated_answer, ideal_answer
            )

            results.append(
                {
                    "question": question,
                    "generated_answer": generated_answer,
                    "ideal_answer": ideal_answer,
                    **evaluation,
                }
            )

        # Calculate averages
        metrics = ["relevance", "coherence", "accuracy", "overall_quality"]
        summary = {}
        for metric in metrics:
            scores = [r[metric] for r in results if metric in r]
            summary[f"avg_{metric}"] = np.mean(scores) if scores else 0

        summary["total_queries"] = len(results)

        return {"results": results, "summary": summary}

    def evaluate_rag_system(
        self, test_data: List[Dict[str, Any]], rag_system: Any
    ) -> Dict[str, Any]:
        """
        Evaluate end-to-end RAG system.

        Args:
            test_data: List of test cases with 'question' and 'ideal_answer'
            rag_system: RAG system with a query method or callable

        Returns:
            Dictionary with evaluation results
        """
        results = []

        for item in test_data:
            question = item["question"]
            ideal_answer = item.get("ideal_answer", "")

            # Get system response
            try:
                if hasattr(rag_system, "query"):
                    response = rag_system.query(question)
                else:
                    response = rag_system(question)

                # Extract answer and context
                if isinstance(response, dict):
                    answer = response.get("answer", "")
                    context = response.get("context", "")
                    sources = response.get("sources", [])
                else:
                    answer = str(response)
                    context = ""
                    sources = []

                # Evaluate the response
                evaluation = self._evaluate_rag_response(
                    question, answer, context, ideal_answer
                )

                results.append(
                    {
                        "question": question,
                        "answer": answer,
                        "context": context,
                        "sources": sources,
                        "ideal_answer": ideal_answer,
                        **evaluation,
                    }
                )

            except Exception as e:
                logger.error(f"Error evaluating question '{question}': {e}")
                results.append(
                    {
                        "question": question,
                        "error": str(e),
                        "answer_relevance": 0,
                        "context_relevance": 0,
                        "accuracy": 0,
                        "overall_quality": 0,
                    }
                )

        # Calculate averages
        metrics = [
            "answer_relevance",
            "context_relevance",
            "accuracy",
            "overall_quality",
        ]
        summary = {}
        for metric in metrics:
            scores = [
                r[metric]
                for r in results
                if metric in r and isinstance(r[metric], (int, float))
            ]
            summary[f"avg_{metric}"] = np.mean(scores) if scores else 0

        summary["total_queries"] = len(results)
        summary["successful_queries"] = len([r for r in results if "error" not in r])

        return {"results": results, "summary": summary}

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using embeddings."""
        try:
            # Get embeddings
            response = self.client.embeddings.create(
                model=self.embedding_model, input=[text1, text2]
            )

            embeddings = [item.embedding for item in response.data]

            # Calculate cosine similarity
            vec1 = np.array(embeddings[0])
            vec2 = np.array(embeddings[1])

            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)

        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    def _evaluate_answer_quality(
        self, question: str, answer: str, reference: str
    ) -> Dict[str, float]:
        """Evaluate answer quality using LLM."""
        prompt = f"""
        You are an expert evaluator. Please evaluate the following answer to a question.
        
        Question: {question}
        
        Generated Answer: {answer}
        
        Reference Answer: {reference}
        
        Please rate the answer on a scale of 1-10 for each criterion:
        1. Relevance: How well does the answer address the question?
        2. Coherence: How well-structured and clear is the answer?
        3. Accuracy: How accurate is the answer compared to the reference?
        4. Overall Quality: Overall quality considering all factors.
        
        Return only a JSON object with the scores:
        {{"relevance": <score>, "coherence": <score>, "accuracy": <score>, "overall_quality": <score>}}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.evaluation_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {
                    "relevance": 0,
                    "coherence": 0,
                    "accuracy": 0,
                    "overall_quality": 0,
                }

        except Exception as e:
            logger.error(f"Error in LLM evaluation: {e}")
            return {"relevance": 0, "coherence": 0, "accuracy": 0, "overall_quality": 0}

    def _evaluate_rag_response(
        self, question: str, answer: str, context: str, reference: str
    ) -> Dict[str, float]:
        """Evaluate RAG response quality using LLM."""
        prompt = f"""
        You are an expert evaluator for RAG systems. Please evaluate the following response.
        
        Question: {question}
        
        Retrieved Context: {context}
        
        Generated Answer: {answer}
        
        Reference Answer: {reference}
        
        Please rate on a scale of 1-10:
        1. Answer Relevance: How relevant is the answer to the question?
        2. Context Relevance: How relevant is the context to the question?
        3. Accuracy: How accurate is the answer compared to the reference?
        4. Overall Quality: Overall quality of the RAG response.
        
        Return only a JSON object:
        {{"answer_relevance": <score>, "context_relevance": <score>, "accuracy": <score>, "overall_quality": <score>}}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.evaluation_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {
                    "answer_relevance": 0,
                    "context_relevance": 0,
                    "accuracy": 0,
                    "overall_quality": 0,
                }

        except Exception as e:
            logger.error(f"Error in RAG evaluation: {e}")
            return {
                "answer_relevance": 0,
                "context_relevance": 0,
                "accuracy": 0,
                "overall_quality": 0,
            }

    def save_results(self, results: Dict[str, Any], output_path: str) -> None:
        """Save evaluation results to a JSON file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"Results saved to {path}")


def load_test_data(file_path: str) -> List[Dict[str, Any]]:
    """Load test data from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Quick evaluation functions
def quick_retrieval_eval(
    vectorstore, test_data_path: str, k: int = 5
) -> Dict[str, Any]:
    """Quick retrieval evaluation with minimal setup."""
    evaluator = RAGEvaluator()
    test_data = load_test_data(test_data_path)
    return evaluator.evaluate_retrieval(vectorstore, test_data, k=k)


def quick_generation_eval(generator_fn, test_data_path: str) -> Dict[str, Any]:
    """Quick generation evaluation with minimal setup."""
    evaluator = RAGEvaluator()
    test_data = load_test_data(test_data_path)
    return evaluator.evaluate_generation(test_data, generator_fn)


def quick_rag_eval(rag_system, test_data_path: str) -> Dict[str, Any]:
    """Quick end-to-end RAG evaluation with minimal setup."""
    evaluator = RAGEvaluator()
    test_data = load_test_data(test_data_path)
    return evaluator.evaluate_rag_system(test_data, rag_system)
