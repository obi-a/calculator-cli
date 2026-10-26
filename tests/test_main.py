"""The executable wrapper starts the REPL and preserves its exit status."""

from pathlib import Path
import runpy

import pytest

from app.calculator import Calculator
from main import main

ENTRY_POINT = Path(__file__).resolve().parents[1] / "main.py"


def test_main_returns_repl_exit_status(monkeypatch):
    monkeypatch.setattr(Calculator, "run", lambda self: 7)
    assert main() == 7


def test_executable_entry_point(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "exit")
    with pytest.raises(SystemExit) as exit_status:
        runpy.run_path(str(ENTRY_POINT), run_name="__main__")
    assert exit_status.value.code == 0
    assert "Goodbye!" in capsys.readouterr().out


def test_importing_entry_point_does_not_start_a_session(capsys):
    runpy.run_path(str(ENTRY_POINT), run_name="calculator_import_check")
    assert capsys.readouterr().out == ""
