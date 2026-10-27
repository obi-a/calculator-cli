# The Enhanced calculator-cli

An interactive command-line calculator. Enter a command, get a
result, and keep working in the same session.

The calculator includes:

- Ten arithmetic operations using Decimal numbers.
- Calculation history with CSV saving, loading, and optional auto-save.
- Undo and redo for calculations and history changes.
- Configurable input limits, rounding, history size, and file encoding.
- File logging and color-coded terminal messages.
- Unit and integration tests, with coverage checks in GitHub Actions.

## Installation

Use Python (version 3.12 recommended).

Clone the project and change into its directory:

```bash
git clone https://github.com/obi-a/calculator-cli.git
cd calculator-cli
```

Create and activate a virtual environment.

```bash
python -m venv venv
source venv/bin/activate
```

With the virtual environment active, install the dependencies:

```bash
pip install -r requirements.txt
```

Continue with the configuration below. Run the remaining commands from the
project directory with the virtual environment active. Use `deactivate` when you want to leave the virtual environment.

## Configuration

Copy [.env.example](.env.example) to `.env` in the project root, beside `main.py`.
If you already have a `.env` file, keep it and add any settings you need from the
example file.

```bash
cp .env.example .env
```

Edit `.env` to change the settings:

| Variable                      | Default          | What it controls                                                                                            |
| ----------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------- |
| `CALCULATOR_LOG_DIR`          | `logs`           | Base directory for relative log file paths.                                                                 |
| `CALCULATOR_LOG_FILE`         | `calculator.log` | Log filename or path. Relative paths start inside the log directory; absolute paths are used directly.      |
| `CALCULATOR_HISTORY_FILE`     | `history.csv`    | CSV destination for saving and loading history. Relative paths start at the project root.                   |
| `CALCULATOR_MAX_HISTORY_SIZE` | `1000`           | Maximum retained history entries and the depth of each undo/redo stack. Must be an integer of at least `1`. |
| `CALCULATOR_AUTO_SAVE`        | `true`           | Save after each history change. Accepts `true` or `false`, case-insensitively.                              |
| `CALCULATOR_PRECISION`        | `28`             | Maximum fractional digits in new results. Must be a nonnegative integer; `0` rounds to a whole number.      |
| `CALCULATOR_MAX_INPUT_VALUE`  | `1e10`           | Inclusive maximum absolute value of each new operand. Must be a positive, finite Decimal value.             |
| `CALCULATOR_DEFAULT_ENCODING` | `utf-8`          | Text encoding used for log and CSV files. Must be a valid text encoding.                                    |

The application loads `.env` using python-dotenv. Existing environment variables
take precedence over values in the file. Missing variables use the defaults, so
the calculator can also run without a `.env` file. Blank or invalid settings
produce a startup error.

Relative log directories and history paths are resolved from the project root,
regardless of the working directory. Paths can also be absolute or start with
`~`. The history and log files must have different destinations. Parent
directories are created when the application needs to write to them.

The `.env` file itself is read as UTF-8. Keep it local: it is ignored by Git,
along with the default log directory and history file. If you choose a custom
history location inside the repository, add it to `.gitignore` as needed.

### Logging

The default log destination is `logs/calculator.log`. The application appends
records to the existing file, including the timestamp, level, and message.

| Level   | Events                                                                                     |
| ------- | ------------------------------------------------------------------------------------------ |
| INFO    | Session start and end, calculations, help requests, history changes, and successful saves. |
| WARNING | Invalid commands, invalid operands, and expected arithmetic errors.                        |
| ERROR   | Persistence failures, observer failures, and unexpected application errors.                |

A calculation record looks like this:

```text
2026-10-27 12:00:00,000 INFO Calculation operation=add left=1.20 right=2.30 result=3.50
```

Log timestamps use local time. New calculation timestamps stored in history use
UTC. Terminal colors are not written to either file.

