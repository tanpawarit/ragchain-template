"""
Content safety guardrails.

This module contains validators that check for harmful, toxic,
or inappropriate content in both inputs and outputs.
"""

import re
from typing import Any, Dict, List

from src.guardrails.base import BaseGuardrail, GuardrailResponse, GuardrailResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ToxicityValidator(BaseGuardrail):
    """
    Detects toxic content in text.

    This is a basic implementation using pattern matching.
    For production use, consider using specialized toxicity detection models
    like Perspective API or similar services.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.toxicity_threshold = config.get("threshold", 0.7)

        # Basic toxic patterns (this should be expanded for production use)
        self.toxic_patterns = config.get(
            "patterns",
            [
                # Violence and threats
                r"\b(kill|murder|die|death|hurt|harm|violence|attack)\b",
                r"\b(threat|threaten|revenge|destroy)\b",
                # Self-harm
                r"\b(suicide|self.harm|cut.myself|end.my.life)\b",
                # Harassment
                r"\b(stupid|idiot|loser|worthless|pathetic)\b",
                r"\b(shut.up|go.away|leave.me.alone)\b",
                # Thai toxic patterns
                r"\b(ตาย|ฆ่า|ทำร้าย|ทำลาย)\b",
                r"\b(โง่|ปัญญาอ่อน|ไร้ค่า|น่าเกลียด)\b",
                r"\b(หุบปาก|ไปให้พ้น|เลิกมาเยอะ)\b",
            ],
        )

        self.severity_weights = {
            "violence": 1.0,
            "harassment": 0.7,
            "self_harm": 1.0,
            "general_toxicity": 0.5,
        }

    @property
    def name(self) -> str:
        return "ToxicityValidator"

    def validate(self, input_data: str) -> GuardrailResponse:
        """
        Check for toxic content in the input.

        Args:
            input_data: Text to validate for toxicity

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
        max_severity = 0.0

        for pattern in self.toxic_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected_patterns.append(pattern)
                # Simple severity scoring based on pattern type
                severity = self._calculate_pattern_severity(pattern)
                max_severity = max(max_severity, severity)

        if detected_patterns:
            if max_severity >= self.toxicity_threshold:
                result = GuardrailResult.FAIL
                message = "Toxic content detected"
            else:
                result = GuardrailResult.WARNING
                message = "Potentially inappropriate content detected"

            logger.warning(f"Toxicity detected: {detected_patterns}")
            return GuardrailResponse(
                result=result,
                message=message,
                confidence=max_severity,
                metadata={
                    "detected_patterns": detected_patterns,
                    "severity_score": max_severity,
                },
            )

        return GuardrailResponse(
            result=GuardrailResult.PASS,
            message="No toxic content detected",
            confidence=0.9,
        )

    def _calculate_pattern_severity(self, pattern: str) -> float:
        """
        Calculate severity score for a detected pattern.

        This is a simple implementation. For production use,
        consider more sophisticated scoring mechanisms.
        """
        # Simple heuristic based on pattern content
        if any(word in pattern for word in ["kill", "murder", "suicide", "ตาย", "ฆ่า"]):
            return 1.0  # Highest severity
        elif any(word in pattern for word in ["harm", "hurt", "ทำร้าย"]):
            return 0.8
        elif any(word in pattern for word in ["stupid", "idiot", "โง่"]):
            return 0.6
        else:
            return 0.5


class HateSpeechValidator(BaseGuardrail):
    """
    Detects hate speech and discriminatory content.

    This validator looks for content that targets individuals or groups
    based on protected characteristics.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.hate_threshold = config.get("threshold", 0.8)

        # Hate speech patterns (basic implementation)
        self.hate_patterns = config.get(
            "patterns",
            [
                # Racial/ethnic slurs and discrimination
                # Note: In production, these patterns should be more comprehensive
                # and regularly updated based on emerging hate speech trends
                # General discriminatory language
                r"\b(hate|despise|disgust).*(race|ethnicity|religion|gender|sexual)\b",
                r"\b(inferior|superior).*(race|ethnicity|people|group)\b",
                # Targeting based on characteristics
                r"\b(all|those).*(people|men|women).*(are|should).*(bad|evil|wrong)\b",
                # Thai hate speech patterns
                r"\b(เกลียด|รังเกียจ).*(เชื้อชาติ|ศาสนา|เพศ)\b",
                r"\b(ด้อยกว่า|เหนือกว่า).*(คน|กลุ่ม|เชื้อชาติ)\b",
            ],
        )

        # Protected characteristics to monitor
        self.protected_characteristics = config.get(
            "protected_characteristics",
            [
                "race",
                "ethnicity",
                "religion",
                "gender",
                "sexual orientation",
                "disability",
                "age",
                "nationality",
                "เชื้อชาติ",
                "ศาสนา",
                "เพศ",
                "อายุ",
                "สัญชาติ",
            ],
        )

    @property
    def name(self) -> str:
        return "HateSpeechValidator"

    def validate(self, input_data: str) -> GuardrailResponse:
        """
        Check for hate speech in the input.

        Args:
            input_data: Text to validate for hate speech

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
        targeted_characteristics = []

        # Check for hate speech patterns
        for pattern in self.hate_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected_patterns.append(pattern)

        # Check for targeting of protected characteristics
        for characteristic in self.protected_characteristics:
            if characteristic.lower() in text:
                targeted_characteristics.append(characteristic)

        # Calculate hate speech score
        hate_score = self._calculate_hate_score(
            detected_patterns, targeted_characteristics
        )

        if detected_patterns and hate_score >= self.hate_threshold:
            logger.warning(f"Hate speech detected: {detected_patterns}")
            return GuardrailResponse(
                result=GuardrailResult.FAIL,
                message="Hate speech detected",
                confidence=hate_score,
                metadata={
                    "detected_patterns": detected_patterns,
                    "targeted_characteristics": targeted_characteristics,
                    "hate_score": hate_score,
                },
            )
        elif detected_patterns or (targeted_characteristics and hate_score > 0.3):
            return GuardrailResponse(
                result=GuardrailResult.WARNING,
                message="Potentially discriminatory content detected",
                confidence=hate_score,
                metadata={
                    "detected_patterns": detected_patterns,
                    "targeted_characteristics": targeted_characteristics,
                    "hate_score": hate_score,
                },
            )

        return GuardrailResponse(
            result=GuardrailResult.PASS,
            message="No hate speech detected",
            confidence=0.9,
        )

    def _calculate_hate_score(
        self, patterns: List[str], characteristics: List[str]
    ) -> float:
        """
        Calculate hate speech score based on detected patterns and characteristics.

        This is a simple implementation. For production use, consider using
        more sophisticated hate speech detection models.
        """
        if not patterns and not characteristics:
            return 0.0

        # Base score for patterns
        pattern_score = min(len(patterns) * 0.3, 0.8)

        # Additional score for targeting protected characteristics
        characteristic_score = min(len(characteristics) * 0.2, 0.5)

        # Combine scores
        total_score = min(pattern_score + characteristic_score, 1.0)

        return total_score
