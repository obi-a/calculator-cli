"""Configuration defaults, environment precedence, and path validation."""

from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.calculator_config import CalculatorConfig
from app.exceptions import ConfigurationError


def test_default_configuration(tmp_path):
    config = CalculatorConfig.load()
    assert config.log_dir == tmp_path / "logs"
    assert config.log_file == tmp_path / "logs/calculator.log"
    assert config.history_file == tmp_path / "history.csv"
    assert config.max_history_size == 1000
    assert config.auto_save is True
    assert config.precision == 28
    assert config.max_input_value == Decimal("1e10")
    assert config.default_encoding == "utf-8"
    assert list(tmp_path.iterdir()) == []


def test_project_dotenv_is_loaded_from_any_working_directory(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        'CALCULATOR_LOG_DIR="custom logs"\n'
        'CALCULATOR_LOG_FILE="sessions/calculations.txt"\n',
        encoding="utf-8",
    )
    working_dir = tmp_path / "elsewhere"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)

    config = CalculatorConfig.load()
    assert config.log_dir == tmp_path / "custom logs"
    assert config.log_file == tmp_path / "custom logs/sessions/calculations.txt"


@pytest.mark.parametrize(
    "setting,value,expected_dir,expected_file",
    [
        ("CALCULATOR_LOG_DIR", "env_logs", "env_logs", "dotenv.log"),
        ("CALCULATOR_LOG_FILE", "env.log", "dotenv_logs", "env.log"),
    ],
)
def test_environment_overrides_dotenv(
    setting, value, expected_dir, expected_file, tmp_path, monkeypatch
):
    (tmp_path / ".env").write_text(
        "CALCULATOR_LOG_DIR=dotenv_logs\nCALCULATOR_LOG_FILE=dotenv.log\n"
    )
    monkeypatch.setenv(setting, value)

    config = CalculatorConfig.load()
    assert config.log_dir == tmp_path / expected_dir
    assert config.log_file == tmp_path / expected_dir / expected_file


@pytest.mark.parametrize(
    "setting,destination,expected_file",
    [
        ("CALCULATOR_LOG_DIR", "absolute", "absolute/calculator.log"),
        ("CALCULATOR_LOG_FILE", "absolute/custom.log", "absolute/custom.log"),
    ],
)
def test_absolute_paths(setting, destination, expected_file, tmp_path, monkeypatch):
    monkeypatch.setenv(setting, str(tmp_path / destination))
    assert CalculatorConfig.load().log_file == tmp_path / expected_file


@pytest.mark.parametrize(
    "setting,value",
    [
        ("CALCULATOR_LOG_DIR", ""),
        ("CALCULATOR_LOG_DIR", " "),
        ("CALCULATOR_LOG_FILE", ""),
        ("CALCULATOR_LOG_FILE", "\t"),
        ("CALCULATOR_HISTORY_FILE", " "),
    ],
)
def test_blank_settings_are_rejected(setting, value, monkeypatch):
    monkeypatch.setenv(setting, value)
    with pytest.raises(ConfigurationError, match=f"{setting} must not be blank"):
        CalculatorConfig.load()


def test_unreadable_dotenv_reports_configuration_error(monkeypatch):
    monkeypatch.setattr(
        "app.calculator_config.load_dotenv", Mock(side_effect=PermissionError("denied"))
    )
    with pytest.raises(ConfigurationError, match="Cannot load .env"):
        CalculatorConfig.load()


def test_invalid_path_reports_configuration_error(monkeypatch):
    monkeypatch.setattr(Path, "resolve", Mock(side_effect=OSError("invalid path")))
    with pytest.raises(ConfigurationError, match="Invalid configuration path"):
        CalculatorConfig.load()


def test_history_and_calculation_settings_from_dotenv(tmp_path):
    destination = tmp_path / "saved/history.csv"
    (tmp_path / ".env").write_text(
        f"CALCULATOR_HISTORY_FILE={destination}\n"
        "CALCULATOR_MAX_HISTORY_SIZE=2\nCALCULATOR_AUTO_SAVE=FaLsE\n"
        "CALCULATOR_PRECISION=2\nCALCULATOR_MAX_INPUT_VALUE=99.5\n"
        "CALCULATOR_DEFAULT_ENCODING=utf-16\n"
    )
    config = CalculatorConfig.load()
    assert config.history_file == destination
    assert config.max_history_size == 2
    assert config.auto_save is False
    assert config.precision == 2
    assert config.max_input_value == Decimal("99.5")
    assert config.default_encoding == "utf-16"


@pytest.mark.parametrize(
    "setting,value",
    [
        ("CALCULATOR_MAX_HISTORY_SIZE", "0"),
        ("CALCULATOR_PRECISION", "-1"),
        ("CALCULATOR_PRECISION", "two"),
        ("CALCULATOR_MAX_INPUT_VALUE", "invalid"),
        ("CALCULATOR_MAX_INPUT_VALUE", "NaN"),
        ("CALCULATOR_MAX_INPUT_VALUE", "0"),
        ("CALCULATOR_AUTO_SAVE", "yes"),
        ("CALCULATOR_DEFAULT_ENCODING", "not-an-encoding"),
        ("CALCULATOR_HISTORY_FILE", "logs/calculator.log"),
    ],
)
def test_invalid_history_and_calculation_settings(setting, value, monkeypatch):
    monkeypatch.setenv(setting, value)
    with pytest.raises(ConfigurationError, match=setting):
        CalculatorConfig.load()
