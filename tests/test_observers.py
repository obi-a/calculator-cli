"""Calculation events, observer registration, and failure isolation."""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.exceptions import CalculatorError
from app.observers import CalculationEvent, CalculationObserver


def test_observers_receive_calculation_details(calculator):
    observer = Mock(spec=CalculationObserver)
    calculator.register_observer(observer)
    calculator.execute_line("add 1.20 2.30")

    observer.update.assert_called_once_with(
        CalculationEvent("add", Decimal("1.20"), Decimal("2.30"), Decimal("3.50"))
    )


def test_registering_twice_and_removing_observers(calculator):
    observer = Mock(spec=CalculationObserver)
    calculator.register_observer(observer)
    calculator.register_observer(observer)
    calculator.execute_line("add 1 2")
    observer.update.assert_called_once()

    calculator.remove_observer(observer)
    calculator.remove_observer(observer)
    calculator.execute_line("add 3 4")
    observer.update.assert_called_once()


def test_observer_failure_is_logged_and_other_observers_continue(
    calculator, tmp_path, capsys
):
    failing = Mock(spec=CalculationObserver)
    failing.update.side_effect = RuntimeError("observer failed")
    remaining = Mock(spec=CalculationObserver)
    calculator.register_observer(failing)
    calculator.register_observer(remaining)

    assert calculator.execute_line("add 1 2") is True

    assert capsys.readouterr().out == "3\n"
    remaining.update.assert_called_once_with(
        CalculationEvent("add", Decimal(1), Decimal(2), Decimal(3))
    )
    content = (tmp_path / "test.log").read_text()
    assert "ERROR Observer" in content
    assert "RuntimeError: observer failed" in content


@pytest.mark.parametrize("command", ["", "help", "exit"])
def test_control_commands_do_not_notify_observers(command, calculator):
    observer = Mock(spec=CalculationObserver)
    calculator.register_observer(observer)
    calculator.execute_line(command)
    observer.update.assert_not_called()


def test_failed_calculation_does_not_notify_observers(calculator):
    observer = Mock(spec=CalculationObserver)
    calculator.register_observer(observer)
    with pytest.raises(CalculatorError, match="Cannot divide by zero"):
        calculator.execute_line("divide 1 0")
    observer.update.assert_not_called()
