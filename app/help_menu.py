"""Help-menu components and a decorator for registered arithmetic operations."""

from dataclasses import dataclass
from typing import Protocol

from app.factory import OperationFactory


class HelpMenu(Protocol):
    """Shared rendering interface for menus and their decorators."""

    def render(self) -> tuple[str, ...]:
        """Return display lines without printing them."""


@dataclass(frozen=True, slots=True)
class BasicHelpMenu(HelpMenu):
    """The undecorated session commands, examples, and input rules."""

    lines: tuple[str, ...]

    def render(self) -> tuple[str, ...]:
        """Return the base menu unchanged."""
        return self.lines


@dataclass(frozen=True, slots=True)
class OperationHelpDecorator(HelpMenu):
    """Wrap a menu with arithmetic commands from the current factory registry."""

    menu: HelpMenu

    def render(self) -> tuple[str, ...]:
        """Read available operations on each call and delegate to the wrapped menu."""
        operation_lines = tuple(
            f"  {name} <number> <number>"
            for name in OperationFactory.supported_operations()
        )
        return operation_lines + self.menu.render()
