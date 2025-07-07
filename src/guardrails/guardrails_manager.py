"""
Guardrail Manager - Central orchestration of all guardrail validations.

This module manages the lifecycle and execution of all guardrail validators
for the RAG system, providing a unified interface for validation checks.
"""

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from src.guardrails.base import BaseGuardrail, GuardrailResponse
from src.guardrails.validators.content_safety import (
    HateSpeechValidator,
    ToxicityValidator,
)
from src.guardrails.validators.input_validators import (
    InputLengthValidator,
    ProfanityValidator,
    PromptInjectionValidator,
)
from src.guardrails.validators.output_validators import (
    HallucinationValidator,
    OutputLengthValidator,
    RelevanceValidator,
)
from src.guardrails.validators.pii_detector import PIIDetector
from src.utils.logger import get_logger

logger = get_logger(__name__)


class InputValidationConfig(BaseModel):
    """Configuration for input validation."""

    enabled: bool = True
    check_prompt_injection: bool = True
    prompt_injection_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    max_length: int = Field(default=1000, gt=0)
    min_length: int = Field(default=1, ge=0)
    check_profanity: bool = True
    profanity_severity: str = "warning"


class OutputValidationConfig(BaseModel):
    """Configuration for output validation."""

    enabled: bool = True
    max_response_length: int = Field(default=2000, gt=0)
    min_response_length: int = Field(default=5, ge=0)
    check_relevance: bool = True
    relevance_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    check_hallucination: bool = True
    hallucination_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class ContentSafetyConfig(BaseModel):
    """Configuration for content safety validation."""

    enabled: bool = True
    toxicity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    hate_speech_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class PIIDetectionConfig(BaseModel):
    """Configuration for PII detection."""

    enabled: bool = True
    mask_pii: bool = True
    allowed_pii_types: List[str] = Field(default_factory=list)
    fail_on_pii: bool = False


class GuardrailManagerConfig(BaseModel):
    """Configuration for the guardrail manager."""

    enabled: bool = True
    input_validation: InputValidationConfig = Field(
        default_factory=InputValidationConfig
    )
    output_validation: OutputValidationConfig = Field(
        default_factory=OutputValidationConfig
    )
    content_safety: ContentSafetyConfig = Field(default_factory=ContentSafetyConfig)
    pii_detection: PIIDetectionConfig = Field(default_factory=PIIDetectionConfig)

    model_config = ConfigDict(
        extra="allow"
    )  # Allow additional fields for extensibility


