"""
Output validation guardrails.

This module contains validators that check system outputs before
they are returned to users.
"""

from typing import Any, Dict

from src.guardrails.base import BaseGuardrail, GuardrailResponse, GuardrailResult
from src.utils.logger import get_logger
from src.utils.nlp_utils import calculate_similarity, get_nlp_processor

logger = get_logger(__name__)


class OutputLengthValidator(BaseGuardrail):
    """
    Validates output length to ensure reasonable response sizes.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.max_length = config.get("max_length", 2000)
        self.min_length = config.get("min_length", 5)

    @property
    def name(self) -> str:
        return "OutputLengthValidator"

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


class RelevanceValidator(BaseGuardrail):
    """
    Validates that the output is relevant to the input question.

    Uses advanced NLP techniques with pythainlp and spacy for better
    language support and semantic understanding.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.min_relevance_score = config.get("min_relevance_score", 0.3)
        self.use_semantic_similarity = config.get("use_semantic_similarity", True)

        # Irrelevant phrases that indicate inability to answer
        self.irrelevant_phrases = config.get(
            "irrelevant_phrases",
            [
                "i don't know",
                "i cannot answer",
                "i'm not sure",
                "ไม่ทราบ",
                "ไม่แน่ใจ",
                "ตอบไม่ได้",
                "ไม่สามารถตอบได้",
            ],
        )

        self.nlp_processor = get_nlp_processor()

    @property
    def name(self) -> str:
        return "RelevanceValidator"

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

        return intersection / union if union > 0 else 0.0


class HallucinationValidator(BaseGuardrail):
    """
    Detects potential hallucinations in model outputs.

    Uses advanced NLP techniques to identify signs that the model might be
    making up information not present in the context.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.confidence_threshold = config.get("confidence_threshold", 0.8)
        self.context_coverage_threshold = config.get("context_coverage_threshold", 0.5)

        # Phrases that might indicate hallucination
        self.uncertainty_phrases = config.get(
            "uncertainty_phrases",
            [
                "according to my knowledge",
                "based on what i know",
                "i believe that",
                "it seems that",
                "probably",
                "likely",
                "ตามที่ฉันรู้",
                "จากความรู้ของฉัน",
                "ฉันเชื่อว่า",
                "ดูเหมือนว่า",
                "น่าจะ",
                "อาจจะ",
            ],
        )

        # Phrases that might indicate made-up information
        self.fabrication_indicators = config.get(
            "fabrication_indicators",
            [
                "as mentioned earlier",
                "as we discussed",
                "in the previous section",
                "ดังที่กล่าวไว้",
                "ตามที่พูดไว้",
                "ในส่วนก่อนหน้า",
            ],
        )

        self.nlp_processor = get_nlp_processor()

    @property
    def name(self) -> str:
        return "HallucinationValidator"

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
            severity = (
                GuardrailResult.WARNING
                if len(detected_issues) <= 2
                else GuardrailResult.FAIL
            )
            return GuardrailResponse(
                result=severity,
                message="Potential hallucination detected",
                confidence=0.7,
                metadata={"detected_issues": detected_issues},
            )

        return GuardrailResponse(
            result=GuardrailResult.PASS,
            message="No hallucination indicators detected",
            confidence=0.8,
        )

    def _check_context_coverage(self, answer: str, context: str) -> float:
        """
        Check how much of the answer is covered by the context.

        Uses proper NLP tokenization for better accuracy across languages.
        """
        answer_keywords = set(self.nlp_processor.get_keywords(answer))
        context_keywords = set(self.nlp_processor.get_keywords(context))

        if not answer_keywords:
            return 1.0

        covered_keywords = answer_keywords & context_keywords
        return len(covered_keywords) / len(answer_keywords)
