"""Configuration defaults, environment precedence, and path validation."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from app.calculator_config import CalculatorConfig
from app.exceptions import ConfigurationError


def test_default_configuration(tmp_path):
    config = CalculatorConfig.load()
    assert config.log_dir == tmp_path / "logs"
    assert config.log_file == tmp_path / "logs/calculator.log"
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
    with pytest.raises(ConfigurationError, match="Invalid logging path"):
        CalculatorConfig.load()
