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
        (PowerOperation, "2", "3", "8"),
        (PowerOperation, "2", "-3", "0.125"),
        (PowerOperation, "-2", "3", "-8"),
        (PowerOperation, "-2", "4", "16"),
        (PowerOperation, "-2", "-3", "-0.125"),
        (PowerOperation, "-2", "3.0", "-8"),
        (PowerOperation, "9", "0.5", "3"),
        (PowerOperation, "0", "2", "0"),
        (PowerOperation, "3", "0", "1"),
        (PowerOperation, "0.5", "2", "0.25"),
        (PowerOperation, "1e2", "2", "1e4"),
        (RootOperation, "8", "3", "2"),
        (RootOperation, "27", "3", "3"),
        (RootOperation, "16", "4", "2"),
        (RootOperation, "16", "-2", "0.25"),
        (RootOperation, "-8", "3", "-2"),
        (RootOperation, "-8", "-3", "-0.5"),
        (RootOperation, "-8", "3.000", "-2"),
        (RootOperation, "81", "2", "9"),
        (RootOperation, "2", "2", "1.414213562373095048801688724"),
        (RootOperation, "2", "3", "1.259921049894873164767210607"),
        (RootOperation, "-32", "5", "-2"),
        (RootOperation, "-32", "-5", "-0.5"),
        (RootOperation, "0", "3", "0"),
        (RootOperation, "-0", "2", "0"),
        (RootOperation, "1", "1e1000001", "1"),
        (RootOperation, "-1", "100000000000000000000000000001", "-1"),
        (RootOperation, "-1", "-100000000000000000000000000001", "-1"),
        (RootOperation, "1e6", "3", "100"),
        (RootOperation, "5.25", "1", "5.25"),
        (
            RootOperation,
            "1.2345678901234567890123456789",
            "1",
            "1.234567890123456789012345679",
        ),
        (ModulusOperation, "5", "2", "1"),
        (ModulusOperation, "-7", "3", "2"),
        (ModulusOperation, "7", "-3", "-2"),
        (ModulusOperation, "-7", "-3", "-1"),
        (ModulusOperation, "0", "3", "0"),
        (ModulusOperation, "6", "3", "0"),
        (ModulusOperation, "5.5", "2", "1.5"),
        (ModulusOperation, "-5.5", "2", "0.5"),
        (ModulusOperation, "5.5", "-2", "-0.5"),
        (ModulusOperation, "1e3", "3", "1"),
        (IntDivideOperation, "7", "2", "3"),
        (IntDivideOperation, "-7", "3", "-2"),
        (IntDivideOperation, "7", "-3", "-2"),
        (IntDivideOperation, "-7", "-3", "2"),
        (IntDivideOperation, "0", "5", "0"),
        (IntDivideOperation, "1.2", "0.5", "2"),
        (IntDivideOperation, "1", "3", "0"),
        (IntDivideOperation, "-1", "3", "0"),
        (IntDivideOperation, "1e3", "3", "333"),
        (IntDivideOperation, "0.99999999999999999999999999999", "1", "0"),
        (IntDivideOperation, "1.99999999999999999999999999999", "1", "1"),
        (IntDivideOperation, "-1.99999999999999999999999999999", "1", "-1"),
        (PercentOperation, "25", "200", "12.5"),
        (PercentOperation, "50", "200", "25"),
        (PercentOperation, "-25", "200", "-12.5"),
        (PercentOperation, "25", "-200", "-12.5"),
        (PercentOperation, "-25", "-200", "12.5"),
        (PercentOperation, "0", "20", "0"),
        (PercentOperation, "20", "5", "400"),
        (PercentOperation, "0.1", "0.2", "50"),
        (PercentOperation, "1e2", "1e3", "10"),
        (PercentOperation, "1", "3", "33.33333333333333333333333333"),
        (AbsDiffOperation, "3", "8", "5"),
        (AbsDiffOperation, "8", "3", "5"),
        (AbsDiffOperation, "-3", "-8", "5"),
        (AbsDiffOperation, "-3", "8", "11"),
        (AbsDiffOperation, "8", "-3", "11"),
        (AbsDiffOperation, "0", "0", "0"),
        (AbsDiffOperation, "0.1", "0.3", "0.2"),
        (AbsDiffOperation, "1e3", "2e3", "1e3"),
    ],
)
def test_arithmetic(operation_type, left, right, expected):
    result = operation_type().execute(Decimal(left), Decimal(right))
    assert isinstance(result, Decimal)
    assert result == Decimal(expected)


