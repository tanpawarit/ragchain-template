from typing import Any, List, Optional, Set
import logging

import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

"""
Custom evaluation metrics for the Typhoon RAG system.

This module contains implementations of various evaluation metrics
for retrieval, generation, and end-to-end RAG evaluation.
"""


class RetrievalMetrics:
    """
    Class for computing retrieval-specific evaluation metrics.
    """

    @staticmethod
    def precision_at_k(
        relevant_docs: Set[str], retrieved_docs: List[str], k: Optional[int] = None
    ) -> float:
        """
        Calculate precision@k for retrieval evaluation.

        Parameters:
        -----------
        relevant_docs: Set[str]
            Set of relevant document IDs
        retrieved_docs: List[str]
            List of retrieved document IDs
        k: Optional[int]
            Number of documents to consider (default: all retrieved)

        Returns:
        --------
        float
            Precision@k score
        """
        if not retrieved_docs:
            return 0.0

        k = k or len(retrieved_docs)
        retrieved_k = retrieved_docs[:k]

        if not retrieved_k:
            return 0.0

        # Count relevant documents in the top-k
        relevant_count = sum(1 for doc in retrieved_k if doc in relevant_docs)

        return relevant_count / len(retrieved_k)

    @staticmethod
    def recall_at_k(
        relevant_docs: Set[str], retrieved_docs: List[str], k: Optional[int] = None
    ) -> float:
        """
        Calculate recall@k for retrieval evaluation.

        Parameters:
        -----------
        relevant_docs: Set[str]
            Set of relevant document IDs
        retrieved_docs: List[str]
            List of retrieved document IDs
        k: Optional[int]
            Number of documents to consider (default: all retrieved)

        Returns:
        --------
        float
            Recall@k score
        """
        if not relevant_docs:
            return 1.0  # Perfect recall if there are no relevant docs

        k = k or len(retrieved_docs)
        retrieved_k = retrieved_docs[:k]

        if not retrieved_k:
            return 0.0

        # Count relevant documents in the top-k
        relevant_count = sum(1 for doc in retrieved_k if doc in relevant_docs)

        return relevant_count / len(relevant_docs)

    @staticmethod
    def f1_at_k(
        relevant_docs: Set[str], retrieved_docs: List[str], k: Optional[int] = None
    ) -> float:
        """
        Calculate F1@k for retrieval evaluation.

        Parameters:
        -----------
        relevant_docs: Set[str]
            Set of relevant document IDs
        retrieved_docs: List[str]
            List of retrieved document IDs
        k: Optional[int]
            Number of documents to consider (default: all retrieved)

        Returns:
        --------
        float
            F1@k score
        """
        precision = RetrievalMetrics.precision_at_k(relevant_docs, retrieved_docs, k)
        recall = RetrievalMetrics.recall_at_k(relevant_docs, retrieved_docs, k)

        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)

    @staticmethod
    def mean_reciprocal_rank(
        relevant_docs: Set[str], retrieved_docs: List[str]
    ) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR) for retrieval evaluation.

        Parameters:
        -----------
        relevant_docs: Set[str]
            Set of relevant document IDs
        retrieved_docs: List[str]
            List of retrieved document IDs

        Returns:
        --------
        float
            MRR score
        """
        if not relevant_docs or not retrieved_docs:
            return 0.0

        # Find the rank of the first relevant document
        for i, doc in enumerate(retrieved_docs):
            if doc in relevant_docs:
                return 1.0 / (i + 1)

        return 0.0


class SemanticSimilarityMetrics:
    """
    Class for computing semantic similarity-based evaluation metrics.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the semantic similarity metrics calculator.

        Parameters:
        -----------
        model_name: str
            Name of the sentence transformer model to use
        """
        self.model = SentenceTransformer(model_name)

    def cosine_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.

        Parameters:
        -----------
        text1: str
            First text
        text2: str
            Second text

        Returns:
        --------
        float
            Cosine similarity score (0-1)
        """
        # Encode texts
        embedding1 = self.model.encode(text1, convert_to_tensor=True)
        embedding2 = self.model.encode(text2, convert_to_tensor=True)

        # Calculate cosine similarity
        cos_sim = torch.nn.functional.cosine_similarity(
            embedding1.unsqueeze(0), embedding2.unsqueeze(0)
        )

        return cos_sim.item()

    def semantic_precision(
        self, reference: str, generated: str, threshold: float = 0.7
    ) -> float:
        """
        Calculate semantic precision between reference and generated text.

        Parameters:
        -----------
        reference: str
            Reference text
        generated: str
            Generated text
        threshold: float
            Similarity threshold for considering a match

        Returns:
        --------
        float
            Semantic precision score (0-1)
        """
        # Split texts into sentences
        ref_sentences = [s.strip() for s in reference.split(".") if s.strip()]
        gen_sentences = [s.strip() for s in generated.split(".") if s.strip()]

        if not gen_sentences:
            return 0.0

        # Calculate similarity for each generated sentence
        matches = 0
        for gen_sent in gen_sentences:
            # Find max similarity with any reference sentence
            max_sim = max(
                (
                    self.cosine_similarity(gen_sent, ref_sent)
                    for ref_sent in ref_sentences
                ),
                default=0.0,
            )

            if max_sim >= threshold:
                matches += 1

        return matches / len(gen_sentences)

    def semantic_recall(
        self, reference: str, generated: str, threshold: float = 0.7
    ) -> float:
        """
        Calculate semantic recall between reference and generated text.

        Parameters:
        -----------
        reference: str
            Reference text
        generated: str
            Generated text
        threshold: float
            Similarity threshold for considering a match

        Returns:
        --------
        float
            Semantic recall score (0-1)
        """
        # Split texts into sentences
        ref_sentences = [s.strip() for s in reference.split(".") if s.strip()]
        gen_sentences = [s.strip() for s in generated.split(".") if s.strip()]

        if not ref_sentences:
            return 1.0  # Perfect recall if there's no reference

        # Calculate similarity for each reference sentence
        matches = 0
        for ref_sent in ref_sentences:
            # Find max similarity with any generated sentence
            max_sim = max(
                (
                    self.cosine_similarity(ref_sent, gen_sent)
                    for gen_sent in gen_sentences
                ),
                default=0.0,
            )

            if max_sim >= threshold:
                matches += 1

        return matches / len(ref_sentences)


