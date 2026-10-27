"""Read, evaluate, and print calculator commands until the user exits."""

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.exceptions import CalculatorError
from app.factory import OperationFactory
from app.input_validators import parse_number
from app.logger import Logger
from app.observers import CalculationEvent, CalculationObserver, LoggingObserver


class Calculator:
    """An interactive invoker for parameterized Calculation commands."""

    def __init__(self, logger: Logger | None = None) -> None:
        self._owns_logger = logger is None
        self._logger = (
            Logger(CalculatorConfig.load().log_file) if logger is None else logger
        )
        self._observers: list[CalculationObserver] = []
        self.register_observer(LoggingObserver(self._logger))

    def register_observer(self, observer: CalculationObserver) -> None:
        """Subscribe once by identity, preserving registration order."""
        if not any(existing is observer for existing in self._observers):
            self._observers.append(observer)

    def remove_observer(self, observer: CalculationObserver) -> None:
        """Unsubscribe by identity; an absent observer needs no action."""
        for index, existing in enumerate(self._observers):
            if existing is observer:
                del self._observers[index]
                return

    def _notify_observers(self, event: CalculationEvent) -> None:
        for observer in tuple(self._observers):
            try:
                observer.update(event)
            except Exception:
                self._logger.exception(
                    "Observer %s failed for %s", type(observer).__name__, event.operation
                )

    def close(self) -> None:
        """Close an internally created logger, leaving injected loggers to callers."""
        if self._owns_logger:
            self._logger.close()

    def run(self) -> int:
        """Run the REPL, recovering from expected errors between commands."""
        try:
            self._logger.info("Calculator session started")
            print("Enhanced Calculator. Type 'help' for commands.")
            while True:
                try:
                    if not self.execute_line(input("calc> ")):
                        break
                except CalculatorError as error:
                    print(f"Error: {error}")
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
            print("Goodbye!")
            return 0
        except Exception:
            self._logger.exception("Unexpected calculator error")
            raise
        finally:
            self._logger.info("Calculator session ended")
            self.close()

    def execute_line(self, line: str) -> bool:
        """Process one line and return whether the session should continue."""
        tokens = line.split()
        if not tokens:
            return True

        try:
            name = tokens[0].lower()
            if name in ("help", "exit", "quit"):
                if len(tokens) != 1:
                    raise CalculatorError(f"Usage: {name}")
                if name == "help":
                    self._logger.info("Help requested")
                    self._print_help()
                    return True
                return False

            operation = OperationFactory.create(name)
            if len(tokens) != 3:
                raise CalculatorError(f"Usage: {name} <number> <number>")

            left, right = (parse_number(token) for token in tokens[1:])
            result = Calculation(operation, left, right).execute()
        except CalculatorError as error:
            self._logger.warning("Rejected command %r: %s", line, error)
            raise

        print(result)
        self._notify_observers(CalculationEvent(name, left, right, result))
        return True

    @staticmethod
    def _print_help() -> None:
        """Build arithmetic help from the same registry used for execution."""
        print("Commands (exactly two numbers per calculation):")
        for name in OperationFactory.supported_operations():
            print(f"  {name} <number> <number>")
        print("  help                  Show this help")
        print("  exit / quit           Exit the calculator")
        print("Examples: add 0.1 0.2; divide 7 2; multiply -2 1e3")
        print("More examples: power 2 -3; root -8 3; percent 25 200")
        print("Root degree: a nonzero integer; negative numbers require odd degrees.")
        print("Precision: 28 significant digits, round-half-even.")
