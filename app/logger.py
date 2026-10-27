"""Application-owned file logging with explicit setup and cleanup."""

import logging
from pathlib import Path
import sys

from app.exceptions import ConfigurationError


def _report_error(error: BaseException | None, message: str) -> None:
    """Report a failed log write without attempting to use the file again."""
    print(f"ERROR: Could not write calculator log ({error}): {message}", file=sys.stderr)


class _FileHandler(logging.FileHandler):
    """Keep runtime write failures visible without interrupting calculations."""

    def handleError(self, record: logging.LogRecord) -> None:
        _report_error(sys.exception(), record.getMessage())


class Logger:
    """A small logging facade whose handler belongs only to this instance."""

    def __init__(self, log_file: Path) -> None:
        # Separate instances can share a destination without duplicating records
        # or closing each other's handlers. Never configure the root logger.
        self._logger = logging.getLogger(f"calculator.{id(self)}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            handler = _FileHandler(log_file, mode="a", encoding="utf-8")
        except (OSError, ValueError) as error:
            raise ConfigurationError(
                f"Cannot open log file {str(log_file)!r}: {error}"
            ) from error

        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        self._handler: _FileHandler | None = handler
        self._logger.addHandler(handler)

    def info(self, message: str, *args: object) -> None:
        """Record a normal application event."""
        self._logger.info(message, *args)

    def warning(self, message: str, *args: object) -> None:
        """Record a recoverable command or arithmetic error."""
        self._logger.warning(message, *args)

    def error(self, message: str, *args: object) -> None:
        """Record a failure without an active exception."""
        self._logger.error(message, *args)

    def exception(self, message: str, *args: object) -> None:
        """Record an ERROR with the active exception's traceback."""
        self._logger.exception(message, *args)

    def close(self) -> None:
        """Release this instance's handler; repeated calls are harmless."""
        handler = self._handler
        if handler is None:
            return
        self._handler = None
        self._logger.removeHandler(handler)
        try:
            handler.close()
        except OSError as error:
            _report_error(error, "closing log file")
