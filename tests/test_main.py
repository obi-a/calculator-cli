"""Executable startup, exit status, and safe imports."""

from pathlib import Path
import runpy

import pytest

from app.calculator import Calculator
from main import main

ENTRY_POINT = Path(__file__).resolve().parents[1] / "main.py"


def test_main_returns_repl_exit_status(monkeypatch):
    monkeypatch.setattr(Calculator, "run", lambda self: 7)
    assert main() == 7


@pytest.mark.parametrize("log_file,expected_status", [("calculator.log", 0), ("", 1)])
def test_executable_startup(log_file, expected_status, monkeypatch, capsys):
    monkeypatch.setenv("CALCULATOR_LOG_FILE", log_file)
    monkeypatch.setattr("builtins.input", lambda prompt: "exit")

    with pytest.raises(SystemExit) as exit_status:
        runpy.run_path(str(ENTRY_POINT), run_name="__main__")

    assert exit_status.value.code == expected_status
    captured = capsys.readouterr()
    if expected_status == 0:
        assert "Goodbye!" in captured.out
    else:
        assert "CALCULATOR_LOG_FILE must not be blank" in captured.err
        assert captured.out == ""


def test_import_does_not_start_calculator_or_create_logs(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("CALCULATOR_LOG_FILE", "")
    runpy.run_path(str(ENTRY_POINT), run_name="calculator_import_check")
    assert capsys.readouterr().out == ""
    assert list(tmp_path.iterdir()) == []
