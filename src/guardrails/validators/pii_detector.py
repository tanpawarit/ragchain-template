"""
PII (Personally Identifiable Information) detection and masking guardrails.

This module contains validators that detect and optionally mask
sensitive personal information in both inputs and outputs.
"""

import re
from typing import Any, Dict, List, Tuple

from pydantic import Field

from src.guardrails.base import (
    BaseGuardrail,
    BaseGuardrailConfig,
    GuardrailResponse,
    GuardrailResult,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PIIDetectionConfig(BaseGuardrailConfig):
    """Configuration for PII detector."""

    mask_pii: bool = Field(default=True, description="Whether to mask detected PII")
    allowed_pii_types: List[str] = Field(
        default=[], description="PII types that are allowed and won't trigger failures"
    )
    fail_on_pii: bool = Field(
        default=True, description="Whether to fail when PII is detected"
    )
    mask_char: str = Field(default="*", description="Character to use for masking PII")
    pii_patterns: Dict[str, str] = Field(
        default={
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone_international": r"\+?\d{1,4}[\s\-]?\(?\d{1,3}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}",
            "phone_thai": r"0[0-9]{8,9}",
            "thai_id": r"\b\d{1}\s?\d{4}\s?\d{5}\s?\d{2}\s?\d{1}\b",
            "credit_card": r"\b(?:\d{4}[\s\-]?){3}\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "potential_name": r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
            "thai_name": r"\b[ก-๙]+\s+[ก-๙]+\b",
        },
        description="Regex patterns for detecting different types of PII",
    )


class PIIDetector(BaseGuardrail):
    """
    Detects and optionally masks personally identifiable information (PII).

    This validator can identify various types of PII including:
    - Email addresses
    - Phone numbers
    - Credit card numbers
    - Thai national ID numbers
    - Names (basic pattern matching)
    """

    guardrail_name = "PIIDetector"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.config_model = PIIDetectionConfig(**config)
        self.mask_pii = self.config_model.mask_pii
        self.allowed_pii_types = set(self.config_model.allowed_pii_types)
        self.fail_on_pii = self.config_model.fail_on_pii
        self.mask_char = self.config_model.mask_char
        self.pii_patterns = self.config_model.pii_patterns

        # Custom patterns from config (for backward compatibility)
        custom_patterns = config.get("custom_patterns", {})
        self.pii_patterns.update(custom_patterns)

    def validate(self, input_data: str) -> GuardrailResponse:
        """
        Detect PII in the input and optionally mask it.

        Args:
            input_data: Text to validate for PII

        Returns:
            GuardrailResponse with validation results and optionally masked text
        """
        if not self.enabled or not input_data:
            return GuardrailResponse(
                result=GuardrailResult.PASS,
                message="Validation skipped (disabled or empty input)",
                confidence=1.0,
            )

        detected_pii = self._detect_pii(input_data)

        if not detected_pii:
            return GuardrailResponse(
                result=GuardrailResult.PASS, message="No PII detected", confidence=0.9
            )

        # Filter out allowed PII types
        filtered_pii = [
            pii for pii in detected_pii if pii["type"] not in self.allowed_pii_types
        ]

        if not filtered_pii:
            return GuardrailResponse(
                result=GuardrailResult.PASS,
                message="Only allowed PII types detected",
                confidence=0.8,
                metadata={"detected_pii": detected_pii},
            )

        # Determine result based on configuration
        if self.fail_on_pii:
            result = GuardrailResult.FAIL
            message = f"PII detected: {[pii['type'] for pii in filtered_pii]}"
        else:
            result = GuardrailResult.WARNING
            message = (
                f"PII detected but allowed: {[pii['type'] for pii in filtered_pii]}"
            )

        # Prepare response metadata
        metadata: Dict[str, Any] = {
            "detected_pii": detected_pii,
            "filtered_pii": filtered_pii,
        }

        # Add masked text if masking is enabled
        if self.mask_pii:
            masked_text = self._mask_pii(input_data, filtered_pii)
            metadata["masked_text"] = masked_text

        logger.warning(f"PII detected: {[pii['type'] for pii in filtered_pii]}")

        return GuardrailResponse(
            result=result, message=message, confidence=0.9, metadata=metadata
        )

    def _detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect all PII in the text.

        Args:
            text: Input text to analyze

        Returns:
            List of detected PII with type, value, and position information
        """
        detected_pii = []

        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                pii_info = {
                    "type": pii_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": self._calculate_pii_confidence(
                        pii_type, match.group()
                    ),
                }
                detected_pii.append(pii_info)

        # Sort by position for consistent masking
        detected_pii.sort(key=lambda x: x["start"])

        return detected_pii

    def _calculate_pii_confidence(self, pii_type: str, value: str) -> float:
        """
        Calculate confidence score for detected PII.

        Args:
            pii_type: Type of PII detected
            value: The detected value

        Returns:
            Confidence score between 0 and 1
        """
        # Simple confidence scoring based on PII type
        confidence_scores = {
            "email": 0.95,
            "phone_international": 0.85,
            "phone_thai": 0.90,
            "thai_id": 0.95,
            "credit_card": 0.90,
            "ssn": 0.95,
            "potential_name": 0.60,  # Lower confidence due to false positives
            "thai_name": 0.70,
        }

        base_confidence = confidence_scores.get(pii_type, 0.8)

        # Adjust confidence based on value characteristics
        if pii_type in ["potential_name", "thai_name"]:
            # Lower confidence for very short or very long "names"
            if len(value) < 5 or len(value) > 50:
                base_confidence *= 0.5

        return min(base_confidence, 1.0)

    def _mask_pii(self, text: str, pii_list: List[Dict[str, Any]]) -> str:
        """
        Mask detected PII in the text.

        Args:
            text: Original text
            pii_list: List of PII to mask

        Returns:
            Text with PII masked
        """
        if not pii_list:
            return text

        # Sort PII by position in reverse order to maintain text positions
        sorted_pii = sorted(pii_list, key=lambda x: x["start"], reverse=True)

        masked_text = text
        for pii in sorted_pii:
            # Create appropriate mask for this PII type
            mask = self._create_mask(pii["value"], pii["type"])

            # Replace the PII with the mask
            masked_text = masked_text[: pii["start"]] + mask + masked_text[pii["end"] :]

        return masked_text

    def _create_mask(self, value: str, pii_type: str) -> str:
        """
        Create an appropriate mask for the detected PII.

        Args:
            value: The original PII value
            pii_type: Type of PII

        Returns:
            Masked version of the value
        """
        # Different masking strategies based on PII type
        if pii_type == "email":
            # Mask email but keep domain visible
            parts = value.split("@")
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                # Keep first and last character of username
                if len(username) > 2:
                    masked_username = (
                        username[0]
                        + self.mask_char * (len(username) - 2)
                        + username[-1]
                    )
                else:
                    masked_username = self.mask_char * len(username)
                return f"{masked_username}@{domain}"

        elif pii_type in ["phone_international", "phone_thai"]:
            # Mask middle digits of phone numbers
            if len(value) > 4:
                return value[:2] + self.mask_char * (len(value) - 4) + value[-2:]

        elif pii_type == "credit_card":
            # Mask all but last 4 digits
            digits_only = "".join(c for c in value if c.isdigit())
            if len(digits_only) > 4:
                masked_digits = (
                    self.mask_char * (len(digits_only) - 4) + digits_only[-4:]
                )
                # Preserve original formatting
                result = ""
                digit_index = 0
                for char in value:
                    if char.isdigit():
                        result += masked_digits[digit_index]
                        digit_index += 1
                    else:
                        result += char
                return result

        elif pii_type == "thai_id":
            # Mask middle digits of Thai ID
            digits_only = "".join(c for c in value if c.isdigit())
            if len(digits_only) >= 13:
                masked_digits = digits_only[:1] + self.mask_char * 8 + digits_only[-4:]
                # Preserve original formatting
                result = ""
                digit_index = 0
                for char in value:
                    if char.isdigit():
                        result += masked_digits[digit_index]
                        digit_index += 1
                    else:
                        result += char
                return result

        # Default masking: replace all characters except spaces
        return "".join(self.mask_char if c != " " else c for c in value)

    def get_masked_text(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Get masked version of text and detected PII information.

        Args:
            text: Input text to process

        Returns:
            Tuple of (masked_text, detected_pii_list)
        """
        detected_pii = self._detect_pii(text)
        masked_text = self._mask_pii(text, detected_pii)
        return masked_text, detected_pii
