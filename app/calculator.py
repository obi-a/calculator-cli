"""Read, evaluate, and print calculator commands until the user exits."""

from collections import deque
from collections.abc import Callable
from decimal import Decimal
from typing import cast

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorMemento
from app.console import format_message, initialize_console, print_message
from app.exceptions import CalculatorError, HistoryError
from app.factory import OperationFactory
from app.history import CalculationHistory
from app.input_validators import parse_number
from app.logger import Logger
from app.observers import (
    AutoSaveObserver,
    CalculationEvent,
    CalculationObserver,
    HistoryChangedEvent,
    HistoryObserver,
    LoggingObserver,
    ObserverRegistry,
)


class Calculator:
    """An interactive invoker for parameterized Calculation commands."""

    def __init__(
        self, logger: Logger | None = None, *, config: CalculatorConfig | None = None
    ) -> None:
        """Load configuration unless supplied, preserving logger-only injection.

        A logger supplied without config uses defaults without reading .env.
        Supplied loggers remain owned by their callers.
        """
        if config is None:
            config = (
                CalculatorConfig.defaults() if logger is not None else CalculatorConfig.load()
            )
        self._config = config
        self._owns_logger = logger is None
        self._logger = (
            Logger(config.log_file, encoding=config.default_encoding)
            if logger is None else logger
        )
        self._history = CalculationHistory(config)
        self._undo_stack: deque[CalculatorMemento] = deque(
            maxlen=config.max_history_size
        )
        self._redo_stack: deque[CalculatorMemento] = deque(
            maxlen=config.max_history_size
        )
        self._calculation_observers = ObserverRegistry[CalculationEvent](self._logger)
        self._history_observers = ObserverRegistry[HistoryChangedEvent](self._logger)
        self.register_observer(LoggingObserver(self._logger))
        if config.auto_save:
            self.register_history_observer(
                AutoSaveObserver(self._history, self._logger)
            )
        self._commands: dict[str, tuple[Callable[[], None], str]] = {
            "help": (self._print_help, "Show this help"),
            "history": (self.show_history, "Display calculation history"),
            "clear": (self.clear_history, "Clear calculation history"),
            "save": (self.save_history, "Save history to the configured CSV file"),
            "load": (self.load_history, "Replace history from the configured CSV file"),
            "undo": (self.undo, "Undo the last history change"),
            "redo": (self.redo, "Redo an undone history change"),
        }

    @property
    def history(self) -> tuple[Calculation, ...]:
        """Expose completed records without letting callers bypass undo tracking."""
        return self._history.entries

    def register_observer(self, observer: CalculationObserver) -> None:
        """Subscribe once by identity, preserving registration order."""
        self._calculation_observers.register(observer)

    def remove_observer(self, observer: CalculationObserver) -> None:
        """Unsubscribe by identity; an absent observer needs no action."""
        self._calculation_observers.remove(observer)

    def register_history_observer(self, observer: HistoryObserver) -> None:
        """Subscribe to all history mutations without receiving arithmetic events."""
        self._history_observers.register(observer)

    def remove_history_observer(self, observer: HistoryObserver) -> None:
        """Remove a history subscriber, if present."""
        self._history_observers.remove(observer)

    def _change_history(self, change: Callable[[], None]) -> None:
        """Record the prior state only after the requested change succeeds."""
        before = CalculatorMemento(self.history)
        change()
        self._undo_stack.append(before)
        self._redo_stack.clear()

    def _history_changed(self, action: str) -> None:
        self._logger.info("History %s (%s entries)", action, len(self.history))
        self._history_observers.notify(HistoryChangedEvent(action, self.history))

    def show_history(self) -> None:
        """Print history in insertion order without re-executing calculations."""
        self._logger.info("History displayed")
        if not self.history:
            print("No calculation history.")
            return
        for index, calculation in enumerate(self.history, start=1):
            record = calculation.to_record()
            print(
                f"{index}. [{record['timestamp']}] "
                f"{record['operation']} {record['left']} {record['right']} "
                f"= {record['result']}"
            )

    def clear_history(self) -> None:
        """Clear history as one undoable change."""
        if not self.history:
            self._logger.info("History already empty")
            print("No history to clear.")
            return
        self._change_history(self._history.clear)
        self._history_changed("clear")
        print_message("History cleared.", "success")

    def save_history(self) -> None:
        """Save current entries without creating an undo checkpoint."""
        self._history.save()
        self._logger.info("History saved to %s", self._config.history_file)
        print_message(f"History saved to {self._config.history_file}.", "success")

    def load_history(self) -> None:
        """Replace history only when the complete file has been validated."""
        self._change_history(self._history.load)
        self._history_changed("load")
        print_message(f"Loaded {len(self.history)} calculation(s).", "success")

    def _restore(
        self,
        source: deque[CalculatorMemento],
        target: deque[CalculatorMemento],
        action: str,
    ) -> None:
        """Move snapshots between stacks and restore records without recalculating."""
        if not source:
            raise CalculatorError(f"Nothing to {action}.")
        target.append(CalculatorMemento(self.history))
        self._history.replace(source.pop().calculations)
        self._history_changed(action)
        print_message(f"{action.capitalize()} complete.", "success")

    def undo(self) -> None:
        """Restore the history state before the last successful change."""
        self._restore(self._undo_stack, self._redo_stack, "undo")

    def redo(self) -> None:
        """Restore an undone state, preserving its original records."""
        self._restore(self._redo_stack, self._undo_stack, "redo")

    def close(self) -> None:
        """Close an internally created logger, leaving injected loggers to callers."""
        if self._owns_logger:
            self._logger.close()

    def run(self) -> int:
        """Run the REPL, recovering from expected errors between commands."""
        try:
            initialize_console()
            self._logger.info("Calculator session started")
            print_message("Enhanced Calculator. Type 'help' for commands.", "info")
            while True:
                try:
                    if not self.execute_line(input(format_message("calc> ", "info"))):
                        break
                except CalculatorError as error:
                    print_message(f"Error: {error}", "error")
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
            if name in self._commands or name in ("exit", "quit"):
                if len(tokens) != 1:
                    raise CalculatorError(f"Usage: {name}")
                if name in ("exit", "quit"):
                    return False
                self._commands[name][0]()
                return True

            operation = OperationFactory.create(name)
            if len(tokens) != 3:
                raise CalculatorError(f"Usage: {name} <number> <number>")

            left, right = (
                parse_number(token, self._config.max_input_value)
                for token in tokens[1:]
            )
            calculation = Calculation(operation, left, right).complete(
                self._config.precision
            )
            self._change_history(lambda: self._history.add(calculation))
        except HistoryError as error:
            self._logger.error("History command %r failed: %s", line, error)
            raise
        except CalculatorError as error:
            self._logger.warning("Rejected command %r: %s", line, error)
            raise

        result = cast(Decimal, calculation.result)
        print_message(result, "success")
        self._calculation_observers.notify(
            CalculationEvent(name, left, right, result)
        )
        self._history_changed("calculation")
        return True

    def _print_help(self) -> None:
        """Build arithmetic help from the same registry used for execution."""
        self._logger.info("Help requested")
        print_message("Commands (exactly two numbers per calculation):", "info")
        for name in OperationFactory.supported_operations():
            print(f"  {name} <number> <number>")
        for name, (_, description) in self._commands.items():
            print(f"  {name:<22}{description}")
        print("  exit / quit           Exit the calculator")
        print("Examples: add 0.1 0.2; divide 7 2; multiply -2 1e3")
        print("More examples: power 2 -3; root -8 3; percent 25 200")
        print("Root degree: a nonzero integer; negative numbers require odd degrees.")
        print("Precision: 28 significant digits, round-half-even.")
        print(f"Fractional digit limit: {self._config.precision}.")
        print(f"Maximum input magnitude: {self._config.max_input_value}.")
