"""CLI results, recoverable errors, and logging through public behavior."""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.calculator import Calculator
from app.factory import OperationFactory
from app.logger import Logger


@pytest.mark.parametrize(
    "name,left,right,result",
    [
        ("add", "1.20", "2.30", "3.50"),
        ("subtract", "3", "8", "-5"),
        ("multiply", "-2", "1e3", "-2E+3"),
        ("divide", "7", "2", "3.5"),
        ("power", "2", "-3", "0.125"),
        ("root", "-8", "3", "-2.000000000000000000000000000"),
        ("modulus", "-7", "3", "2"),
        ("int_divide", "-7", "3", "-2"),
        ("percent", "25", "200", "12.500"),
        ("abs_diff", "3", "8", "5"),
    ],
)
def test_calculations_print_and_log_results(name, left, right, result, run_session, tmp_path):
    status, output = run_session(f"  {name.upper()}\t{left}  {right} ", "exit")

    assert status == 0
    assert f"calc> {result}\n" in output
    content = (tmp_path / "logs/calculator.log").read_text()
    assert content.count("INFO Calculation") == 1
    assert (
        f"operation={name} left={Decimal(left)} right={Decimal(right)} result={result}"
    ) in content


def test_help_lists_commands(run_session, tmp_path):
    _, output = run_session("help", "exit")
    for name in OperationFactory.supported_operations():
        assert f"{name} <number> <number>" in output
    assert "exit / quit" in output
    assert "INFO Help requested" in (tmp_path / "logs/calculator.log").read_text()


@pytest.mark.parametrize(
    "command,message",
    [
        ("unknown 1 2", "Unknown operation"),
        ("add", "Usage: add"),
        ("divide 1", "Usage: divide"),
        ("power 1 2 3", "Usage: power"),
        ("exit 1", "Usage: exit"),
        ("load unexpected.csv", "Usage: load"),
        ("add nope 2", "Invalid number"),
        ("divide 1 -0", "Cannot divide by zero"),
    ],
)
def test_invalid_commands_log_warning_and_allow_recovery(
    command, message, run_session, tmp_path
):
    status, output = run_session(command, "add 2 3", "exit")

    assert status == 0
    assert f"Error: {message}" in output
    assert "calc> 5\n" in output
    content = (tmp_path / "logs/calculator.log").read_text()
    assert content.count("WARNING Rejected command") == 1
    assert content.count("INFO Calculation") == 1


@pytest.mark.parametrize("end", ["exit", "quit", EOFError(), KeyboardInterrupt()])
def test_clean_shutdown(end, run_session, tmp_path):
    status, output = run_session("divide 1 3", end)

    assert status == 0
    assert "0.3333333333333333333333333333" in output
    assert output.endswith("Goodbye!\n")
    content = (tmp_path / "logs/calculator.log").read_text()
    assert "INFO Calculator session started" in content
    assert "INFO Calculator session ended" in content


def test_unexpected_errors_are_logged_and_raised(monkeypatch, run_session, tmp_path):
    monkeypatch.setattr(
        OperationFactory, "create", Mock(side_effect=RuntimeError("unexpected failure"))
    )
    with pytest.raises(RuntimeError, match="unexpected failure"):
        run_session("add 1 2")

    content = (tmp_path / "logs/calculator.log").read_text()
    assert "ERROR Unexpected calculator error" in content
    assert "RuntimeError: unexpected failure" in content


@pytest.mark.parametrize("injected", [False, True])
def test_calculator_only_closes_its_own_logger(injected, monkeypatch):
    logger = Mock(spec=Logger)
    monkeypatch.setattr("app.calculator.Logger", lambda path, **kwargs: logger)
    monkeypatch.setattr("builtins.input", lambda prompt: "exit")
    calculator = Calculator(logger=logger) if injected else Calculator()

    assert calculator.run() == 0
    assert logger.close.call_count == (0 if injected else 1)


def test_injected_logger_bypasses_configuration(logger, monkeypatch):
    monkeypatch.setenv("CALCULATOR_LOG_FILE", "")
    calculator = Calculator(logger=logger)
    assert calculator.execute_line("add 1 2") is True
