"""Arithmetic examples and boundaries of the fixed Decimal context."""

from decimal import (
    ROUND_UP,
    Decimal,
    DivisionByZero,
    Inexact,
    localcontext,
)

import pytest

from app.exceptions import CalculatorError
from app.operations import (
    AddOperation,
    DivideOperation,
    MultiplyOperation,
    Operation,
    SubtractOperation,
)


@pytest.mark.parametrize(
    "operation_type,left,right,expected",
    [
        (AddOperation, "2", "3", "5"),
        (AddOperation, "-2", "-3", "-5"),
        (AddOperation, "-2", "3", "1"),
        (AddOperation, "0", "0", "0"),
        (AddOperation, "0.1", "0.2", "0.3"),
        (AddOperation, "1e3", "2e2", "1200"),
        (SubtractOperation, "8", "3", "5"),
        (SubtractOperation, "3", "8", "-5"),
        (SubtractOperation, "-2", "-3", "1"),
        (SubtractOperation, "0", "0", "0"),
        (SubtractOperation, "1.25", "0.2", "1.05"),
        (MultiplyOperation, "2", "3", "6"),
        (MultiplyOperation, "-2", "3", "-6"),
        (MultiplyOperation, "-2", "-3", "6"),
        (MultiplyOperation, "0", "5", "0"),
        (MultiplyOperation, "1.25", "0.2", "0.25"),
        (MultiplyOperation, "1e1000", "10", "1e1001"),
        (DivideOperation, "7", "2", "3.5"),
        (DivideOperation, "2", "8", "0.25"),
        (DivideOperation, "-7", "2", "-3.5"),
        (DivideOperation, "-7", "-2", "3.5"),
        (DivideOperation, "0", "5", "0"),
        (DivideOperation, "1.25", "0.5", "2.5"),
        (DivideOperation, "1", "3", "0.3333333333333333333333333333"),
        (
            AddOperation,
            "1234567890123456789012345678",
            "0.5",
            "1234567890123456789012345678",
        ),
        (
            AddOperation,
            "1234567890123456789012345679",
            "0.5",
            "1234567890123456789012345680",
        ),
    ],
)
def test_arithmetic(operation_type, left, right, expected):
    result = operation_type().execute(Decimal(left), Decimal(right))
    assert isinstance(result, Decimal)
    assert result == Decimal(expected)


@pytest.mark.parametrize("left", ["0", "1"])
@pytest.mark.parametrize("right", ["0", "-0", "0.00", "-0E+5"])
def test_division_by_any_zero(left, right):
    with pytest.raises(CalculatorError, match="Cannot divide by zero"):
        DivideOperation().execute(Decimal(left), Decimal(right))


@pytest.mark.parametrize(
    "operation,left,right",
    [
        (MultiplyOperation(), "1e999999", "10"),
        (DivideOperation(), "1e-999999", "1e100"),
    ],
)
def test_arithmetic_range_errors(operation, left, right):
    with pytest.raises(CalculatorError, match="supported decimal range"):
        operation.execute(Decimal(left), Decimal(right))


@pytest.mark.parametrize("invalid", ["NaN", "sNaN", "Infinity", "-Infinity"])
@pytest.mark.parametrize("side", ["left", "right"])
def test_operations_reject_nonfinite_operands(invalid, side):
    operands = {"left": Decimal(1), "right": Decimal(2)}
    operands[side] = Decimal(invalid)
    with pytest.raises(CalculatorError, match="finite decimal numbers"):
        AddOperation().execute(**operands)


@pytest.mark.parametrize("invalid", [1, 1.5, "2", True, None])
def test_operations_reject_implicit_numeric_conversion(invalid):
    with pytest.raises(CalculatorError, match="Operands must be Decimal"):
        AddOperation().execute(invalid, Decimal(2))


def test_operations_isolate_and_restore_context():
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_UP
        context.traps[DivisionByZero] = False
        context.traps[Inexact] = True
        context.flags[Inexact] = True
        before = str(context)

        result = DivideOperation().execute(Decimal(1), Decimal(3))

        assert result == Decimal("0.3333333333333333333333333333")
        assert str(context) == before
        with pytest.raises(CalculatorError):
            MultiplyOperation().execute(Decimal("1e999999"), Decimal(10))
        assert str(context) == before


def test_display_significance_is_preserved():
    result = AddOperation().execute(Decimal("1.20"), Decimal("2.30"))
    assert str(result) == "3.50"


def test_operation_interface_requires_two_operands():
    with pytest.raises(TypeError):
        AddOperation().execute(Decimal(1))
    with pytest.raises(TypeError):
        AddOperation().execute(Decimal(1), Decimal(2), Decimal(3))


def test_operation_base_is_abstract():
    with pytest.raises(TypeError):
        Operation()
