"""
PII (Personally Identifiable Information) detection and masking guardrails.

This module contains validators that detect and optionally mask
sensitive personal information in both inputs and outputs.
"""

import re
from typing import Any, Dict, List, Tuple

from src.guardrails.base import BaseGuardrail, GuardrailResponse, GuardrailResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


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

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.mask_pii = config.get("mask_pii", True)
        self.allowed_pii_types = set(config.get("allowed_pii_types", []))
        self.fail_on_pii = config.get("fail_on_pii", True)

        # PII detection patterns
        self.pii_patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone_international": r"\+?\d{1,4}[\s\-]?\(?\d{1,3}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}",
            "phone_thai": r"0[0-9]{8,9}",
            "thai_id": r"\b\d{1}\s?\d{4}\s?\d{5}\s?\d{2}\s?\d{1}\b",
            "credit_card": r"\b(?:\d{4}[\s\-]?){3}\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            # Basic name patterns (these might have false positives)
            "potential_name": r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
            "thai_name": r"\b[ก-๙]+\s+[ก-๙]+\b",
        }

        # Custom patterns from config
        custom_patterns = config.get("custom_patterns", {})
        self.pii_patterns.update(custom_patterns)

        # Masking character
        self.mask_char = config.get("mask_char", "*")

    @property
    def name(self) -> str:
        return "PIIDetector"

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

        masked_text = text

        # Process PII from end to start to maintain correct positions
        for pii in reversed(pii_list):
            start, end = pii["start"], pii["end"]
            pii_type = pii["type"]
            original_value = pii["value"]

            # Create mask based on PII type
            masked_value = self._create_mask(original_value, pii_type)

            # Replace the PII with masked value
            masked_text = masked_text[:start] + masked_value + masked_text[end:]

        return masked_text

    def _create_mask(self, value: str, pii_type: str) -> str:
        """
        Create appropriate mask for different PII types.

        Args:
            value: Original PII value
            pii_type: Type of PII

        Returns:
            Masked value
        """
        if pii_type == "email":
            # Mask email keeping domain visible: "user@domain.com" -> "****@domain.com"
            parts = value.split("@")
            if len(parts) == 2:
                return self.mask_char * 4 + "@" + parts[1]
            else:
                return self.mask_char * len(value)

        elif pii_type in ["phone_international", "phone_thai"]:
            # Mask phone keeping last 4 digits: "0812345678" -> "******5678"
            if len(value) > 4:
                return self.mask_char * (len(value) - 4) + value[-4:]
            else:
                return self.mask_char * len(value)

        elif pii_type == "thai_id":
            # Mask Thai ID keeping first and last digit: "1234567890123" -> "1***********3"
            if len(value) > 2:
                clean_value = re.sub(r"\s", "", value)
                return (
                    clean_value[0]
                    + self.mask_char * (len(clean_value) - 2)
                    + clean_value[-1]
                )
            else:
                return self.mask_char * len(value)

        elif pii_type == "credit_card":
            # Mask credit card keeping last 4 digits: "1234 5678 9012 3456" -> "**** **** **** 3456"
            clean_value = re.sub(r"[\s\-]", "", value)
            if len(clean_value) > 4:
                masked_digits = (
                    self.mask_char * (len(clean_value) - 4) + clean_value[-4:]
                )
                # Restore original formatting
                return re.sub(
                    r"\d",
                    lambda m: masked_digits[0:1] if masked_digits else self.mask_char,
                    value,
                )
            else:
                return self.mask_char * len(value)

        elif pii_type in ["potential_name", "thai_name"]:
            # Mask names keeping first letter: "John Doe" -> "J*** D**"
            words = value.split()
            masked_words = []
            for word in words:
                if len(word) > 1:
                    masked_words.append(word[0] + self.mask_char * (len(word) - 1))
                else:
                    masked_words.append(self.mask_char)
            return " ".join(masked_words)

        else:
            # Default masking: replace entire value
            return self.mask_char * len(value)

    def get_masked_text(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Public method to get masked text and detected PII.

        Args:
            text: Input text to process

        Returns:
            Tuple of (masked_text, detected_pii_list)
        """
        detected_pii = self._detect_pii(text)

        # Filter out allowed PII types
        filtered_pii = [
            pii for pii in detected_pii if pii["type"] not in self.allowed_pii_types
        ]

        masked_text = self._mask_pii(text, filtered_pii) if self.mask_pii else text

        return masked_text, detected_pii
