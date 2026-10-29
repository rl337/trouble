# AGENTS.md

## Cursor Cloud specific instructions

This repository is an **inspiration blog** (Sphinx static site from curated X post JSON). It is **not** the legacy Trouble etude generator (see the `legacy` branch).

### Key commands

| Task | Command |
|------|---------|
| Validate fixtures + `posts/` | `python -m inspiration validate` |
| Build HTML site | `python -m inspiration build` |
| Run tests | `pytest tests/` |
| Serve built site locally | `python -m http.server --directory .build/html 8000` |

Install once: `pip install -e ".[dev]"` (Python 3.10+). A virtualenv under `.venv/` is fine.

### Adding a curated post (agents)

1. **One JSON file per post** at `posts/YYYY/MM/DD/<post-id>.json` (UTC date folders).
2. **Filename must match** `"id"` inside the file.
3. **Validate against** `schema/post.schema.json` before committing; CI runs `python -m inspiration validate`.
4. **`summary_md`:** paraphrased, deeply **attributed** summary of the thread—not verbatim X text. Use Markdown; the site renders it via MyST.
5. **`referenced_urls`:** at least one entry with a **fully expanded** URL (not only `t.co`). Include GitHub or other external links the reader should follow. Set `from_post` to the id of the post where the link appeared.
6. **`topics`:** only slugs listed in `topics.yaml` (currently `local-models`, `harness-dev`, `agentic-media`, `agentic-cognition`).
7. **Do not** put test/sample content under `posts/`—use `sample/fixtures/` for fake data.
8. An empty `posts/` tree is normal; the build must succeed with zero posts.

### Non-obvious notes

- The published site is built in GitHub Actions on push to `main` (`.github/workflows/pages.yml`); output is `.build/html`.
- Raw JSON under `posts/` is the source of truth for other agents—keep the directory layout stable and documented in `posts/README.md`.
- Local build artifacts live under `.build/` (gitignored).
