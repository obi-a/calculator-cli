"""Reusable fixtures for interactive calculator sessions."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.logger import Logger


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Keep dotenv changes and all default log files inside this test's directory."""
    monkeypatch.setattr("app.calculator_config.PROJECT_ROOT", tmp_path)
    for name in (
        "CALCULATOR_LOG_DIR", "CALCULATOR_LOG_FILE", "PYTHON_DOTENV_DISABLED",
        "CALCULATOR_HISTORY_FILE", "CALCULATOR_MAX_HISTORY_SIZE", "CALCULATOR_AUTO_SAVE",
        "CALCULATOR_PRECISION", "CALCULATOR_MAX_INPUT_VALUE", "CALCULATOR_DEFAULT_ENCODING",
    ):
        # Record absent keys too, so values later added by dotenv are restored.
        monkeypatch.setenv(name, "")
        monkeypatch.delenv(name)
    return tmp_path


@pytest.fixture
def logger(tmp_path):
    """Provide a real file logger with explicit ownership for integration tests."""
    instance = Logger(tmp_path / "test.log")
    yield instance
    instance.close()


@pytest.fixture
def config():
    """Use normal defaults with auto-save disabled for unrelated unit tests."""
    return replace(CalculatorConfig.defaults(), auto_save=False)


@pytest.fixture
def calculator(logger, config):
    """Inject a logger so individual command tests need no startup configuration."""
    return Calculator(logger=logger, config=config)


@pytest.fixture
def run_session(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> Callable[..., tuple[int, str]]:
    """Run a session with supplied input lines or terminal exceptions."""

    def run(*entries: str | BaseException) -> tuple[int, str]:
        responses = iter(entries)

        def read_input(prompt: str) -> str:
            print(prompt, end="")
            response = next(responses, EOFError())
            if isinstance(response, BaseException):
                raise response
            return response

        monkeypatch.setattr("builtins.input", read_input)
        config = replace(CalculatorConfig.load(), auto_save=False)
        status = Calculator(config=config).run()
        return status, capsys.readouterr().out

    return run
