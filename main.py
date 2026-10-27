"""Start the calculator with ``python main.py``."""

import sys

from app.calculator import Calculator
from app.exceptions import ConfigurationError


def main() -> int:
    """Run the interactive calculator and return its process exit status."""
    try:
        calculator = Calculator()
    except ConfigurationError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    try:
        return calculator.run()
    finally:
        calculator.close()


if __name__ == "__main__":
    raise SystemExit(main())
