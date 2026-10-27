"""Events and observers for successful calculator commands."""

from dataclasses import dataclass
from decimal import Decimal
import sys
from typing import Generic, Protocol, TypeVar

from app.calculation import Calculation
from app.exceptions import HistoryError
from app.history import CalculationHistory
from app.logger import Logger

EventT = TypeVar("EventT")
EventT_contra = TypeVar("EventT_contra", contravariant=True)


@dataclass(frozen=True, slots=True)
class CalculationEvent:
    """The operation and exact Decimal values from one successful calculation."""

    operation: str
    left: Decimal
    right: Decimal
    result: Decimal


@dataclass(frozen=True, slots=True)
class HistoryChangedEvent:
    """A committed history state, distinct from a new arithmetic calculation."""

    action: str
    calculations: tuple[Calculation, ...]


class Observer(Protocol[EventT_contra]):
    """A subscriber to one kind of immutable event."""

    def update(self, event: EventT_contra) -> None:
        """Respond to an event."""


class CalculationObserver(Observer[CalculationEvent], Protocol):
    """Subscribe to newly performed calculations."""


class HistoryObserver(Observer[HistoryChangedEvent], Protocol):
    """Subscribe to committed history changes."""


class ObserverRegistry(Generic[EventT]):
    """Share ordered registration and failure isolation between event types."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self._observers: list[Observer[EventT]] = []

    def register(self, observer: Observer[EventT]) -> None:
        if not any(existing is observer for existing in self._observers):
            self._observers.append(observer)

    def remove(self, observer: Observer[EventT]) -> None:
        for index, existing in enumerate(self._observers):
            if existing is observer:
                del self._observers[index]
                return

    def notify(self, event: EventT) -> None:
        for observer in tuple(self._observers):
            try:
                observer.update(event)
            except Exception:
                self._logger.exception(
                    "Observer %s failed during %s",
                    type(observer).__name__, type(event).__name__,
                )


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


class AutoSaveObserver:
    """Persist each committed state while keeping IO failures recoverable."""

    def __init__(self, history: CalculationHistory, logger: Logger) -> None:
        self._history = history
        self._logger = logger

    def update(self, event: HistoryChangedEvent) -> None:
        try:
            self._history.save(event.calculations)
        except HistoryError as error:
            self._logger.error("Auto-save failed: %s", error)
            print(f"Warning: Auto-save failed: {error}", file=sys.stderr)
        else:
            self._logger.info("History auto-saved after %s", event.action)
