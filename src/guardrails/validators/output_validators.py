"""
Output validation guardrails.

This module contains validators that check system outputs before
they are returned to users.
"""

from typing import Any, Dict, List

from pydantic import Field

from src.guardrails.base import (
    BaseGuardrail,
    BaseGuardrailConfig,
    GuardrailResponse,
    GuardrailResult,
)
from src.utils.logger import get_logger
from src.utils.nlp_utils import calculate_similarity, get_nlp_processor

logger = get_logger(__name__)


class OutputLengthConfig(BaseGuardrailConfig):
    """Configuration for output length validator."""

    max_length: int = Field(
        default=2000, gt=0, description="Maximum allowed output length"
    )
    min_length: int = Field(
        default=5, ge=0, description="Minimum required output length"
    )


class OutputLengthValidator(BaseGuardrail):
    """
    Validates output length to ensure reasonable response sizes.
    """

    guardrail_name = "OutputLengthValidator"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.config_model = OutputLengthConfig(**config)
        self.max_length = self.config_model.max_length
        self.min_length = self.config_model.min_length

    def validate(self, input_data: str) -> GuardrailResponse:
        """
        Validate output length constraints.

        Args:
            input_data: Generated response string to validate

        Returns:
            GuardrailResponse with validation results
        """
        if not self.enabled:
            return GuardrailResponse(
                result=GuardrailResult.PASS,
                message="Validation skipped (disabled)",
                confidence=1.0,
            )

        if not input_data:
            return GuardrailResponse(
                result=GuardrailResult.FAIL, message="Output is empty", confidence=1.0
            )

        length = len(input_data)

        if length < self.min_length:
            return GuardrailResponse(
                result=GuardrailResult.FAIL,
                message=f"Output too short (minimum: {self.min_length} characters)",
                confidence=1.0,
                metadata={"output_length": length},
            )

        if length > self.max_length:
            return GuardrailResponse(
                result=GuardrailResult.FAIL,
                message=f"Output too long (maximum: {self.max_length} characters)",
                confidence=1.0,
                metadata={"output_length": length},
            )

        return GuardrailResponse(
            result=GuardrailResult.PASS,
            message=f"Output length valid ({length} characters)",
            confidence=1.0,
            metadata={"output_length": length},
        )


class RelevanceConfig(BaseGuardrailConfig):
    """Configuration for relevance validator."""

    min_relevance_score: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Minimum relevance score required"
    )
    use_semantic_similarity: bool = Field(
        default=True, description="Whether to use semantic similarity"
    )
    irrelevant_phrases: List[str] = Field(
        default=[
            "i don't know",
            "i cannot answer",
            "i'm not sure",
            "ไม่ทราบ",
            "ไม่แน่ใจ",
            "ตอบไม่ได้",
            "ไม่สามารถตอบได้",
        ],
        description="Phrases that indicate inability to answer",
    )


class RelevanceValidator(BaseGuardrail):
    """
    Validates that the output is relevant to the input question.

    Uses advanced NLP techniques with pythainlp and spacy for better
    language support and semantic understanding.
    """

    guardrail_name = "RelevanceValidator"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.config_model = RelevanceConfig(**config)
        self.min_relevance_score = self.config_model.min_relevance_score
        self.use_semantic_similarity = self.config_model.use_semantic_similarity
        self.irrelevant_phrases = self.config_model.irrelevant_phrases
        self.nlp_processor = get_nlp_processor()

    def validate(self, input_data: Dict[str, str]) -> GuardrailResponse:
        """
        Validate output relevance to the question.

        Args:
            input_data: Dictionary containing 'answer', 'question', and 'context'

        Returns:
            GuardrailResponse with validation results
        """
        if not self.enabled:
            return GuardrailResponse(
                result=GuardrailResult.PASS,
                message="Validation skipped (disabled)",
                confidence=1.0,
            )

        answer = input_data.get("answer", "")
        question = input_data.get("question", "")

        if not answer or not question:
            return GuardrailResponse(
                result=GuardrailResult.FAIL,
                message="Missing answer or question for relevance check",
                confidence=1.0,
            )

        # Check for explicit irrelevant phrases
        answer_lower = answer.lower()
        for phrase in self.irrelevant_phrases:
            if phrase in answer_lower:
                return GuardrailResponse(
                    result=GuardrailResult.FAIL,
                    message=f"Answer indicates inability to respond: '{phrase}'",
                    confidence=0.9,
                    metadata={"detected_phrase": phrase},
                )

        # Calculate relevance score using advanced NLP
        relevance_score = self._calculate_relevance_score(question, answer)

        if relevance_score < self.min_relevance_score:
            return GuardrailResponse(
                result=GuardrailResult.WARNING,
                message=f"Low relevance score: {relevance_score:.2f}",
                confidence=0.7,
                metadata={"relevance_score": relevance_score},
            )

        return GuardrailResponse(
            result=GuardrailResult.PASS,
            message=f"Relevance check passed (score: {relevance_score:.2f})",
            confidence=0.8,
            metadata={"relevance_score": relevance_score},
        )

    def _calculate_relevance_score(self, question: str, answer: str) -> float:
        """
        Calculate relevance score using advanced NLP techniques.

        Uses semantic similarity when available, falls back to keyword-based
        similarity for better accuracy across languages.
        """
        if self.use_semantic_similarity:
            # Try semantic similarity first (works well with spacy)
            semantic_score = calculate_similarity(question, answer)
            if semantic_score > 0:
                return semantic_score

        # Fallback to keyword-based relevance
        return self._calculate_keyword_relevance(question, answer)

    def _calculate_keyword_relevance(self, question: str, answer: str) -> float:
        """
        Calculate keyword-based relevance score using proper NLP tokenization.

        Uses pythainlp for Thai and spacy for English with proper stop word removal.
        """
        # Get keywords using proper NLP tokenization
        question_keywords = set(self.nlp_processor.get_keywords(question))
        answer_keywords = set(self.nlp_processor.get_keywords(answer))

        if not question_keywords:
            return 1.0  # No keywords to match

        # Calculate Jaccard similarity
        intersection = len(question_keywords & answer_keywords)
        union = len(question_keywords | answer_keywords)

        if union == 0:
            return 0.0

        return intersection / union


