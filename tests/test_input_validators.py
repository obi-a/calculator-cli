"""Numerical parsing without float conversion or ambient context changes."""

from decimal import Decimal, InvalidOperation, localcontext

import pytest

from app.exceptions import CalculatorError
from app.input_validators import (
    parse_number,
    validate_integer,
    validate_nonzero,
    validate_operand,
)


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


@pytest.mark.parametrize("value", ["0", "-0", "0.00", "-0E+5"])
def test_nonzero_validator_rejects_all_zero_representations(value):
    with pytest.raises(CalculatorError, match="Cannot divide by zero"):
        validate_nonzero(Decimal(value))


def test_nonzero_validator_accepts_nonzero_values_and_customizes_errors():
    assert validate_nonzero(Decimal("-0.001")) is None
    with pytest.raises(CalculatorError, match="Root degree cannot be zero"):
        validate_nonzero(Decimal(0), "Root degree cannot be zero.")


@pytest.mark.parametrize("value", ["0", "-3", "3.000", "3E2"])
def test_integer_validator_accepts_exact_integer_values(value):
    assert validate_integer(Decimal(value), "An integer is required.") is None


@pytest.mark.parametrize("value", ["1.5", "-2.5"])
def test_integer_validator_rejects_fractional_values(value):
    with pytest.raises(CalculatorError, match="An integer is required"):
        validate_integer(Decimal(value), "An integer is required.")


def test_parsing_does_not_depend_on_or_change_caller_context():
    with localcontext() as context:
        context.prec = 2
        context.traps[InvalidOperation] = False
        before = str(context)

        assert parse_number("1.23456789") == Decimal("1.23456789")
        with pytest.raises(CalculatorError, match="Invalid number"):
            parse_number("not-a-number")
        assert str(context) == before
