"""Read, evaluate, and print calculator commands until the user exits."""

from app.calculation import Calculation
from app.exceptions import CalculatorError
from app.factory import OperationFactory
from app.input_validators import parse_number


class Calculator:
    """An interactive invoker for parameterized Calculation commands."""

    def run(self) -> int:
        """Run the REPL, recovering from expected errors between commands."""
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

    def execute_line(self, line: str) -> bool:
        """Process one line and return whether the session should continue."""
        tokens = line.split()
        if not tokens:
            return True

        name = tokens[0].lower()
        if name in ("help", "exit", "quit"):
            if len(tokens) != 1:
                raise CalculatorError(f"Usage: {name}")
            if name == "help":
                self._print_help()
                return True
            return False

        operation = OperationFactory.create(name)
        if len(tokens) != 3:
            raise CalculatorError(f"Usage: {name} <number> <number>")

        left, right = (parse_number(token) for token in tokens[1:])
        command = Calculation(operation, left, right)
        print(command.execute())
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
        print("Precision: 28 significant digits, round-half-even.")
