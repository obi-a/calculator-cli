"""Start the calculator with ``python main.py``."""

from app.calculator import Calculator


def main() -> int:
    """Run the interactive calculator and return its process exit status."""
    return Calculator().run()


if __name__ == "__main__":
    raise SystemExit(main())
