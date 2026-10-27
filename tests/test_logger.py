"""File creation, logging levels, append behavior, and IO failures."""

import logging
from unittest.mock import Mock

import pytest

from app.exceptions import ConfigurationError
from app.logger import Logger


def test_creates_log_directory_and_file(tmp_path):
    destination = tmp_path / "nested/calculator.log"
    logger = Logger(destination)
    try:
        assert destination.is_file()
    finally:
        logger.close()


@pytest.mark.parametrize("level", ["info", "warning", "error"])
def test_log_levels_and_messages(level, logger, tmp_path):
    getattr(logger, level)("Event %s", "café")
    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert f"{level.upper()} Event café" in content


def test_loggers_append_without_duplicate_records(tmp_path):
    destination = tmp_path / "calculator.log"
    destination.write_text("existing record\n")
    first = Logger(destination)
    second = Logger(destination)
    try:
        first.info("first event")
        first.close()
        first.close()
        second.info("second event")
    finally:
        first.close()
        second.close()

    content = destination.read_text()
    assert content.startswith("existing record\n")
    assert content.count("first event") == 1
    assert content.count("second event") == 1


@pytest.mark.parametrize("destination_kind", ["directory", "parent_file"])
def test_invalid_log_destination(destination_kind, tmp_path):
    destination = tmp_path
    if destination_kind == "parent_file":
        parent = tmp_path / "occupied"
        parent.write_text("not a directory")
        destination = parent / "calculator.log"

    with pytest.raises(ConfigurationError, match="Cannot open log file"):
        Logger(destination)


@pytest.mark.parametrize("action", ["write", "close"])
def test_file_errors_are_reported_on_stderr(action, logger, monkeypatch, capsys):
    with monkeypatch.context() as patch:
        patch.setattr(
            logging.FileHandler, "flush", Mock(side_effect=OSError("disk full"))
        )
        if action == "write":
            logger.info("a calculation")
        else:
            logger.close()

    assert "ERROR: Could not write calculator log (disk full)" in capsys.readouterr().err
