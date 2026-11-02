"""Help decoration and operation discovery when rendering."""

from app.factory import OperationFactory
from app.help_menu import BasicHelpMenu, OperationHelpDecorator
from app.operations import AddOperation


def test_help_updates_when_operations_are_added(monkeypatch):
    monkeypatch.setattr(OperationFactory, "_operations", {"add": AddOperation})
    base_lines = ("  help", "  exit / quit")
    base_menu = BasicHelpMenu(base_lines)
    menu = OperationHelpDecorator(base_menu)

    assert menu.render() == ("  add <number> <number>",) + base_lines

    monkeypatch.setitem(OperationFactory._operations, "sum", AddOperation)

    assert menu.render() == (
        "  add <number> <number>", "  sum <number> <number>",
    ) + base_lines
    assert base_menu.render() == base_lines
