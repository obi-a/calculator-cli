"""Command objects that bind an operation to its numerical operands."""

from dataclasses import dataclass
from decimal import Decimal

from app.operations import Operation


@dataclass(frozen=True, slots=True)
class Calculation:
    """An immutable request, ready to execute against its operation receiver."""

    operation: Operation
    left: Decimal
    right: Decimal

    def execute(self) -> Decimal:
        """Delegate arithmetic and validation to the stored operation."""
        return self.operation.execute(self.left, self.right)
