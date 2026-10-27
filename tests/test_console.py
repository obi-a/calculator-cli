"""Console colors, plain-output conditions, and representative CLI messages."""

from dataclasses import replace
from io import StringIO
import sys

from colorama import Fore, Style
import pytest

from app.calculator import Calculator
from app.console import format_message, print_message
from main import main


@pytest.fixture(autouse=True)
def color_environment(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    # Keep simulated terminals independent of the host's Windows console API.
    monkeypatch.setattr("app.console.just_fix_windows_console", lambda: None)


@pytest.fixture
def terminal(monkeypatch):
    stream = StringIO()
    monkeypatch.setattr(stream, "isatty", lambda: True)
    return stream


@pytest.mark.parametrize(
    "category,color",
    [
        ("success", Fore.GREEN),
        ("error", Fore.RED),
        ("warning", Fore.YELLOW),
        ("info", Fore.CYAN),
    ],
)
def test_message_colors_reset_after_text(category, color, terminal):
    assert format_message("message", category, file=terminal) == (
        f"{color}message{Style.RESET_ALL}"
    )


@pytest.mark.parametrize(
    "is_terminal,no_color,colored",
    [(False, "", False), (True, "", True), (True, "0", False)],
)
def test_terminal_detection_and_opt_out(
    is_terminal, no_color, colored, terminal, monkeypatch
):
    monkeypatch.setattr(terminal, "isatty", lambda: is_terminal)
    monkeypatch.setenv("NO_COLOR", no_color)

    expected = f"{Fore.GREEN}message{Style.RESET_ALL}" if colored else "message"
    assert format_message("message", "success", file=terminal) == expected


def test_print_checks_stdout_and_stderr_independently(monkeypatch, capsys):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)

    print_message("result", "success")
    print_message("warning", "warning", file=sys.stderr)

    captured = capsys.readouterr()
    assert captured.out == "result\n"
    assert captured.err == f"{Fore.YELLOW}warning{Style.RESET_ALL}\n"


def test_terminal_session_keeps_persisted_data_plain(monkeypatch, run_session, tmp_path):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    status, output = run_session("add 1.20 2.30", "help", "history", "save", "exit")

    assert status == 0
    assert f"{Fore.CYAN}calc> {Style.RESET_ALL}" in output
    assert f"{Fore.GREEN}3.50{Style.RESET_ALL}\n" in output
    assert f"{Fore.CYAN}Commands (" in output
    assert "  add <number> <number>\n" in output
    assert "add 1.20 2.30 = 3.50\n" in output
    assert output.endswith("Goodbye!\n")
    for path in (tmp_path / "logs/calculator.log", tmp_path / "history.csv"):
        assert "\x1b[" not in path.read_text()


def test_startup_error_is_red_on_stderr(monkeypatch, capsys):
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    monkeypatch.setenv("CALCULATOR_LOG_FILE", "")

    assert main() == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        f"{Fore.RED}Error: CALCULATOR_LOG_FILE must not be blank.{Style.RESET_ALL}\n"
    )


def test_auto_save_warning_is_yellow_on_stderr(
    config, logger, tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    parent = tmp_path / "blocked"
    parent.write_text("not a directory")
    config = replace(config, auto_save=True, history_file=parent / "history.csv")
    calculator = Calculator(logger=logger, config=config)

    calculator.execute_line("add 1 2")

    captured = capsys.readouterr()
    assert captured.out == "3\n"
    assert captured.err.startswith(f"{Fore.YELLOW}Warning: Auto-save failed:")
    assert captured.err.endswith(f"{Style.RESET_ALL}\n")
