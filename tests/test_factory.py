"""Operation registration, name normalization, and unknown commands."""

from unittest.mock import Mock

import pytest

from app.exceptions import CalculatorError
from app.factory import OperationFactory
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
    "name,expected_type",
    [
        (" ADD ", AddOperation),
        ("subtract", SubtractOperation),
        ("multiply", MultiplyOperation),
        ("divide", DivideOperation),
        ("power", PowerOperation),
        ("root", RootOperation),
        ("modulus", ModulusOperation),
        ("int_divide", IntDivideOperation),
        ("percent", PercentOperation),
        ("abs_diff", AbsDiffOperation),
    ],
)
def test_factory_creates_operations(name, expected_type):
    operation = OperationFactory.create(name)
    assert isinstance(operation, expected_type)
    assert operation is not OperationFactory.create(name)
    assert OperationFactory.name_for(operation) == name.strip().lower()


@pytest.mark.parametrize("name", ["unknown", ""])
def test_factory_rejects_unknown_operations(name):
    with pytest.raises(CalculatorError, match="Unknown operation"):
        OperationFactory.create(name)


def test_factory_lists_supported_commands():
    assert OperationFactory.supported_operations() == (
        "add", "subtract", "multiply", "divide", "power", "root", "modulus",
        "int_divide", "percent", "abs_diff",
    )


def test_factory_rejects_unregistered_receivers():
    with pytest.raises(CalculatorError, match="Unregistered operation"):
        OperationFactory.name_for(Mock(spec=Operation))
