"""Command objects that bind an operation to its numerical operands."""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext

from app.exceptions import CalculatorError
from app.factory import OperationFactory
from app.input_validators import parse_number
from app.operations import Operation


@dataclass(frozen=True, slots=True)
class Calculation:
    """An immutable request, ready to execute against its operation receiver."""

    operation: Operation
    left: Decimal
    right: Decimal
    result: Decimal | None = field(default=None, kw_only=True)
    timestamp: datetime | None = field(default=None, kw_only=True)

    @property
    def operation_name(self) -> str:
        """Use the same operation names as command dispatch and CSV loading."""
        return OperationFactory.name_for(self.operation)

    def execute(self) -> Decimal:
        """Delegate arithmetic and validation to the stored operation."""
        return self.operation.execute(self.left, self.right)

    def complete(self, decimal_places: int = 28) -> "Calculation":
        """Execute once and capture a rounded result and UTC timestamp."""
        result = self.execute()
        if result.as_tuple().exponent < -decimal_places:
            context = Context(
                prec=max(28, result.adjusted() + decimal_places + 2),
                rounding=ROUND_HALF_EVEN,
            )
            with localcontext(context):
                result = result.quantize(Decimal((0, (1,), -decimal_places)))
        return replace(self, result=result, timestamp=datetime.now(timezone.utc))

    def to_record(self) -> dict[str, str]:
        """Serialize a completed calculation without introducing floats."""
        if self.result is None or self.timestamp is None:
            raise CalculatorError("Only completed calculations can be recorded.")
        return {
            "operation": self.operation_name,
            "left": str(self.left),
            "right": str(self.right),
            "result": str(self.result),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_record(cls, record: Mapping[str, str]) -> "Calculation":
        """Restore saved values without applying today's limits or re-executing."""
        timestamp = datetime.fromisoformat(record["timestamp"])
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise CalculatorError("History timestamps must include a timezone.")
        return cls(
            OperationFactory.create(record["operation"]),
            parse_number(record["left"]),
            parse_number(record["right"]),
            result=parse_number(record["result"]),
            timestamp=timestamp,
        )