@pytest.mark.parametrize("left", ["0", "1"])
@pytest.mark.parametrize("right", ["0", "-0", "0.00", "-0E+5"])
@pytest.mark.parametrize(
    "operation_type",
    [DivideOperation, ModulusOperation, IntDivideOperation, PercentOperation],
)
def test_division_by_any_zero(operation_type, left, right):
    with pytest.raises(CalculatorError, match="Cannot divide by zero"):
        operation_type().execute(Decimal(left), Decimal(right))


@pytest.mark.parametrize(
    "operation_type,left,right,message",
    [
        (PowerOperation, "0", "0", "power of zero is undefined"),
        (PowerOperation, "-0", "0", "power of zero is undefined"),
        (PowerOperation, "0", "-1", "negative power"),
        (PowerOperation, "-0", "-2", "negative power"),
        (PowerOperation, "-2", "0.5", "integer exponent"),
        (PowerOperation, "-2", "-0.5", "integer exponent"),
        (RootOperation, "16", "0", "degree cannot be zero"),
        (RootOperation, "16", "-0", "degree cannot be zero"),
        (RootOperation, "16", "0.5", "degree must be an integer"),
        (RootOperation, "16", "-0.5", "degree must be an integer"),
        (RootOperation, "-16", "2", "odd root degree"),
        (RootOperation, "-16", "-2", "odd root degree"),
        (RootOperation, "-1", "3e1", "odd root degree"),
        (RootOperation, "-1", "100000000000000000000000000002", "odd root degree"),
        (RootOperation, "0", "-3", "negative root degree"),
        (RootOperation, "-0", "-2", "negative root degree"),
    ],
)
def test_power_and_root_domain_errors(operation_type, left, right, message):
    with pytest.raises(CalculatorError, match=message):
        operation_type().execute(Decimal(left), Decimal(right))


@pytest.mark.parametrize(
    "operation,left,right",
    [
        (MultiplyOperation(), "1e999999", "10"),
        (DivideOperation(), "1e-999999", "1e100"),
        (PowerOperation(), "1e999999", "2"),
        (PowerOperation(), "1e-999999", "2"),
        (RootOperation(), "1e-1000000", "-1"),
        (RootOperation(), "1e-2000100", "2"),
        (IntDivideOperation(), "1e28", "1"),
        (ModulusOperation(), "1e29", "3"),
        (PercentOperation(), "1e999999", "1"),
        (PercentOperation(), "1e-999999", "1e100"),
        (AbsDiffOperation(), "9e999999", "-9e999999"),
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


@pytest.mark.parametrize(
    "operation_type,left,right,expected",
    [
        (DivideOperation, "1", "3", "0.3333333333333333333333333333"),
        (PowerOperation, "2", "-3", "0.125"),
        (RootOperation, "2", "2", "1.414213562373095048801688724"),
        (ModulusOperation, "-7", "3", "2"),
        (IntDivideOperation, "1.99999999999999999999999999999", "1", "1"),
        (PercentOperation, "25", "200", "12.5"),
        (AbsDiffOperation, "3", "8", "5"),
    ],
)
def test_operations_isolate_and_restore_context(operation_type, left, right, expected):
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_UP
        context.traps[DivisionByZero] = False
        context.traps[Inexact] = True
        context.flags[Inexact] = True
        before = str(context)

        result = operation_type().execute(Decimal(left), Decimal(right))

        assert result == Decimal(expected)
        assert str(context) == before
        with pytest.raises(CalculatorError):
            MultiplyOperation().execute(Decimal("1e999999"), Decimal(10))
        assert str(context) == before


@pytest.mark.parametrize("result", ["Infinity", "-Infinity", "NaN"])
def test_shared_execution_boundary_rejects_nonfinite_results(result):
    class NonFiniteOperation(Operation):
        def _calculate(self, left, right):
            return Decimal(result)

    with pytest.raises(CalculatorError, match="must produce a finite result"):
        NonFiniteOperation().execute(Decimal(1), Decimal(2))


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
