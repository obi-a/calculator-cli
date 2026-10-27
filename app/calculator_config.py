"""Load calculator settings without depending on the working directory."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

from app.exceptions import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class CalculatorConfig:
    """Resolved logging paths, loaded explicitly when a calculator starts."""

    log_dir: Path
    log_file: Path

    @classmethod
    def load(cls) -> "CalculatorConfig":
        """Load the project's .env without overriding existing environment values."""
        try:
            load_dotenv(PROJECT_ROOT / ".env", override=False)
        except (OSError, UnicodeError, ValueError) as error:
            raise ConfigurationError(f"Cannot load .env: {error}") from error

        log_dir_value = os.getenv("CALCULATOR_LOG_DIR", "logs")
        log_file_value = os.getenv("CALCULATOR_LOG_FILE", "calculator.log")
        for name, value in (
            ("CALCULATOR_LOG_DIR", log_dir_value),
            ("CALCULATOR_LOG_FILE", log_file_value),
        ):
            if not value.strip():
                raise ConfigurationError(f"{name} must not be blank.")

        try:
            log_dir = Path(log_dir_value).expanduser()
            if not log_dir.is_absolute():
                log_dir = PROJECT_ROOT / log_dir
            log_dir = log_dir.resolve()

            log_file = Path(log_file_value).expanduser()
            if not log_file.is_absolute():
                log_file = log_dir / log_file
            return cls(log_dir=log_dir, log_file=log_file.resolve())
        except (OSError, RuntimeError, ValueError) as error:
            raise ConfigurationError(f"Invalid logging path: {error}") from error
