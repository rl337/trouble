# AGENTS.md

## Cursor Cloud specific instructions

**Trouble** is a Python-based static site generator that produces a tabbed site from "Etudes" (modular sections). No databases, Docker, or Node.js required.

### Key Commands

All commands are documented in `README.md`. Quick reference:

| Task | Command |
|---|---|
| Generate site | `poetry run trouble generate` |
| Run unit tests | `poetry run python -m unittest discover -s tests -p "test_*.py"` |
| Run E2E tests | `poetry run pytest tests/e2e/` |
| Generate mock data | `poetry run trouble generate-mock-data --scenario success` |
| Run daily fetch | `poetry run trouble daily` |
| Serve locally | `python -m http.server 8008 --directory docs` |

### Non-obvious notes

- The virtualenv is configured in-project (`.venv/`). Poetry is installed via pipx; ensure `~/.local/bin` is on `PATH`.
- E2E tests auto-start their own HTTP server on port 8008. If that port is busy from a previous manual serve, the tests will fail with an "Address already in use" error. Kill any lingering server before running E2E tests.
- For local browser testing, you must generate mock data and write it to `docs/all_etudes_results.json` before serving. The client-side JS in the main `index.html` fetches `all_etudes_results.json` relative to the served directory for status indicators.
- The `generate` command fetches live data from external APIs (`dummyjson.com`, `jsonplaceholder.typicode.com`) during generation. This works in cloud VMs with network access.
- Playwright browsers must be installed once via `poetry run playwright install --with-deps`. This is handled by the update script.
- `python3.12-venv` apt package is required for Poetry/pipx to work in the Ubuntu environment.
