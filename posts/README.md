# Curated posts (live data)

External agents drop **one JSON file per curated post** here. The path encodes the **first archive date** (UTC):

```text
posts/YYYY/MM/DD/<post-id>.json
posts/YYYY/MM/DD/<post-id>/media/<n>.webp
```

- `<post-id>` must match the `id` field inside the JSON file.
- **Thread updates** modify the **same file** (same path); set `updated_at` when refreshing `thread` / `summary_md`.
- Validate against [`schema/post.schema.json`](../schema/post.schema.json).
- Incremental runs use [`state/last_run.json`](../state/last_run.json).

Sample posts for tests live under `sample/fixtures/` (not here).
