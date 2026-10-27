"""Consistent console colors with terminal detection and a NO_COLOR opt-out."""

import os
import sys
from typing import Literal, TextIO

from colorama import Fore, Style, just_fix_windows_console

Category = Literal["success", "error", "warning", "info"]
_COLORS = {
    "success": Fore.GREEN,
    "error": Fore.RED,
    "warning": Fore.YELLOW,
    "info": Fore.CYAN,
}


def initialize_console() -> None:
    """Enable Windows console support; repeated calls are safe."""
    just_fix_windows_console()


def format_message(
    text: object, category: Category, *, file: TextIO | None = None
) -> str:
    """Style terminal text, resetting before subsequent output or typed input."""
    stream = sys.stdout if file is None else file
    message = str(text)
    if stream.isatty() and not os.getenv("NO_COLOR"):
        return f"{_COLORS[category]}{message}{Style.RESET_ALL}"
    return message


def print_message(
    text: object, category: Category, *, file: TextIO | None = None
) -> None:
    """Resolve the destination at call time and print one formatted message."""
    stream = sys.stdout if file is None else file
    print(format_message(text, category, file=stream), file=stream)