The log file must be opened successfully before the calculator accepts commands.
If startup fails, check the path settings, encoding, and directory permissions.
The process reports the error and exits with status `1`. A log-write failure
during a session is reported on stderr while calculations continue.

## Usage

Start the calculator:

```bash
python main.py
```

Enter commands at the `calc>` prompt. Use `help` to see the available commands.
These examples use the default settings:

```text
calc> add 0.1 0.2
0.3
calc> divide 7 2
3.5
calc> power 2 -3
0.125
calc> divide 1 0
Error: Cannot divide by zero.
calc> exit
Goodbye!
```

Expected command errors leave the session running so you can correct the input
and continue. Command names are case-insensitive, and extra whitespace is allowed.

### Arithmetic commands

Each arithmetic command takes exactly two finite numbers. Negative numbers,
decimal fractions, and scientific notation such as `1e3` are supported.

| Command          | What it does                                        | Example           |
| ---------------- | --------------------------------------------------- | ----------------- |
| `add a b`        | Add the two numbers.                                | `add 0.1 0.2`     |
| `subtract a b`   | Subtract `b` from `a`.                              | `subtract 3 8`    |
| `multiply a b`   | Multiply the two numbers.                           | `multiply -2 1e3` |
| `divide a b`     | Divide `a` by `b`.                                  | `divide 7 2`      |
| `power a b`      | Raise `a` to the power `b`.                         | `power 2 -3`      |
| `root a b`       | Find the `b`th root of `a`.                         | `root -8 3`       |
| `modulus a b`    | Return a remainder whose nonzero sign follows `b`.  | `modulus -7 3`    |
| `int_divide a b` | Divide and discard the fractional part toward zero. | `int_divide -7 3` |
| `percent a b`    | Calculate `(a / b) * 100`.                          | `percent 25 200`  |
| `abs_diff a b`   | Return the absolute difference between the numbers. | `abs_diff -3 8`   |

For example, `int_divide -7 3` returns `-2`, `modulus -7 3` returns `2`, and
`percent 25 200` returns `12.500`.

### Number and rounding rules

The Calculator uses a Decimal working context with 28 significant digits and
round-half-even. `CALCULATOR_PRECISION` then limits fractional digits in the final
result. Increasing that setting does not increase the working precision.

Results are rounded only when they exceed the fractional-digit limit. Existing
significance is preserved: `add 1.20 2.30` produces `3.50`, with no extra padding.
If `CALCULATOR_PRECISION=2`, `power 2 -3` produces `0.12` because round-half-even
rounds the exact halfway value `0.125` to `0.12`.

The input limit applies to both operands, including negative values. With the
default `1e10` limit, inputs from `-10000000000` through `10000000000` are allowed.
Results can exceed that limit, but must stay within the supported Decimal range.
`NaN` and infinity are rejected.

Some operations have additional rules:

- `divide`, `modulus`, `int_divide`, and `percent` require a nonzero second operand.
- A negative base in `power` requires an integer exponent. Zero to the power of
  zero, or zero to a negative power, is rejected.
- `root` requires a nonzero integer degree. A negative number requires an odd
  degree, and zero cannot have a negative degree. Negative degrees give reciprocal
  roots: `root 16 -2` has the numeric value `0.25`, displayed with the retained
  trailing zeros.

### Session and history commands

These commands take no arguments. `save` and `load` use
`CALCULATOR_HISTORY_FILE`; a filename is not supplied at the prompt.

| Command         | What it does                                                                    |
| --------------- | ------------------------------------------------------------------------------- |
| `help`          | Display supported commands and input rules.                                     |
| `history`       | Display retained calculations, oldest first, with their timestamps and results. |
| `clear`         | Clear current history as one undoable change.                                   |
| `save`          | Save current history to the configured CSV file.                                |
| `load`          | Replace current history with the validated CSV contents as one undoable change. |
| `undo`          | Restore the history state before the last successful change.                    |
| `redo`          | Restore a change that was undone.                                               |
| `exit` / `quit` | End the session. EOF and Ctrl+C also exit cleanly.                              |

