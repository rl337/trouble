# Inspiration Blog

A personal, Slashdot-style **inspiration blog** built from curated posts on X (Twitter). Each entry is a single JSON file on disk; a Sphinx-based builder turns those files into a static site published on GitHub Pages.

The previous **Trouble** etude site generator lived on the [`legacy`](https://github.com/rl337/trouble/tree/legacy) branch. `main` is this project.

## Data layout

Curated posts live under a **day-based path** (UTC date when the post was first archived):

```text
posts/YYYY/MM/DD/<post-id>.json
posts/YYYY/MM/DD/<post-id>/media/<n>.webp   # optional local thumbnails
```

- One JSON file per post; `<post-id>` must match the `"id"` field.
- Thread updates **edit the same file** (same path); bump `updated_at` and refresh `thread` / `summary_md`.
- The live site starts **empty** (`posts/` has no JSON until you add some).
- Incremental ingestion uses [`state/last_run.json`](state/last_run.json) (`last_run_at`, `ingested_post_ids`).

**Schema:** [`schema/post.schema.json`](schema/post.schema.json)

**Topics:** [`topics.yaml`](topics.yaml) defines the allowed `topics` slugs.

**Test fixtures:** [`sample/fixtures/`](sample/fixtures/) — not published.

## Adding a post

1. Create `posts/YYYY/MM/DD/<post-id>.json` following the schema (`updated_at` equals `collected_at` on first write).
2. Paraphrased, attributed Markdown in `summary_md`.
3. At least one fully expanded URL in `referenced_urls`.
4. Topic slugs from `topics.yaml`.
5. Optional `media` array; for images, add a WebP thumbnail under `posts/.../<id>/media/` (see `scripts/make_thumbnail.py`).
6. Validate and build:

   ```bash
   pip install -e ".[dev]"
   python -m inspiration validate
   python -m inspiration build
   ```

7. After an ingest run, update `state/last_run.json`.

See [`AGENTS.md`](AGENTS.md) for agent workflows.

## Thumbnails

```bash
python scripts/make_thumbnail.py https://example.com/image.png posts/2026/03/26/<post-id>/media/0.webp
```

Produces a WebP about 480px wide for inline display (original linked from the thumbnail).

## Build locally

```bash
pip install -e ".[dev]"
python -m inspiration validate
python -m inspiration build
python -m http.server --directory .build/html 8000
```

## Site structure

| Page | Content |
|------|---------|
| Front page | Posts sorted by `updated_at`, grouped by update day; *(updated)* when refreshed |
| `topics/<slug>` | Posts in that category |
| `archive/YYYY-MM-DD` | Posts by original archive day (path) |
| `posts/<id>` | Summary, thread, media (thumbnail + OCR blockquote), links |

Media: images use local thumbnails when present; video/gif link to the original. `ocr_text` renders as an indented blockquote directly under its thumbnail.

## License

[`LICENSE`](LICENSE) — CC0 1.0 Universal.