class GuardrailManager:
    """
    Manages and orchestrates all guardrail validations.

    This class provides a unified interface for running all types of
    guardrail validations across the RAG pipeline.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the guardrail manager with configuration.

        Args:
            config: Guardrail configuration dictionary
        """
        self.config_dict = config
        self.config = GuardrailManagerConfig(**config)
        self.enabled = self.config.enabled

        # Initialize validator lists
        self.input_validators: List[BaseGuardrail] = []
        self.output_validators: List[BaseGuardrail] = []
        self.context_validators: List[BaseGuardrail] = []

        if self.enabled:
            self._initialize_validators()

    def _initialize_validators(self) -> None:
        """Initialize all configured validators."""
        try:
            # Input validation
            input_config = self.config.input_validation
            if input_config.enabled:
                self._initialize_input_validators(input_config)

            # Output validation
            output_config = self.config.output_validation
            if output_config.enabled:
                self._initialize_output_validators(output_config)

            # Content safety
            content_safety_config = self.config.content_safety
            if content_safety_config.enabled:
                self._initialize_content_safety_validators(content_safety_config)

            # PII detection
            pii_config = self.config.pii_detection
            if pii_config.enabled:
                self._initialize_pii_validators(pii_config)

            logger.info(
                f"Initialized guardrails: {len(self.input_validators)} input, "
                f"{len(self.output_validators)} output, "
                f"{len(self.context_validators)} context validators"
            )

        except Exception as e:
            logger.error(f"Failed to initialize guardrails: {e}")
            # Continue with empty validators rather than failing

    def _initialize_input_validators(self, config: InputValidationConfig) -> None:
        """Initialize input validation guardrails."""
        # Prompt injection detection
        if config.check_prompt_injection:
            prompt_injection_config = {
                "enabled": True,
                "threshold": config.prompt_injection_threshold,
            }
            self.input_validators.append(
                PromptInjectionValidator(prompt_injection_config)
            )

        # Input length validation
        length_config = {
            "enabled": True,
            "max_length": config.max_length,
            "min_length": config.min_length,
        }
        self.input_validators.append(InputLengthValidator(length_config))

        # Profanity detection
        if config.check_profanity:
            profanity_config = {
                "enabled": True,
                "severity": config.profanity_severity,
            }
            self.input_validators.append(ProfanityValidator(profanity_config))

    def _initialize_output_validators(self, config: OutputValidationConfig) -> None:
        """Initialize output validation guardrails."""
        # Output length validation
        length_config = {
            "enabled": True,
            "max_length": config.max_response_length,
            "min_length": config.min_response_length,
        }
        self.output_validators.append(OutputLengthValidator(length_config))

        # Relevance checking
        if config.check_relevance:
            relevance_config = {
                "enabled": True,
                "min_relevance_score": config.relevance_threshold,
            }
            self.output_validators.append(RelevanceValidator(relevance_config))

        # Hallucination detection
        if config.check_hallucination:
            hallucination_config = {
                "enabled": True,
                "confidence_threshold": config.hallucination_threshold,
            }
            self.output_validators.append(HallucinationValidator(hallucination_config))

    def _initialize_content_safety_validators(
        self, config: ContentSafetyConfig
    ) -> None:
        """Initialize content safety guardrails."""
        # Toxicity detection (applies to both input and output)
        toxicity_config = {
            "enabled": True,
            "threshold": config.toxicity_threshold,
        }
        toxicity_validator = ToxicityValidator(toxicity_config)
        self.input_validators.append(toxicity_validator)
        self.output_validators.append(toxicity_validator)

        # Hate speech detection (applies to both input and output)
        hate_speech_config = {
            "enabled": True,
            "threshold": config.hate_speech_threshold,
        }
        hate_speech_validator = HateSpeechValidator(hate_speech_config)
        self.input_validators.append(hate_speech_validator)
        self.output_validators.append(hate_speech_validator)

    def _initialize_pii_validators(self, config: PIIDetectionConfig) -> None:
        """Initialize PII detection guardrails."""
        pii_config = {
            "enabled": True,
            "mask_pii": config.mask_pii,
            "allowed_pii_types": config.allowed_pii_types,
            "fail_on_pii": config.fail_on_pii,  # Default to warning for PII
        }
        pii_detector = PIIDetector(pii_config)

        # Apply PII detection to both input and output
        self.input_validators.append(pii_detector)
        self.output_validators.append(pii_detector)

    def validate_input(
        self, question: str, user_id: Optional[str] = None
    ) -> Tuple[bool, List[GuardrailResponse]]:
        """
        Validate user input before processing.

        Args:
            question: User's input question
            user_id: Optional user identifier for logging

        Returns:
            Tuple of (is_valid, list_of_validation_results)
        """
        if not self.enabled:
            return True, []

        results = []

        for validator in self.input_validators:
            if not validator.is_enabled():
                continue

            try:
                result = validator.validate(question)
                results.append(result)

                # Stop on first failure (unless configured otherwise)
                if result.is_failed():
                    logger.warning(
                        f"Input validation failed: {validator.name} - {result.message}"
                    )
                    return False, results

            except Exception as e:
                logger.error(f"Error in input validator {validator.name}: {e}")
                # Continue with other validators

        # Check if any warnings should be escalated to failures
        warning_count = sum(1 for r in results if r.is_warning())
        if warning_count > 2:  # Configurable threshold
            logger.warning(
                f"Too many validation warnings ({warning_count}), treating as failure"
            )
            return False, results

        return True, results

    def validate_context(
        self, retrieved_docs: List[Any]
    ) -> Tuple[bool, List[GuardrailResponse]]:
        """
        Validate retrieved context documents.

        Args:
            retrieved_docs: List of retrieved documents from vector store

        Returns:
            Tuple of (is_valid, list_of_validation_results)
        """
        if not self.enabled:
            return True, []

        results = []

        # For now, we mainly apply content safety to retrieved documents
        context_text = ""
        if retrieved_docs:
            context_text = "\n".join(
                [getattr(doc, "page_content", str(doc)) for doc in retrieved_docs]
            )

        # Apply content safety validators to the context
        for validator in self.context_validators:
            if not validator.is_enabled():
                continue

            try:
                result = validator.validate(context_text)
                results.append(result)

                if result.is_failed():
                    logger.warning(
                        f"Context validation failed: {validator.name} - {result.message}"
                    )
                    return False, results

            except Exception as e:
                logger.error(f"Error in context validator {validator.name}: {e}")

        return True, results

    def validate_output(
        self, answer: str, question: str, context: str
    ) -> Tuple[bool, List[GuardrailResponse]]:
        """
        Validate generated output before returning to user.

        Args:
            answer: Generated response from the model
            question: Original user question
            context: Retrieved context used for generation

        Returns:
            Tuple of (is_valid, list_of_validation_results)
        """
        if not self.enabled:
            return True, []

        results = []

        for validator in self.output_validators:
            if not validator.is_enabled():
                continue

            try:
                # Determine what data to pass to the validator
                if validator.name in ["RelevanceValidator", "HallucinationValidator"]:
                    # These validators need structured data
                    validation_data = {
                        "answer": answer,
                        "question": question,
                        "context": context,
                    }
                else:
                    # Simple validators just need the text
                    validation_data = answer

                result = validator.validate(validation_data)
                results.append(result)

                if result.is_failed():
                    logger.warning(
                        f"Output validation failed: {validator.name} - {result.message}"
                    )
                    return False, results

            except Exception as e:
                logger.error(f"Error in output validator {validator.name}: {e}")

        return True, results

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the configured guardrails."""
        return {
            "enabled": self.enabled,
            "input_validators": [v.name for v in self.input_validators],
            "output_validators": [v.name for v in self.output_validators],
            "context_validators": [v.name for v in self.context_validators],
            "config": self.config.model_dump(),
        }

    def get_validation_report(self, results: List[GuardrailResponse]) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.

        Args:
            results: List of validation results

        Returns:
            Dictionary with validation report
        """
        if not results:
            return {"status": "no_validations", "details": []}

        passed = [r for r in results if r.is_passed()]
        failed = [r for r in results if r.is_failed()]
        warnings = [r for r in results if r.is_warning()]

        return {
            "status": "failed" if failed else ("warning" if warnings else "passed"),
            "total_checks": len(results),
            "passed": len(passed),
            "failed": len(failed),
            "warnings": len(warnings),
            "details": [
                {
                    "result": r.result.value,
                    "message": r.message,
                    "confidence": r.confidence,
                    "metadata": r.metadata or {},
                }
                for r in results
            ],
        }
