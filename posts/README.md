# Curated posts (live data)

External agents drop **one JSON file per curated post** here. The path encodes the curation date (UTC):

```
posts/YYYY/MM/DD/<post-id>.json
```

Example:

```
posts/2026/03/26/1847291059283747291.json
```

- `<post-id>` must match the `id` field inside the JSON file.
- Files must validate against [`schema/post.schema.json`](../schema/post.schema.json).
- Topic slugs must come from [`topics.yaml`](../topics.yaml).
- The published site starts with an **empty** tree; only validated files under this directory are built.

Sample posts for tests live under `sample/fixtures/` (not here).
