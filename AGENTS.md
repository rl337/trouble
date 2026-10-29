# AGENTS.md

## Cursor Cloud specific instructions

This repository is an **inspiration blog** (Sphinx static site from curated X post JSON). Legacy Trouble code is on the `legacy` branch.

### Key commands

| Task | Command |
|------|---------|
| Validate fixtures, `posts/`, state | `python -m inspiration validate` |
| Build HTML site | `python -m inspiration build` |
| Image thumbnail | `python scripts/make_thumbnail.py <url-or-path> posts/YYYY/MM/DD/<id>/media/0.webp` |
| Tests | `pytest tests/` |
| Serve built site | `python -m http.server --directory .build/html 8000` |

Install: `pip install -e ".[dev]"` (Python 3.10+).

### Incremental ingestion

1. Read `state/last_run.json` — only process X posts **created after** `last_run_at`.
2. New post: write `posts/YYYY/MM/DD/<post-id>.json` with `updated_at` = `collected_at`.
3. Existing thread with new author follow-ups: **update the same JSON file** (original archive path). Append to `thread`, refresh `summary_md`, set `updated_at` to now (UTC). Never duplicate files for the same `id`.
4. After the run: set `last_run_at` to run completion time and sync `ingested_post_ids` from all `posts/*/*/*/*.json` basenames.

### Post JSON rules

- Validate against `schema/post.schema.json` before commit.
- `summary_md`: paraphrased, attributed — not verbatim X text.
- `referenced_urls`: at least one fully expanded URL (GitHub or other external).
- `topics`: slugs from `topics.yaml` only.
- Optional `keywords`: **pre-normalized** before write — lowercase, no leading `#`, singular form (e.g. `aiagent` not `aiagents`), no `@handles` or author names. The builder merges hashtags, topics, keywords, and extracted nouns into one normalized genindex term set per post.
- Sample data only under `sample/fixtures/`, not `posts/`.

### Media

- `media[]`: `type` (`image`|`video`|`gif`), `url`, `from_post`, `description`; optional `kind`, `thumbnail` (images only), `ocr_text`.
- Thumbnail path pattern: `posts/YYYY/MM/DD/<post-id>/media/<n>.webp` (~480px wide WebP). Generate with `scripts/make_thumbnail.py`.
- Site renders thumbnails inline (linking to `url`); `ocr_text` appears as a **blockquote under the thumbnail** (not collapsed).

### Non-obvious notes

- Pages deploy from `.github/workflows/pages.yml` on push to `main`.
- Build output: `.build/html/` (gitignored). Fixture thumbnails live under `sample/fixtures/media-assets/posts/...` for CI.
