"""Immutable history snapshots used by Calculator undo and redo."""

from dataclasses import dataclass

from app.calculation import Calculation


@dataclass(frozen=True, slots=True)
class CalculatorMemento:
    """Preserve completed calculations, including results and timestamps."""

    calculations: tuple[Calculation, ...]