### Saving and restoring history

Each session starts with empty in-memory history. To resume an existing saved
history, run `load` before entering new calculations. With auto-save enabled,
new work replaces the CSV with the current in-memory history.

For an existing history file, you can enter these commands at the prompt:

```text
calc> load
calc> add 2 3
calc> history
calc> undo
calc> redo
calc> save
```

Auto-save is enabled by default. It runs after a calculation, a clear that removes
entries, a successful load, an undo, or a redo. Clearing nonempty history therefore
also saves an empty CSV when auto-save is enabled. Use `undo` in the current
session to restore that change. Setting `CALCULATOR_AUTO_SAVE=false` lets you
control writes with `save`.

History is stored using pandas with these CSV columns:

```csv
operation,operands,result,timestamp
add,"[""1.20"", ""2.30""]",3.50,2026-10-27T12:00:00+00:00
```

The `operands` column contains a JSON array of two numeric strings.
Numeric representations and timestamps are preserved when records are loaded.
Current precision and input limits apply to new calculations; loaded records are
not recalculated or rounded again. Saving empty history writes the header only.

When history exceeds `CALCULATOR_MAX_HISTORY_SIZE`, the oldest entries are
discarded. The same limit applies when loading a file, keeping its newest rows.
Undo can restore entries evicted by the last calculation.

Undo and redo work within the current session. Their stacks are not saved to CSV.
They restore complete history states, including the original results and
timestamps. A new calculation, a clear that removes entries, or a successful load
discards redo states. Displaying history and saving it leave the stacks unchanged.
Empty stacks produce `Nothing to undo.` or `Nothing to redo.` errors.

A missing, malformed, or unreadable CSV produces an error and leaves current
history unchanged. A failed save preserves the previous CSV. Auto-save failures
produce a warning while retaining the calculation in memory; fix the destination
or permissions, then use `save` to retry.

### Color Coding

| Color  | Output                                                  |
| ------ | ------------------------------------------------------- |
| Green  | Results and successful history actions.                 |
| Red    | Command errors, startup errors, and log-write failures. |
| Yellow | Auto-save warnings.                                     |
| Cyan   | Welcome message, prompt, and help heading.              |

Help details, history rows, and the goodbye message stay neutral.

Colors are enabled only when the destination is a terminal. Redirected output
stays plain. stdout and stderr are checked independently.

Set `NO_COLOR` to any nonempty value to disable colors in an interactive terminal. Apply it to one run:

```bash
NO_COLOR=1 python main.py
```

## Testing

Run the full suite from the project root with the virtual environment active:

```bash
pytest
```

[pytest.ini](pytest.ini) enables coverage automatically for `app` and `main`,
including statements and branches. The run fails if combined coverage is below
90%. Reports are written to:

- The terminal, including any missing lines.
- `htmlcov/index.html`, which you can open in a browser.
- `coverage.xml`, for tools and CI reporting.

To run just the history tests without the whole-project coverage requirement:

```bash
pytest tests/test_history.py --no-cov
```

Tests use temporary paths and isolated configuration so they do not use your local
`.env`, log file, or saved history. Coverage exclusions are reserved for documented,
intentionally unreachable code.

## GitHub Actions

The [Python application workflow](.github/workflows/python-app.yml) runs on pushes
to `main` and pull requests targeting `main`.

It uses Ubuntu and Python 3.12 to:

1. Check out the repository.
2. Install the dependencies from `requirements.txt`.
3. Run `python -m pytest`, enforcing the same 90% coverage minimum used locally.
4. Upload available HTML and XML reports as the `coverage-reports` artifact, even
   when tests fail.

Open the workflow run in the repository's Actions tab to inspect failures and
download coverage reports. This workflow provides continuous integration; it
does not publish releases or deploy the application.
