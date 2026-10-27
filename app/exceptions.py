"""Exceptions that can be explained to calculator users without a traceback."""


class CalculatorError(ValueError):
    """An invalid calculator request or an unsupported arithmetic result."""


class ConfigurationError(CalculatorError):
    """Invalid startup settings prevent the application from running."""


class HistoryError(CalculatorError):
    """Calculation history could not be saved or loaded."""
