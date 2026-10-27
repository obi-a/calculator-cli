"""Number parsing and operand validation through representative inputs."""

from decimal import Decimal, InvalidOperation, localcontext

import pytest

from app.exceptions import CalculatorError
from app.input_validators import parse_number, validate_operand


@pytest.mark.parametrize(
    "text,expected",
    [
        ("2", "2"),
        (".5", "0.5"),
        ("-2.5E-3", "-0.0025"),
        ("0.10000000000000000000000000001", "0.10000000000000000000000000001"),
    ],
)
def test_parse_number(text, expected):
    assert parse_number(text) == Decimal(expected)


@pytest.mark.parametrize("text", ["", "abc", "1.2.3"])
def test_malformed_numbers(text):
    with pytest.raises(CalculatorError, match="Invalid number"):
        parse_number(text)


@pytest.mark.parametrize("text", ["NaN", "Infinity"])
def test_nonfinite_numbers(text):
    with pytest.raises(CalculatorError, match="finite decimal numbers"):
        parse_number(text)


@pytest.mark.parametrize("value", [1.5, "2"])
def test_operands_require_decimal_values(value):
    with pytest.raises(CalculatorError, match="Operands must be Decimal"):
        validate_operand(value)


def test_parsing_preserves_decimal_context():
    with localcontext() as context:
        context.prec = 2
        context.traps[InvalidOperation] = False
        before = str(context)

        assert parse_number("1.23456789") == Decimal("1.23456789")
        with pytest.raises(CalculatorError, match="Invalid number"):
            parse_number("not-a-number")
        assert str(context) == before


@pytest.mark.parametrize(
    "value,allowed",
    [("10", True), ("-10", True), ("10.01", False), ("-10.01", False)],
)
def test_input_magnitude_limit(value, allowed):
    if allowed:
        assert parse_number(value, Decimal(10)) == Decimal(value)
    else:
        with pytest.raises(CalculatorError, match="must not exceed"):
            parse_number(value, Decimal(10))
