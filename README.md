# Inspiration Blog

A personal, Slashdot-style **inspiration blog** built from curated posts on X (Twitter). Each entry is a single JSON file on disk; a Sphinx-based builder turns those files into a static site published on GitHub Pages.

The previous **Trouble** etude site generator lived on the [`legacy`](https://github.com/rl337/trouble/tree/legacy) branch. `main` is this project.

## Data layout

Curated posts live under a **day-based path** (UTC curation date):

```text
posts/YYYY/MM/DD/<post-id>.json
```

- One file per post; `<post-id>` must match the `"id"` field in the JSON.
- The live site starts **empty** (`posts/` has no JSON until you add some).
- Other agents may read these JSON files directly—keep paths stable and documented.

**Schema:** [`schema/post.schema.json`](schema/post.schema.json)

**Topics:** [`topics.yaml`](topics.yaml) defines the allowed `topics` slugs (title + description for each category).

**Test fixtures:** [`sample/fixtures/`](sample/fixtures/) holds fake posts used by CI/tests—not published.

## Adding a post

1. Create `posts/YYYY/MM/DD/<post-id>.json` following the schema.
2. Use paraphrased, attributed Markdown in `summary_md` (not verbatim post text).
3. Include at least one fully expanded URL in `referenced_urls` (GitHub links are common).
4. Pick one or more topic slugs from `topics.yaml`.
5. Validate:

   ```bash
   pip install -e .
   python -m inspiration validate
   ```

6. Build locally (see below) and open `.build/html/index.html`.

See [`AGENTS.md`](AGENTS.md) for agent-specific rules.

## Build locally

Requirements: Python 3.10+

```bash
pip install -e ".[dev]"
python -m inspiration validate   # fixtures + posts/
python -m inspiration build      # writes .build/html/
python -m http.server --directory .build/html 8000
```

Then visit http://localhost:8000/

## Site structure

The builder generates:

| Page | Content |
|------|---------|
| Front page | Recent posts, newest first, grouped by archive day |
| `topics/<slug>` | Posts for each topic category |
| `archive/YYYY-MM-DD` | All posts archived on that day |
| `posts/<id>` | Full entry with summary, thread, links, hashtags |

## License

[`LICENSE`](LICENSE) — CC0 1.0 Universal.
