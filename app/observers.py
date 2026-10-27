"""Events and observers for successful calculator commands."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.logger import Logger


@dataclass(frozen=True, slots=True)
class CalculationEvent:
    """The operation and exact Decimal values from one successful calculation."""

    operation: str
    left: Decimal
    right: Decimal
    result: Decimal


class CalculationObserver(Protocol):
    """Observers respond to immutable events without re-executing arithmetic."""

    def update(self, event: CalculationEvent) -> None:
        """Respond to a completed calculation."""


class LoggingObserver:
    """Record successful calculations through the application's Logger."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def update(self, event: CalculationEvent) -> None:
        """Preserve Decimal significance and scientific notation in the log."""
        self._logger.info(
            "Calculation operation=%s left=%s right=%s result=%s",
            event.operation, event.left, event.right, event.result,
        )
