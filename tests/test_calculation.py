"""Command objects retain their parameters and delegate to a receiver."""

from dataclasses import FrozenInstanceError
from decimal import Decimal, Inexact, localcontext
from unittest.mock import Mock

import pytest

from app.calculation import Calculation
from app.exceptions import CalculatorError
from app.factory import OperationFactory
from app.operations import AddOperation, DivideOperation, Operation


def test_command_delegates_stored_operands_to_receiver():
    operation = Mock(spec=Operation)
    operation.execute.return_value = Decimal("3.50")
    command = Calculation(operation, Decimal("1.20"), Decimal("2.30"))

    assert command.execute() == Decimal("3.50")
    operation.execute.assert_called_once_with(Decimal("1.20"), Decimal("2.30"))


def test_command_can_be_executed_repeatedly_without_changing_operands():
    command = Calculation(AddOperation(), Decimal("0.1"), Decimal("0.2"))
    assert command.execute() == command.execute() == Decimal("0.3")
    assert (command.left, command.right) == (Decimal("0.1"), Decimal("0.2"))


@pytest.mark.parametrize(
    "field,value",
    [("left", Decimal(9)), ("right", Decimal(9)), ("operation", DivideOperation())],
)
def test_command_bindings_are_immutable(field, value):
    command = Calculation(AddOperation(), Decimal(1), Decimal(2))
    with pytest.raises(FrozenInstanceError):
        setattr(command, field, value)


def test_command_preserves_receiver_validation_errors():
    command = Calculation(DivideOperation(), Decimal(1), Decimal(0))
    with pytest.raises(CalculatorError, match="Cannot divide by zero"):
        command.execute()


@pytest.mark.parametrize(
    "operation,left,right,places,expected",
    [
        ("power", "2", "-3", 2, "0.12"),
        ("add", "0.135", "0", 2, "0.14"),
        ("add", "1.20", "2.30", 4, "3.50"),
        ("divide", "7", "2", 0, "4"),
    ],
)
def test_completed_calculations_limit_decimal_places(
    operation, left, right, places, expected
):
    command = Calculation(
        OperationFactory.create(operation), Decimal(left), Decimal(right)
    )
    with localcontext() as context:
        context.prec = 3
        context.traps[Inexact] = True
        before = str(context)
        completed = command.complete(places)
        assert str(context) == before

    assert command.result is None
    assert str(completed.result) == expected
    assert completed.timestamp.utcoffset().total_seconds() == 0


def test_unexecuted_commands_cannot_be_serialized():
    with pytest.raises(CalculatorError, match="Only completed calculations"):
        Calculation(AddOperation(), Decimal(1), Decimal(2)).to_record()
