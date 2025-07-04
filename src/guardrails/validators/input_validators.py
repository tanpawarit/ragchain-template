"""
Input validation guardrails.

This module contains validators that check user inputs before
they are processed by the RAG system.
"""

import re
from typing import Any, Dict, List

from pydantic import Field

from src.guardrails.base import (
    BaseGuardrail,
    BaseGuardrailConfig,
    GuardrailResponse,
    GuardrailResult,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PromptInjectionConfig(BaseGuardrailConfig):
    """Configuration for prompt injection validator."""

    patterns: List[str] = Field(
        default=[
            # English patterns
            r"ignore\s+previous\s+instructions",
            r"forget\s+everything",
            r"disregard\s+.+instructions",
            r"system\s*:",
            r"assistant\s*:",
            r"<\|.*?\|>",
            r"###\s*instruction",
            r"you\s+are\s+now",
            r"new\s+instructions",
            r"override\s+previous",
            # Thai patterns
            r"ลืม.*คำสั่ง",
            r"เพิกเฉย.*คำสั่ง",
            r"ไม่สนใจ.*คำสั่ง",
            r"คำสั่งใหม่",
            r"ระบบ\s*:",
            r"ผู้ช่วย\s*:",
        ],
        description="Regex patterns to detect prompt injection attempts",
    )
    threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence threshold for detection"
    )


class PromptInjectionValidator(BaseGuardrail):
    """
    Detects potential prompt injection attacks in user input.

    This validator looks for patterns commonly used in prompt injection
    attacks, including attempts to override system instructions.
    """

    guardrail_name = "PromptInjectionValidator"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.config_model = PromptInjectionConfig(**config)
        self.injection_patterns = self.config_model.patterns
        self.threshold = self.config_model.threshold

    def validate(self, input_data: str) -> GuardrailResponse:
        """
        Check for prompt injection patterns in the input.

        Args:
            input_data: User input string to validate

        Returns:
            GuardrailResponse with validation results
        """
        if not self.enabled or not input_data:
            return GuardrailResponse(
                result=GuardrailResult.PASS,
                message="Validation skipped (disabled or empty input)",
                confidence=1.0,
            )

        text = input_data.lower().strip()
        detected_patterns = []

        for pattern in self.injection_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                detected_patterns.append(pattern)

        if detected_patterns:
            logger.warning(f"Prompt injection detected: {detected_patterns}")
            return GuardrailResponse(
                result=GuardrailResult.FAIL,
                message="Potential prompt injection detected",
                confidence=self.threshold,
                metadata={"detected_patterns": detected_patterns},
            )

        return GuardrailResponse(
            result=GuardrailResult.PASS,
            message="No prompt injection detected",
            confidence=0.9,
        )


class InputLengthConfig(BaseGuardrailConfig):
    """Configuration for input length validator."""

    max_length: int = Field(
        default=1000, gt=0, description="Maximum allowed input length"
    )
    min_length: int = Field(
        default=1, ge=0, description="Minimum required input length"
    )


class InputLengthValidator(BaseGuardrail):
    """
    Validates input length to prevent resource exhaustion attacks.
    """

    guardrail_name = "InputLengthValidator"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.config_model = InputLengthConfig(**config)
        self.max_length = self.config_model.max_length
        self.min_length = self.config_model.min_length

    def validate(self, input_data: str) -> GuardrailResponse:
        """
        Validate input length constraints.

        Args:
            input_data: User input string to validate

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
                result=GuardrailResult.FAIL, message="Input is empty", confidence=1.0
            )

        length = len(input_data)

        if length < self.min_length:
            return GuardrailResponse(
                result=GuardrailResult.FAIL,
                message=f"Input too short (minimum: {self.min_length} characters)",
                confidence=1.0,
                metadata={"input_length": length},
            )

        if length > self.max_length:
            return GuardrailResponse(
                result=GuardrailResult.FAIL,
                message=f"Input too long (maximum: {self.max_length} characters)",
                confidence=1.0,
                metadata={"input_length": length},
            )

        return GuardrailResponse(
            result=GuardrailResult.PASS,
            message=f"Input length valid ({length} characters)",
            confidence=1.0,
            metadata={"input_length": length},
        )


class ProfanityConfig(BaseGuardrailConfig):
    """Configuration for profanity validator."""

    patterns: List[str] = Field(
        default=[
            r"\b(damn|hell|shit|fuck|bitch)\b",
            r"\b(โง่|ชั่ว|แย่)\b",
        ],
        description="Regex patterns to detect profanity",
    )
    severity: str = Field(
        default="warning", description="Severity level ('warning' or 'fail')"
    )


class ProfanityValidator(BaseGuardrail):
    """
    Detects profanity and inappropriate content in user input.
    """

    guardrail_name = "ProfanityValidator"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.config_model = ProfanityConfig(**config)
        self.profanity_patterns = self.config_model.patterns
        self.severity = self.config_model.severity

    def validate(self, input_data: str) -> GuardrailResponse:
        """
        Check for profanity in the input.

        Args:
            input_data: User input string to validate

        Returns:
            GuardrailResponse with validation results
        """
        if not self.enabled or not input_data:
            return GuardrailResponse(
                result=GuardrailResult.PASS,
                message="Validation skipped (disabled or empty input)",
                confidence=1.0,
            )

        text = input_data.lower()
        detected_patterns = []

        for pattern in self.profanity_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected_patterns.append(pattern)

        if detected_patterns:
            result = (
                GuardrailResult.FAIL
                if self.severity == "fail"
                else GuardrailResult.WARNING
            )
            return GuardrailResponse(
                result=result,
                message="Inappropriate content detected",
                confidence=0.8,
                metadata={"detected_patterns": detected_patterns},
            )

        return GuardrailResponse(
            result=GuardrailResult.PASS,
            message="No inappropriate content detected",
            confidence=0.9,
        )
