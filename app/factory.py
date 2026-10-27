"""Creation of supported operations through a single explicit registry."""

from typing import ClassVar

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


class OperationFactory:
    """Construct operation receivers without coupling the REPL to their types."""

    _operations: ClassVar[dict[str, type[Operation]]] = {
        "add": AddOperation,
        "subtract": SubtractOperation,
        "multiply": MultiplyOperation,
        "divide": DivideOperation,
        "power": PowerOperation,
        "root": RootOperation,
        "modulus": ModulusOperation,
        "int_divide": IntDivideOperation,
        "percent": PercentOperation,
        "abs_diff": AbsDiffOperation,
    }

    @classmethod
    def create(cls, name: str) -> Operation:
        """Return a fresh operation or report an unsupported command name."""
        normalized_name = name.strip().lower()
        operation_type = cls._operations.get(normalized_name)
        if operation_type is None:
            raise CalculatorError(
                f"Unknown operation {normalized_name!r}. "
                "Type 'help' for supported commands."
            )
        return operation_type()

    @classmethod
    def supported_operations(cls) -> tuple[str, ...]:
        """Return registered names in their help-display order."""
        return tuple(cls._operations)

    @classmethod
    def name_for(cls, operation: Operation) -> str:
        """Find a receiver's canonical name using the existing registry."""
        for name, operation_type in cls._operations.items():
            if type(operation) is operation_type:
                return name
        raise CalculatorError(f"Unregistered operation: {type(operation).__name__}.")