class HallucinationMetrics:
    """
    Class for computing hallucination-related evaluation metrics.
    """

    @staticmethod
    def context_consistency(
        answer: str, context: str, similarity_metric: Optional[Any] = None
    ) -> float:
        """
        Measure the consistency between the answer and the provided context.
        Lower scores indicate potential hallucinations.

        Parameters:
        -----------
        answer: str
            Generated answer
        context: str
            Retrieved context
        similarity_metric: Optional[Any]
            Function or object to calculate similarity (default: SemanticSimilarityMetrics)

        Returns:
        --------
        float
            Consistency score (0-1)
        """
        if not answer or not context:
            return 0.0

        # Use default similarity metric if none provided
        if similarity_metric is None:
            similarity_metric = SemanticSimilarityMetrics()

        if hasattr(similarity_metric, "cosine_similarity"):
            return similarity_metric.cosine_similarity(answer, context)
        elif callable(similarity_metric):
            return similarity_metric(answer, context)
        else:
            raise ValueError("Invalid similarity metric provided")

    @staticmethod
    def fact_verification(
        answer: str, context: str, openai_client: Any, model: str = "gpt-3.5-turbo"
    ) -> float:
        """
        Verify factual consistency between answer and context using an LLM.

        Parameters:
        -----------
        answer: str
            Generated answer
        context: str
            Retrieved context
        openai_client: Any
            OpenAI client for API calls
        model: str
            Model to use for verification

        Returns:
        --------
        float
            Factual consistency score (0-1)
        """
        prompt = f"""
        You are an expert fact-checker. Your task is to verify if the following answer is factually consistent with the provided context.
        
        Context: {context}
        
        Answer: {answer}
        
        Rate the factual consistency on a scale from 0 to 1, where:
        - 0 means the answer contains information completely unsupported by the context (hallucination)
        - 0.5 means the answer contains some information supported by the context and some that isn't
        - 1 means the answer is completely factually consistent with the context
        
        Provide only a single number as your response, nothing else.
        """

        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
            )

            score_text = response.choices[0].message.content.strip()

            # Extract numeric score
            try:
                score = float(score_text)
                return max(0.0, min(1.0, score))  # Clamp to [0, 1]
            except ValueError:
                logger.error("Failed to parse score from response: %s", score_text)
                return 0.0

        except Exception as e:
            logger.error("Error in fact verification: %s", e)
            return 0.0
