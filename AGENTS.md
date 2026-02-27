# AGENTS.md

## Cursor Cloud specific instructions

**Trouble** is a Python-based static site generator that creates websites organized into "Etudes." See `README.md` for full documentation.

### Quick reference

| Task | Command |
|---|---|
| Install deps | `poetry install` |
| Unit tests | `poetry run python -m unittest discover -s tests -p "test_*.py"` |
| E2E tests | `poetry run pytest tests/e2e/` |
| Generate site | `poetry run trouble generate` |
| Daily data fetch | `poetry run trouble daily` |
| Generate mock data | `poetry run trouble generate-mock-data --scenario success` |
| Serve locally | `python -m http.server 8000 --directory docs` |

### Non-obvious notes

- Poetry must be on `PATH`. It installs to `~/.local/bin` — ensure `export PATH="$HOME/.local/bin:$PATH"` is in your shell profile.
- The virtualenv is created in-project (`.venv/`) via `poetry config virtualenvs.in-project true`.
- Playwright browsers must be installed once after `poetry install`: `poetry run playwright install --with-deps`. This is **not** in the update script because it is slow and rarely changes.
- E2E tests automatically start a local HTTP server on port 8008, generate the site, and mock GitHub API calls — no manual setup needed.
- There is no linter configured in the project (no flake8, ruff, pylint, or mypy config). The project has no lint step.
- The `docs/` directory is the generated output and is gitignored. It is rebuilt by `poetry run trouble generate`.
