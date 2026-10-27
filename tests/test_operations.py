"""Representative arithmetic, domain errors, and Decimal precision."""

from decimal import ROUND_UP, Decimal, DivisionByZero, Inexact, localcontext

import pytest

from app.exceptions import CalculatorError
from app.operations import (
    AbsDiffOperation,
    AddOperation,
    DivideOperation,
    IntDivideOperation,
    ModulusOperation,
    MultiplyOperation,
    Operation,
    PercentOperation,
    PowerOperation,
    RootOperation,
    SubtractOperation,
)


@pytest.mark.parametrize(
    "operation_type,left,right,expected",
    [
        (AddOperation, "0.1", "0.2", "0.3"),
        (SubtractOperation, "3", "8", "-5"),
        (MultiplyOperation, "-2", "1e3", "-2e3"),
        (DivideOperation, "7", "2", "3.5"),
        (DivideOperation, "0", "5", "0"),
        (PowerOperation, "2", "3", "8"),
        (PowerOperation, "2", "-3", "0.125"),
        (PowerOperation, "-2", "-3", "-0.125"),
        (PowerOperation, "-2", "4", "16"),
        (PowerOperation, "9", "0.5", "3"),
        (PowerOperation, "0", "2", "0"),
        (PowerOperation, "3", "0", "1"),
        (RootOperation, "16", "2", "4"),
        (RootOperation, "16", "-2", "0.25"),
        (RootOperation, "-8", "3.000", "-2"),
        (RootOperation, "-8", "-3", "-0.5"),
        (RootOperation, "0", "3", "0"),
        (RootOperation, "1", "2", "1"),
        (RootOperation, "-1", "3", "-1"),
        (ModulusOperation, "7", "3", "1"),
        (ModulusOperation, "-5.5", "2", "0.5"),
        (ModulusOperation, "7", "-3", "-2"),
        (ModulusOperation, "-7", "-3", "-1"),
        (ModulusOperation, "6", "3", "0"),
        (IntDivideOperation, "-7", "3", "-2"),
        (IntDivideOperation, "1", "3", "0"),
        (IntDivideOperation, "1.99999999999999999999999999999", "1", "1"),
        (IntDivideOperation, "-1.99999999999999999999999999999", "1", "-1"),
        (PercentOperation, "25", "200", "12.5"),
        (AbsDiffOperation, "-3", "8", "11"),
    ],
)
def test_arithmetic(operation_type, left, right, expected):
    result = operation_type().execute(Decimal(left), Decimal(right))
    assert isinstance(result, Decimal)
    assert result == Decimal(expected)


@pytest.mark.parametrize(
    "left,expected",
    [
        ("1234567890123456789012345678", "1234567890123456789012345678"),
        ("1234567890123456789012345679", "1234567890123456789012345680"),
    ],
)
def test_round_half_even(left, expected):
    assert AddOperation().execute(Decimal(left), Decimal("0.5")) == Decimal(expected)


@pytest.mark.parametrize(
    "operation_type,zero",
    [
        (DivideOperation, "0"),
        (ModulusOperation, "-0"),
        (IntDivideOperation, "0.00"),
        (PercentOperation, "-0E+5"),
    ],
)
def test_division_by_zero(operation_type, zero):
    with pytest.raises(CalculatorError, match="Cannot divide by zero"):
        operation_type().execute(Decimal(1), Decimal(zero))


@pytest.mark.parametrize(
    "operation_type,left,right,message",
    [
        (PowerOperation, "0", "0", "power of zero is undefined"),
        (PowerOperation, "-0", "-1", "negative power"),
        (PowerOperation, "-2", "0.5", "integer exponent"),
        (RootOperation, "16", "0", "degree cannot be zero"),
        (RootOperation, "16", "0.5", "degree must be an integer"),
        (RootOperation, "-16", "2", "odd root degree"),
        (RootOperation, "-16", "3e1", "odd root degree"),
        (RootOperation, "-0", "-2", "negative root degree"),
    ],
)
def test_domain_errors(operation_type, left, right, message):
    with pytest.raises(CalculatorError, match=message):
        operation_type().execute(Decimal(left), Decimal(right))


@pytest.mark.parametrize(
    "operation_type,left,right",
    [
        (MultiplyOperation, "1e999999", "10"),
        (DivideOperation, "1e-999999", "1e100"),
        (IntDivideOperation, "1e28", "1"),
    ],
)
def test_decimal_range_errors(operation_type, left, right):
    with pytest.raises(CalculatorError, match="supported decimal range"):
        operation_type().execute(Decimal(left), Decimal(right))


@pytest.mark.parametrize("left,right", [("NaN", "1"), ("1", "Infinity")])
def test_nonfinite_operands(left, right):
    with pytest.raises(CalculatorError, match="finite decimal numbers"):
        AddOperation().execute(Decimal(left), Decimal(right))


def test_arithmetic_restores_decimal_context_after_success_and_error():
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_UP
        context.traps[DivisionByZero] = False
        context.traps[Inexact] = True
        context.flags[Inexact] = True
        before = str(context)

        assert DivideOperation().execute(Decimal(1), Decimal(3)) == Decimal(
            "0.3333333333333333333333333333"
        )
        assert RootOperation().execute(Decimal(2), Decimal(2)) == Decimal(
            "1.414213562373095048801688724"
        )
        assert str(context) == before
        with pytest.raises(CalculatorError):
            MultiplyOperation().execute(Decimal("1e999999"), Decimal(10))
        assert str(context) == before


def test_operations_reject_nonfinite_results():
    class NonFiniteOperation(Operation):
        def _calculate(self, left, right):
            return Decimal("Infinity")

    with pytest.raises(CalculatorError, match="must produce a finite result"):
        NonFiniteOperation().execute(Decimal(1), Decimal(2))


def test_display_significance_is_preserved():
    assert str(AddOperation().execute(Decimal("1.20"), Decimal("2.30"))) == "3.50"
