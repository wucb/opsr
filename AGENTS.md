# Repository Guidelines

## Project Structure & Module Organization
- `src/opsr/` holds the Python package. Core layers live in `agents/`, `models/`, `repositories/`, and `services/`.
- `tests/` contains unit tests (currently milestone-focused).
- `frontend/` is a static demo UI (`index.html`, `app.js`, `styles.css`).
- `README.md` documents product context and milestone 1 scope.

## Build, Test, and Development Commands
- `python -m unittest discover -s tests -p "test_*.py"` runs the current unit test suite.
- `python -m http.server 8080` serves the static frontend; open `http://localhost:8080/frontend/`.
- There is no build step or package manager defined yet; use standard Python tooling.

## Coding Style & Naming Conventions
- Python code uses 4-space indentation and type hints (`list[str]`, `dict[str, str]`).
- Names follow PEP 8: `snake_case` for functions/modules, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep modules small and layered (agents -> services -> repositories).
- No formatter or linter is configured; keep diffs tidy and consistent with existing files.

## Testing Guidelines
- Tests use the built-in `unittest` framework.
- Test files are named `test_*.py` and live under `tests/`.
- Aim to cover discovery, tagging, and topology behaviors when adding features.

## Commit & Pull Request Guidelines
- Commit history uses Conventional Commit prefixes (examples: `feat: ...`, `docs: ...`).
- Keep commits focused and scoped to a single change.
- PRs should include a short summary, test results (command + outcome), and UI screenshots when modifying `frontend/`.

## Security & Configuration Tips
- This milestone uses in-memory repositories only; avoid adding persistent credentials or secrets.
- If you introduce configuration, document defaults in `README.md` and provide safe local examples.