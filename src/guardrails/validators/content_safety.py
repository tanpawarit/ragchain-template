"""
Content safety guardrails.

This module contains validators that check for harmful, toxic,
or inappropriate content in both inputs and outputs.
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


class ToxicityConfig(BaseGuardrailConfig):
    """Configuration for toxicity validator."""

    threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Toxicity detection threshold"
    )
    patterns: List[str] = Field(
        default=[
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
        description="Regex patterns to detect toxic content",
    )


class ToxicityValidator(BaseGuardrail):
    """
    Detects toxic content in text.

    This is a basic implementation using pattern matching.
    For production use, consider using specialized toxicity detection models
    like Perspective API or similar services.
    """

    guardrail_name = "ToxicityValidator"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.config_model = ToxicityConfig(**config)
        self.toxicity_threshold = self.config_model.threshold
        self.toxic_patterns = self.config_model.patterns

        self.severity_weights = {
            "violence": 1.0,
            "harassment": 0.7,
            "self_harm": 1.0,
            "general_toxicity": 0.5,
        }

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


class HateSpeechConfig(BaseGuardrailConfig):
    """Configuration for hate speech validator."""

    threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Hate speech detection threshold"
    )
    patterns: List[str] = Field(
        default=[
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
        description="Regex patterns to detect hate speech",
    )
    protected_characteristics: List[str] = Field(
        default=[
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
        description="Protected characteristics to monitor",
    )


class HateSpeechValidator(BaseGuardrail):
    """
    Detects hate speech and discriminatory content.

    This validator looks for content that targets individuals or groups
    based on protected characteristics.
    """

    guardrail_name = "HateSpeechValidator"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.config_model = HateSpeechConfig(**config)
        self.hate_threshold = self.config_model.threshold
        self.hate_patterns = self.config_model.patterns
        self.protected_characteristics = self.config_model.protected_characteristics

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
            if characteristic in text:
                targeted_characteristics.append(characteristic)

        if detected_patterns or targeted_characteristics:
            hate_score = self._calculate_hate_score(
                detected_patterns, targeted_characteristics
            )

            if hate_score >= self.hate_threshold:
                result = GuardrailResult.FAIL
                message = "Hate speech detected"
            else:
                result = GuardrailResult.WARNING
                message = "Potentially discriminatory content detected"

            logger.warning(f"Hate speech detected: {detected_patterns}")
            return GuardrailResponse(
                result=result,
                message=message,
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
        Calculate hate speech severity score.

        Args:
            patterns: Detected hate speech patterns
            characteristics: Targeted protected characteristics

        Returns:
            Hate speech score between 0 and 1
        """
        # Base score from pattern detection
        pattern_score = min(len(patterns) * 0.3, 1.0)

        # Additional score from targeting protected characteristics
        characteristic_score = min(len(characteristics) * 0.2, 0.5)

        # Combine scores
        total_score = pattern_score + characteristic_score

        return min(total_score, 1.0)
