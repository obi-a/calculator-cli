"""Full interactive sessions, including recovery and terminal shutdown."""

import pytest

from app.calculator import Calculator
from app.factory import OperationFactory


def test_session_runs_all_four_operations(run_session):
    status, output = run_session(
        "add 0.1 0.2", "subtract 3 8", "multiply -2 4", "divide 7 2", "exit"
    )
    assert status == 0
    for result in ("0.3", "-5", "-8", "3.5"):
        assert f"calc> {result}\n" in output
    assert "Goodbye!" in output


def test_session_runs_all_six_new_operations(run_session):
    status, output = run_session(
        "power 2 -3", "root -8 3", "modulus -7 3", "int_divide -7 3",
        "percent 25 200", "abs_diff 3 8", "exit"
    )
    assert status == 0
    for result in ("0.125", "-2.000000000000000000000000000", "2", "-2", "12.500", "5"):
        assert f"calc> {result}\n" in output
    assert "Error:" not in output
    assert output.endswith("Goodbye!\n")


def test_new_operations_accept_normalized_names_and_decimal_operands(run_session):
    _, output = run_session("  RoOt\t1e6  3 ", "MoDuLuS -5.5 2", "quit")
    assert "0.5\n" in output
    assert "100.0000000000000000000000000\n" in output
    assert "Error:" not in output


def test_session_accepts_case_whitespace_and_scientific_notation(run_session):
    status, output = run_session("", " \t ", "  MuLtIpLy\t-2  1e3  ", " QuIt ")
    assert status == 0
    assert "-2E+3\n" in output
    assert "Error:" not in output


def test_help_lists_registered_operations_and_usage(run_session):
    _, output = run_session("HELP", "exit")
    for name in OperationFactory.supported_operations():
        assert f"{name} <number> <number>" in output
    assert "exit / quit" in output
    assert "28 significant digits" in output


@pytest.mark.parametrize("name", OperationFactory.supported_operations())
@pytest.mark.parametrize("operands", ["", " 1", " 1 2 3"])
def test_wrong_arithmetic_arity_recovers(run_session, name, operands):
    status, output = run_session(name + operands, "add 2 3", "exit")
    assert status == 0
    assert f"Error: Usage: {name} <number> <number>" in output
    assert "calc> 5\n" in output


@pytest.mark.parametrize("name", ["help", "exit", "quit"])
def test_control_commands_reject_operands_and_keep_running(run_session, name):
    _, output = run_session(f"{name} 1", "add 2 3", "exit")
    assert f"Error: Usage: {name}\n" in output
    assert "calc> 5\n" in output


@pytest.mark.parametrize(
    "line,message",
    [
        ("unknown 1 2", "Unknown operation"),
        ("power -2 0.5", "integer exponent"),
        ("power 0 -1", "negative power"),
        ("root -16 2", "odd root degree"),
        ("root 16 0", "degree cannot be zero"),
        ("root 16 0.5", "degree must be an integer"),
        ("modulus 5 0", "Cannot divide by zero"),
        ("int_divide 5 -0", "Cannot divide by zero"),
        ("percent 25 0", "Cannot divide by zero"),
        ("power NaN 2", "finite decimal numbers"),
        ("root 16 Infinity", "finite decimal numbers"),
        ("add nope 2", "Invalid number"),
        ("subtract 2 nope", "Invalid number"),
        ("add NaN 1", "finite decimal numbers"),
        ("multiply 1 Infinity", "finite decimal numbers"),
        ("divide 1 -0", "Cannot divide by zero"),
        ("multiply 1e999999 10", "supported decimal range"),
        ("divide 1e-999999 1e100", "supported decimal range"),
    ],
)
def test_expected_errors_do_not_end_session(run_session, line, message):
    status, output = run_session(line, "add 2 3", "exit")
    assert status == 0
    assert "Error:" in output
    assert message in output
    assert "calc> 5\n" in output
    assert "Traceback" not in output


@pytest.mark.parametrize("end", [EOFError(), KeyboardInterrupt(), "exit", "quit"])
def test_clean_shutdown_after_a_calculation(run_session, end):
    status, output = run_session("divide 1 3", end)
    assert status == 0
    assert "0.3333333333333333333333333333" in output
    assert output.endswith("Goodbye!\n")
    assert "Error:" not in output


def test_unexpected_programming_errors_are_not_swallowed(monkeypatch):
    def broken_factory(name):
        raise RuntimeError("Unexpected implementation failure")

    monkeypatch.setattr(OperationFactory, "create", broken_factory)
    monkeypatch.setattr("builtins.input", lambda prompt: "add 1 2")
    with pytest.raises(RuntimeError, match="Unexpected implementation failure"):
        Calculator().run()
