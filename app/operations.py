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
from app.input_validators import (
    validate_integer,
    validate_nonzero,
    validate_operand,
)

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
                result = self._calculate(left, right)
                if not result.is_finite():
                    raise CalculatorError("Calculation must produce a finite result.")
                return result
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
        validate_nonzero(right)
        return left / right


class PowerOperation(Operation):
    """Raise the left operand to a real-valued power given by the right operand."""

    def _calculate(self, left: Decimal, right: Decimal) -> Decimal:
        if left.is_zero():
            if right.is_zero():
                raise CalculatorError("Zero to the power of zero is undefined.")
            if right < 0:
                raise CalculatorError("Zero cannot be raised to a negative power.")
        if left < 0:
            validate_integer(right, "Negative bases require an integer exponent.")
        return left ** right


def _is_odd_integer(value: Decimal) -> bool:
    """Check a nonzero integral Decimal without constructing a large integer."""
    parts = value.as_tuple()
    # Positive exponents append zeros; negative exponents remove fractional zeros.
    return parts.exponent <= 0 and parts.digits[parts.exponent - 1] % 2 == 1


class RootOperation(Operation):
    """Calculate a real root with a nonzero integer degree, including reciprocals."""

    def _calculate(self, left: Decimal, right: Decimal) -> Decimal:
        validate_nonzero(right, "Root degree cannot be zero.")
        validate_integer(right, "Root degree must be an integer.")
        if left < 0 and not _is_odd_integer(right):
            raise CalculatorError("Negative numbers require an odd root degree.")
        if left.is_zero():
            if right < 0:
                raise CalculatorError("Zero cannot have a negative root degree.")
            return left
        if left.copy_abs() == 1:
            return +left

        # Guard digits reduce error from rounding the reciprocal degree before power.
        with localcontext() as context:
            context.prec += 12
            result = left.copy_abs() ** (Decimal(1) / right)
            if left < 0:
                result = result.copy_negate()
        return +result


class ModulusOperation(Operation):
    """Return a remainder whose nonzero sign matches the divisor."""

    def _calculate(self, left: Decimal, right: Decimal) -> Decimal:
        validate_nonzero(right)
        remainder = left % right
        # Decimal's native remainder follows the dividend; use divisor-sign modulo.
        if remainder and remainder.is_signed() != right.is_signed():
            remainder += right
        return remainder


class IntDivideOperation(Operation):
    """Return the integer quotient, discarding the fractional part toward zero."""

    def _calculate(self, left: Decimal, right: Decimal) -> Decimal:
        validate_nonzero(right)
        return left // right


class PercentOperation(Operation):
    """Calculate the left operand as a percentage of the right operand."""

    def _calculate(self, left: Decimal, right: Decimal) -> Decimal:
        validate_nonzero(right)
        return (left / right) * Decimal(100)


class AbsDiffOperation(Operation):
    """Return the absolute difference between the two operands."""

    def _calculate(self, left: Decimal, right: Decimal) -> Decimal:
        return (left - right).copy_abs()
