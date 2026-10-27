"""Load calculator settings without depending on the working directory."""

from dataclasses import dataclass, field
from decimal import Context, Decimal, InvalidOperation
import os
from pathlib import Path

from dotenv import load_dotenv

from app.exceptions import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _setting(name: str, default: str) -> str:
    value = os.getenv(name, default)
    if not value.strip():
        raise ConfigurationError(f"{name} must not be blank.")
    return value


def _integer_setting(name: str, default: str) -> int:
    value = _setting(name, default)
    try:
        return int(value)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be an integer: {error}") from error


def _resolve_path(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


@dataclass(frozen=True, slots=True)
class CalculatorConfig:
    """Validated calculator settings with project-relative default paths."""

    log_dir: Path
    log_file: Path
    history_file: Path = field(default_factory=lambda: PROJECT_ROOT / "history.csv")
    max_history_size: int = 1000
    auto_save: bool = True
    precision: int = 28
    max_input_value: Decimal = Decimal("1e10")
    default_encoding: str = "utf-8"

    def __post_init__(self) -> None:
        for name, value, minimum in (
            ("CALCULATOR_MAX_HISTORY_SIZE", self.max_history_size, 1),
            ("CALCULATOR_PRECISION", self.precision, 0),
        ):
            if value < minimum:
                raise ConfigurationError(f"{name} must be at least {minimum}.")
        if not self.max_input_value.is_finite() or self.max_input_value <= 0:
            raise ConfigurationError(
                "CALCULATOR_MAX_INPUT_VALUE must be positive and finite."
            )
        if self.history_file == self.log_file:
            raise ConfigurationError(
                "CALCULATOR_HISTORY_FILE must differ from CALCULATOR_LOG_FILE."
            )
        try:
            "".encode(self.default_encoding)
        except (LookupError, ValueError) as error:
            raise ConfigurationError(
                f"CALCULATOR_DEFAULT_ENCODING must be a text encoding: {error}"
            ) from error

    @classmethod
    def defaults(cls) -> "CalculatorConfig":
        """Build defaults without reading or modifying the environment."""
        return cls(
            log_dir=PROJECT_ROOT / "logs",
            log_file=PROJECT_ROOT / "logs/calculator.log",
        )

    @classmethod
    def load(cls) -> "CalculatorConfig":
        """Load the project's .env without overriding existing environment values."""
        try:
            load_dotenv(PROJECT_ROOT / ".env", override=False)
        except (OSError, ValueError) as error:
            raise ConfigurationError(f"Cannot load .env: {error}") from error

        log_dir_value = _setting("CALCULATOR_LOG_DIR", "logs")
        log_file_value = _setting("CALCULATOR_LOG_FILE", "calculator.log")
        history_file_value = _setting("CALCULATOR_HISTORY_FILE", "history.csv")

        try:
            log_dir = _resolve_path(log_dir_value, PROJECT_ROOT)
            log_file = _resolve_path(log_file_value, log_dir)
            history_file = _resolve_path(history_file_value, PROJECT_ROOT)
        except (OSError, RuntimeError, ValueError) as error:
            raise ConfigurationError(f"Invalid configuration path: {error}") from error

        auto_save_value = _setting("CALCULATOR_AUTO_SAVE", "true").strip().lower()
        if auto_save_value not in ("true", "false"):
            raise ConfigurationError("CALCULATOR_AUTO_SAVE must be true or false.")
        try:
            max_input_value = Decimal(
                _setting("CALCULATOR_MAX_INPUT_VALUE", "1e10"),
                context=Context(traps=[InvalidOperation]),
            )
        except InvalidOperation as error:
            raise ConfigurationError(
                "CALCULATOR_MAX_INPUT_VALUE must be a decimal number."
            ) from error

        return cls(
            log_dir=log_dir,
            log_file=log_file,
            history_file=history_file,
            max_history_size=_integer_setting("CALCULATOR_MAX_HISTORY_SIZE", "1000"),
            auto_save=auto_save_value == "true",
            precision=_integer_setting("CALCULATOR_PRECISION", "28"),
            max_input_value=max_input_value,
            default_encoding=_setting("CALCULATOR_DEFAULT_ENCODING", "utf-8"),
        )
