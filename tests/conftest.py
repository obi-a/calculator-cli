"""Reusable fixtures for interactive calculator sessions."""

from collections.abc import Callable

import pytest

from app.calculator import Calculator


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
        status = Calculator().run()
        return status, capsys.readouterr().out

    return run
