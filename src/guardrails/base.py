"""
Base classes and interfaces for the guardrails system.

This module defines the core abstractions and data structures used
throughout the guardrails package.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field


class GuardrailResult(str, Enum):
    """Enumeration of possible guardrail validation results."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


class GuardrailResponse(BaseModel):
    """Response object containing guardrail validation results."""

    result: GuardrailResult
    message: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(default=None)

    def is_passed(self) -> bool:
        """Check if the guardrail validation passed."""
        return self.result == GuardrailResult.PASS

    def is_failed(self) -> bool:
        """Check if the guardrail validation failed."""
        return self.result == GuardrailResult.FAIL

    def is_warning(self) -> bool:
        """Check if the guardrail validation resulted in a warning."""
        return self.result == GuardrailResult.WARNING


class BaseGuardrailConfig(BaseModel):
    """Base configuration model for guardrails."""

    enabled: bool = True

    class Config:
        extra = "allow"  # Allow additional fields for extensibility


class BaseGuardrail(ABC):
    """
    Abstract base class for all guardrail validators.

    This class defines the interface that all guardrail implementations
    must follow. Each guardrail should validate specific aspects of the
    RAG system's inputs, outputs, or intermediate data.
    """

    # Class variable to store the name of the guardrail
    guardrail_name: ClassVar[str]

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the guardrail with configuration.

        Args:
            config: Configuration dictionary for this guardrail
        """
        self.config = config
        self.enabled = config.get("enabled", True)

    @abstractmethod
    def validate(self, input_data: Any) -> GuardrailResponse:
        """
        Validate input data and return validation result.

        Args:
            input_data: The data to validate (type depends on guardrail)

        Returns:
            GuardrailResponse containing validation results
        """
        pass

    @property
    def name(self) -> str:
        """Return the unique name of this guardrail."""
        return getattr(self, "guardrail_name", self.__class__.__name__)

    def is_enabled(self) -> bool:
        """Check if this guardrail is enabled."""
        return self.enabled
