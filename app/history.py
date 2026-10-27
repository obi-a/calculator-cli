"""Bounded calculation history and pandas CSV persistence."""

from collections.abc import Iterable, Sequence
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
import warnings

import pandas as pd

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.exceptions import HistoryError

COLUMNS = ("operation", "operands", "result", "timestamp")


class CalculationHistory:
    """Store completed calculations and validate files before replacing state."""

    def __init__(self, config: CalculatorConfig) -> None:
        self._config = config
        self._entries: list[Calculation] = []

    @property
    def entries(self) -> tuple[Calculation, ...]:
        """Expose entries without allowing mutation outside history management."""
        return tuple(self._entries)

    def replace(self, entries: Iterable[Calculation]) -> None:
        """Validate the complete replacement before keeping its newest entries."""
        entries = list(entries)
        for entry in entries:
            entry.to_record()
        self._entries = entries[-self._config.max_history_size:]

    def add(self, calculation: Calculation) -> None:
        """Append one completed calculation, evicting the oldest if necessary."""
        self.replace((*self._entries, calculation))

    def clear(self) -> None:
        """Remove current entries."""
        self._entries.clear()

    def to_dataframe(
        self, entries: Sequence[Calculation] | None = None
    ) -> pd.DataFrame:
        """Keep Decimal values as text, including their trailing zeros."""
        if entries is None:
            entries = self._entries
        return pd.DataFrame([entry.to_record() for entry in entries], columns=COLUMNS)

    @staticmethod
    def from_dataframe(frame: pd.DataFrame) -> list[Calculation]:
        """Validate every row before making any change to current history."""
        if set(frame.columns) != set(COLUMNS):
            raise HistoryError(
                f"History CSV must contain columns: {', '.join(COLUMNS)}."
            )
        entries = []
        for row_number, record in enumerate(frame.to_dict("records"), start=2):
            try:
                entries.append(Calculation.from_record(record))
            except (ValueError, TypeError) as error:
                raise HistoryError(
                    f"Invalid history row {row_number}: {error}"
                ) from error
        return entries

    def save(self, entries: Sequence[Calculation] | None = None) -> None:
        """Replace the destination only after the complete CSV has been written."""
        destination = self._config.history_file
        temporary_path = None
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(
                mode="w", encoding=self._config.default_encoding, newline="",
                dir=destination.parent, delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                self.to_dataframe(entries).to_csv(stream, index=False)
            temporary_path.replace(destination)
        except (OSError, ValueError) as error:
            raise HistoryError(
                f"Cannot save history to {str(destination)!r}: {error}"
            ) from error
        finally:
            if temporary_path is not None:
                with suppress(OSError):
                    temporary_path.unlink(missing_ok=True)

    def load(self) -> None:
        """Read a CSV explicitly, preserving its values, timestamps, and row order."""
        source = self._config.history_file
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", pd.errors.ParserWarning)
                frame = pd.read_csv(
                    source, dtype=str, keep_default_na=False, index_col=False,
                    encoding=self._config.default_encoding, compression=None,
                )
        except (OSError, ValueError, pd.errors.ParserWarning) as error:
            raise HistoryError(
                f"Cannot load history from {str(source)!r}: {error}"
            ) from error
        self.replace(self.from_dataframe(frame))
