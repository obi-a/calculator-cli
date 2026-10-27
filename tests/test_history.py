"""History persistence and state changes through the public interfaces."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pandas as pd
import pytest

from app.calculation import Calculation
from app.calculator import Calculator
from app.exceptions import CalculatorError, HistoryError
from app.history import CalculationHistory
from app.operations import AddOperation


def completed(value):
    return Calculation(AddOperation(), Decimal(value), Decimal(0)).complete()


def results(calculator):
    return [str(entry.result) for entry in calculator.history]


@pytest.fixture
def entry():
    """A historical record beyond today's input and working-precision limits."""
    return Calculation(
        AddOperation(),
        Decimal("123456789012345678901234567890.1200"),
        Decimal("3.5000"),
        result=Decimal("123456789012345678901234567893.6200"),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@pytest.mark.parametrize("count,encoding", [(0, "utf-8"), (1, "utf-16")])
def test_csv_round_trip(count, encoding, entry, config):
    config = replace(config, default_encoding=encoding)
    history = CalculationHistory(config)
    if count:
        history.add(entry)
    history.save()

    assert config.history_file.read_text(encoding=encoding).splitlines()[0] == (
        "operation,operands,result,timestamp"
    )
    restored = CalculationHistory(
        replace(config, precision=0, max_input_value=Decimal(1))
    )
    restored.load()
    assert [item.to_record() for item in restored.entries] == (
        [item.to_record() for item in history.entries]
    )


@pytest.mark.parametrize(
    "contents",
    [
        None,
        "",
        "operation,left,right,result,timestamp\n",
        "operation,operands,result,timestamp\n"
        'add,"[""1"", ""2""]",3,2026-01-01T00:00:00+00:00,extra\n',
    ],
    ids=["missing", "empty-file", "wrong-columns", "extra-field"],
)
def test_invalid_csv_keeps_existing_history(contents, entry, config):
    history = CalculationHistory(config)
    history.add(entry)
    if contents is not None:
        config.history_file.write_text(contents)

    with pytest.raises(HistoryError):
        history.load()
    assert history.entries == (entry,)


@pytest.mark.parametrize(
    "field,value",
    [
        ("operation", "unknown"),
        ("operands", "not-json"),
        ("operands", '{"left": "1", "right": "2"}'),
        ("operands", '["1"]'),
        ("operands", '["1", 2]'),
        ("operands", '["not-a-number", "2"]'),
        ("result", "Infinity"),
        ("timestamp", "not-a-timestamp"),
        ("timestamp", "2026-01-01T00:00:00"),
    ],
)
def test_invalid_rows_are_rejected_together(field, value, entry, config):
    history = CalculationHistory(config)
    history.add(entry)
    valid = dict(entry.to_record(), operands='["1", "2"]', result="3")
    invalid = dict(entry.to_record(), **{field: value})
    pd.DataFrame([valid, invalid]).to_csv(config.history_file, index=False)

    with pytest.raises(HistoryError, match="Invalid history row 3"):
        history.load()
    assert history.entries == (entry,)


def test_failed_save_preserves_previous_file(entry, config, monkeypatch):
    history = CalculationHistory(config)
    history.add(entry)
    history.save()
    original = config.history_file.read_bytes()
    existing_files = set(config.history_file.parent.iterdir())
    monkeypatch.setattr(pd.DataFrame, "to_csv", Mock(side_effect=OSError("disk full")))

    with pytest.raises(HistoryError, match="disk full"):
        history.save()

    assert config.history_file.read_bytes() == original
    assert set(config.history_file.parent.iterdir()) == existing_files


@pytest.mark.parametrize(
    "commands,expected",
    [
        (["undo"], ["3"]),
        (["undo", "redo"], ["3", "7"]),
        (["clear", "undo"], ["3", "7"]),
        (["clear", "undo", "redo"], []),
    ],
)
def test_undo_redo(commands, expected, calculator):
    calculator.execute_line("add 1 2")
    calculator.execute_line("add 3 4")
    original = {str(item.result): item.to_record() for item in calculator.history}

    for command in commands:
        calculator.execute_line(command)

    assert results(calculator) == expected
    for item in calculator.history:
        assert item.to_record() == original[str(item.result)]


def test_new_calculation_discards_redo(calculator):
    calculator.execute_line("add 1 2")
    calculator.undo()
    calculator.execute_line("multiply 2 3")

    assert results(calculator) == ["6"]
    with pytest.raises(CalculatorError, match="Nothing to redo"):
        calculator.redo()


def test_undo_restores_evicted_entries(config, logger):
    calculator = Calculator(logger=logger, config=replace(config, max_history_size=2))
    calculator.execute_line("add 1 0")
    calculator.execute_line("add 2 0")
    before = calculator.history
    calculator.execute_line("add 3 0")

    assert results(calculator) == ["2", "3"]
    calculator.undo()
    assert calculator.history == before
    calculator.redo()
    assert results(calculator) == ["2", "3"]


def test_loading_replaces_and_limits_history(config, logger):
    source = CalculationHistory(config)
    for value in (1, 2, 3):
        source.add(completed(value))
    source.save()

    calculator = Calculator(logger=logger, config=replace(config, max_history_size=2))
    assert calculator.history == ()
    calculator.execute_line("add 9 0")
    before = calculator.history
    calculator.load_history()

    assert results(calculator) == ["2", "3"]
    assert [item.to_record() for item in calculator.history] == (
        [item.to_record() for item in source.entries[-2:]]
    )
    calculator.undo()
    assert calculator.history == before
    calculator.redo()
    assert results(calculator) == ["2", "3"]


def test_history_and_save_preserve_undo(calculator, config, capsys):
    calculator.execute_line("add 1.20 2.30")
    calculator.execute_line("history")
    assert not config.history_file.exists()
    calculator.execute_line("save")
    output = capsys.readouterr().out

    timestamp = calculator.history[0].timestamp.isoformat()
    assert f"1. [{timestamp}] add 1.20 2.30 = 3.50" in output
    assert "History saved to" in output
    assert config.history_file.exists()
    calculator.undo()
    assert calculator.history == ()


def test_empty_history_commands(calculator, capsys):
    calculator.execute_line("history")
    calculator.execute_line("clear")
    output = capsys.readouterr().out
    assert "No calculation history." in output
    assert "No history to clear." in output
    with pytest.raises(CalculatorError, match="Nothing to undo"):
        calculator.execute_line("undo")


def test_failed_load_preserves_redo(calculator, config, tmp_path):
    calculator.execute_line("add 1 2")
    calculator.execute_line("add 3 4")
    before = calculator.history
    calculator.undo()
    config.history_file.write_text("invalid,columns\n")

    with pytest.raises(HistoryError):
        calculator.execute_line("load")

    assert results(calculator) == ["3"]
    calculator.redo()
    assert calculator.history == before
    assert "ERROR History command" in (tmp_path / "test.log").read_text()


@pytest.mark.parametrize(
    "commands",
    [["add 4 5"], ["undo"], ["undo", "redo"], ["clear"], ["load"]],
    ids=["calculation", "undo", "redo", "clear", "load"],
)
def test_auto_save_follows_history(commands, config, logger):
    config = replace(config, auto_save=True, max_history_size=2)
    calculator = Calculator(logger=logger, config=config)
    calculator.execute_line("add 1 2")

    # A different on-disk state makes each action's save observable, including load.
    pd.DataFrame([completed(value).to_record() for value in (1, 2, 3)]).to_csv(
        config.history_file, index=False
    )
    for command in commands:
        calculator.execute_line(command)

    frame = pd.read_csv(config.history_file, dtype=str, keep_default_na=False)
    assert frame.to_dict("records") == [item.to_record() for item in calculator.history]


def test_auto_save_failure_keeps_calculation_and_undo(config, logger, tmp_path, capsys):
    parent = tmp_path / "blocked"
    parent.write_text("not a directory")
    config = replace(config, auto_save=True, history_file=parent / "history.csv")
    calculator = Calculator(logger=logger, config=config)

    assert calculator.execute_line("add 1 2") is True

    assert results(calculator) == ["3"]
    assert "Warning: Auto-save failed" in capsys.readouterr().err
    assert "ERROR Auto-save failed" in (tmp_path / "test.log").read_text()
    calculator.undo()
    assert calculator.history == ()


def test_configured_rounding_and_input_limit(config, logger):
    config = replace(config, precision=2, max_input_value=Decimal(10))
    calculator = Calculator(logger=logger, config=config)
    calculator.execute_line("divide 1 3")
    calculator.execute_line("multiply 10 10")
    before = calculator.history

    assert results(calculator) == ["0.33", "100"]
    with pytest.raises(CalculatorError, match="must not exceed"):
        calculator.execute_line("add -10.01 0")
    assert calculator.history == before
