"""Binary arithmetic operations executed with consistent decimal precision."""

from abc import ABC, abstractmethod
from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DecimalException,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    Underflow,
    localcontext,
)

from app.exceptions import CalculatorError
from app.input_validators import validate_operand

DECIMAL_PRECISION = 28

# Copy this context for each execution; never modify the caller's settings.
_ARITHMETIC_CONTEXT = Context(
    prec=DECIMAL_PRECISION,
    rounding=ROUND_HALF_EVEN,
    Emin=-999999,
    Emax=999999,
    traps=[InvalidOperation, DivisionByZero, Overflow, Underflow],
)


class Operation(ABC):
    """A receiver that calculates a result from exactly two Decimal operands."""

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        """Validate operands and calculate without altering ambient context."""
        validate_operand(left)
        validate_operand(right)
        try:
            with localcontext(_ARITHMETIC_CONTEXT):
                return self._calculate(left, right)
        except DecimalException as error:
            raise CalculatorError(
                "Calculation is outside the supported decimal range."
            ) from error

    @abstractmethod
    def _calculate(self, left: Decimal, right: Decimal) -> Decimal:
        """Implement one operation within the context supplied by execute."""
        # Abstract operations cannot be instantiated or executed directly.
        raise NotImplementedError  # pragma: no cover


class AddOperation(Operation):
    """Add the two operands."""

    def _calculate(self, left: Decimal, right: Decimal) -> Decimal:
        return left + right


class SubtractOperation(Operation):
    """Subtract the right operand from the left operand."""

    def _calculate(self, left: Decimal, right: Decimal) -> Decimal:
        return left - right


class MultiplyOperation(Operation):
    """Multiply the two operands."""

    def _calculate(self, left: Decimal, right: Decimal) -> Decimal:
        return left * right


class DivideOperation(Operation):
    """Divide the left operand by a nonzero right operand."""

    def _calculate(self, left: Decimal, right: Decimal) -> Decimal:
        if right.is_zero():
            raise CalculatorError("Cannot divide by zero.")
        return left / right
