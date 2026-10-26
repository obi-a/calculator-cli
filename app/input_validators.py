"""Shared validation for numerical text and Decimal operands."""

from decimal import Context, Decimal, InvalidOperation

from app.exceptions import CalculatorError


def validate_operand(value: Decimal) -> None:
    """Require a finite Decimal, avoiding implicit conversion from floats."""
    if not isinstance(value, Decimal):
        raise CalculatorError("Operands must be Decimal numbers.")
    if not value.is_finite():
        raise CalculatorError("Operands must be finite decimal numbers.")


def validate_nonzero(
    value: Decimal, message: str = "Cannot divide by zero."
) -> None:
    """Require an already validated operand to be nonzero, including signed zero."""
    if value.is_zero():
        raise CalculatorError(message)


def validate_integer(value: Decimal, message: str) -> None:
    """Require a finite operand to be integral without rounding or float conversion."""
    if value != value.to_integral_value():
        raise CalculatorError(message)


def parse_number(text: str) -> Decimal:
    """Parse numerical text without introducing binary floating-point error."""
    try:
        # A separate context also keeps invalid input from setting caller flags.
        value = Decimal(text, context=Context(traps=[InvalidOperation]))
    except InvalidOperation as error:
        raise CalculatorError(
            f"Invalid number {text!r}. Use a finite decimal number."
        ) from error
    validate_operand(value)
    return value
