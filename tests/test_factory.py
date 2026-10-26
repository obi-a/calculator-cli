"""Supported operation creation and rejection of unknown names."""

import pytest

from app.exceptions import CalculatorError
from app.factory import OperationFactory
from app.operations import (
    AddOperation,
    DivideOperation,
    MultiplyOperation,
    SubtractOperation,
)


@pytest.mark.parametrize(
    "name,expected_type",
    [
        ("add", AddOperation),
        ("subtract", SubtractOperation),
        ("multiply", MultiplyOperation),
        ("divide", DivideOperation),
    ],
)
def test_factory_creates_correct_fresh_operation(name, expected_type):
    first = OperationFactory.create(name)
    assert isinstance(first, expected_type)
    assert first is not OperationFactory.create(name)


@pytest.mark.parametrize("name", ["ADD", "Add", " add ", "\tAdD\n"])
def test_factory_normalizes_names(name):
    assert isinstance(OperationFactory.create(name), AddOperation)


@pytest.mark.parametrize(
    "name",
    ["power", "root", "modulus", "int_divide", "percent", "abs_diff", "unknown", ""],
)
def test_factory_rejects_unknown_and_deferred_operations(name):
    with pytest.raises(CalculatorError, match="Unknown operation"):
        OperationFactory.create(name)


def test_factory_exposes_only_supported_commands():
    assert OperationFactory.supported_operations() == (
        "add", "subtract", "multiply", "divide"
    )
