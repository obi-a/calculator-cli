"""Executable startup, exit status, and safe imports."""

import csv
import json
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


def test_entry_point_applies_encoding_to_logs_and_auto_save(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text(
        "CALCULATOR_DEFAULT_ENCODING=utf-16\n"
        "CALCULATOR_HISTORY_FILE=archive/history.csv\n"
    )
    commands = iter(["add 1.20 2.30", "undo", "redo", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(commands))

    assert main() == 0

    log = (tmp_path / "logs/calculator.log").read_text(encoding="utf-16")
    assert "INFO Calculation operation=add left=1.20 right=2.30 result=3.50" in log
    contents = (tmp_path / "archive/history.csv").read_text(encoding="utf-16")
    record = next(csv.DictReader(contents.splitlines()))
    assert list(record) == ["operation", "operands", "result", "timestamp"]
    assert json.loads(record["operands"]) == ["1.20", "2.30"]
    assert record["result"] == "3.50"
