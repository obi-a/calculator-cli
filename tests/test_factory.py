"""Supported operation creation and rejection of unknown names."""

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
    PercentOperation,
    PowerOperation,
    RootOperation,
    SubtractOperation,
)


@pytest.mark.parametrize(
    "name,expected_type",
    [
        ("add", AddOperation),
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
def test_factory_creates_correct_fresh_operation(name, expected_type):
    first = OperationFactory.create(name)
    assert isinstance(first, expected_type)
    assert first is not OperationFactory.create(name)


@pytest.mark.parametrize(
    "name,expected_type",
    [
        ("ADD", AddOperation),
        ("Add", AddOperation),
        (" add ", AddOperation),
        ("\tAdD\n", AddOperation),
        (" PoWeR ", PowerOperation),
        ("RoOt", RootOperation),
        ("MODULUS", ModulusOperation),
        ("INT_DIVIDE", IntDivideOperation),
        ("PERCENT", PercentOperation),
        ("ABS_DIFF", AbsDiffOperation),
    ],
)
def test_factory_normalizes_names(name, expected_type):
    assert isinstance(OperationFactory.create(name), expected_type)


@pytest.mark.parametrize(
    "name",
    ["unknown", "", "sqrt", "addition"],
)
def test_factory_rejects_unknown_operations(name):
    with pytest.raises(CalculatorError, match="Unknown operation"):
        OperationFactory.create(name)


def test_factory_exposes_only_supported_commands():
    assert OperationFactory.supported_operations() == (
        "add", "subtract", "multiply", "divide", "power", "root", "modulus",
        "int_divide", "percent", "abs_diff"
    )
