"""Numerical parsing without float conversion or ambient context changes."""

from decimal import Decimal, InvalidOperation, localcontext

import pytest

from app.exceptions import CalculatorError
from app.input_validators import parse_number, validate_operand


@pytest.mark.parametrize(
    "text,expected",
    [
        ("2", "2"),
        ("-2", "-2"),
        ("+2.5", "2.5"),
        (".5", "0.5"),
        ("1e3", "1000"),
        ("-2.5E-3", "-0.0025"),
        ("0.10000000000000000000000000001", "0.10000000000000000000000000001"),
    ],
)
def test_parse_number(text, expected):
    result = parse_number(text)
    assert isinstance(result, Decimal)
    assert result == Decimal(expected)


@pytest.mark.parametrize(
    "text", ["", "abc", "1.2.3", "1/2", "0x10", "--2", "1e999999999999999999999"]
)
def test_malformed_numbers(text):
    with pytest.raises(CalculatorError, match="Invalid number"):
        parse_number(text)


@pytest.mark.parametrize("text", ["NaN", "sNaN", "Infinity", "+Infinity", "-inf"])
def test_nonfinite_numbers(text):
    with pytest.raises(CalculatorError, match="finite decimal numbers"):
        parse_number(text)


def test_valid_operand_requires_no_conversion():
    assert validate_operand(Decimal("1.20")) is None


def test_parsing_does_not_depend_on_or_change_caller_context():
    with localcontext() as context:
        context.prec = 2
        context.traps[InvalidOperation] = False
        before = str(context)

        assert parse_number("1.23456789") == Decimal("1.23456789")
        with pytest.raises(CalculatorError, match="Invalid number"):
            parse_number("not-a-number")
        assert str(context) == before
