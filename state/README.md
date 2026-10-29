# Ingestion run state

`last_run.json` tracks incremental curation runs:

| Field | Meaning |
|-------|---------|
| `last_run_at` | ISO 8601 UTC. The ingesting agent only processes X posts **created after** this timestamp. |
| `ingested_post_ids` | Post ids already stored under `posts/` (optional cache; can be rebuilt by scanning `posts/**/*.json`). |

After each successful ingest run, bump `last_run_at` to the run completion time (UTC) and refresh `ingested_post_ids` from the repo.

Thread follow-ups on an **existing** post update the **same** JSON file (same path under the original archive day). Set `updated_at` when refreshing `thread` and `summary_md`.