class HallucinationConfig(BaseGuardrailConfig):
    """Configuration for hallucination validator."""

    confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for hallucination detection",
    )
    context_coverage_threshold: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Minimum context coverage required"
    )
    uncertainty_phrases: List[str] = Field(
        default=[
            "i think",
            "maybe",
            "possibly",
            "perhaps",
            "might be",
            "could be",
            "ไม่แน่ใจ",
            "อาจจะ",
            "น่าจะ",
            "คงจะ",
        ],
        description="Phrases indicating uncertainty",
    )
    fabrication_indicators: List[str] = Field(
        default=[
            "i made this up",
            "this is fictional",
            "i don't have information",
            "ไม่มีข้อมูล",
            "ไม่ทราบข้อมูล",
            "ไม่มีรายละเอียด",
        ],
        description="Phrases indicating fabrication",
    )


class HallucinationValidator(BaseGuardrail):
    """
    Detects potential hallucinations in generated responses.

    This validator uses multiple strategies to identify when the model
    might be generating information not supported by the provided context.
    """

    guardrail_name = "HallucinationValidator"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.config_model = HallucinationConfig(**config)
        self.confidence_threshold = self.config_model.confidence_threshold
        self.context_coverage_threshold = self.config_model.context_coverage_threshold
        self.uncertainty_phrases = self.config_model.uncertainty_phrases
        self.fabrication_indicators = self.config_model.fabrication_indicators

    def validate(self, input_data: Dict[str, str]) -> GuardrailResponse:
        """
        Check for potential hallucinations in the output.

        Args:
            input_data: Dictionary containing 'answer', 'question', and 'context'

        Returns:
            GuardrailResponse with validation results
        """
        if not self.enabled:
            return GuardrailResponse(
                result=GuardrailResult.PASS,
                message="Validation skipped (disabled)",
                confidence=1.0,
            )

        answer = input_data.get("answer", "")
        context = input_data.get("context", "")

        if not answer:
            return GuardrailResponse(
                result=GuardrailResult.FAIL,
                message="No answer provided for hallucination check",
                confidence=1.0,
            )

        answer_lower = answer.lower()
        detected_issues = []

        # Check for uncertainty phrases
        for phrase in self.uncertainty_phrases:
            if phrase in answer_lower:
                detected_issues.append(f"Uncertainty phrase: '{phrase}'")

        # Check for fabrication indicators
        for phrase in self.fabrication_indicators:
            if phrase in answer_lower:
                detected_issues.append(f"Fabrication indicator: '{phrase}'")

        # If context is provided, check if answer contains information not in context
        if context:
            context_coverage = self._check_context_coverage(answer, context)
            if context_coverage < self.context_coverage_threshold:
                detected_issues.append(f"Low context coverage: {context_coverage:.2f}")

        if detected_issues:
            return GuardrailResponse(
                result=GuardrailResult.WARNING,
                message="Potential hallucination detected",
                confidence=self.confidence_threshold,
                metadata={"detected_issues": detected_issues},
            )

        return GuardrailResponse(
            result=GuardrailResult.PASS,
            message="No hallucination indicators detected",
            confidence=0.9,
        )

    def _check_context_coverage(self, answer: str, context: str) -> float:
        """
        Calculate how much of the answer is covered by the context.

        This is a simple implementation using keyword overlap.
        For production use, consider more sophisticated semantic matching.
        """
        # Simple keyword-based coverage check
        answer_words = set(answer.lower().split())
        context_words = set(context.lower().split())

        if not answer_words:
            return 1.0

        # Calculate overlap
        overlap = len(answer_words & context_words)
        coverage = overlap / len(answer_words)

        return min(coverage, 1.0)
