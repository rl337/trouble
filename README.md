# Trouble

A multi-purpose CLI tool.

## Overview

This project is designed to be executed by GitHub Actions, initially for generating static documentation files (Markdown or HTML) to be published via GitHub Pages.

## Commands

### `generate`

This command is used to generate documentation.

**Usage:**

```bash
python -m trouble generate
```

The `generate` command currently:
- Reads page data from `trouble/data.json`. Each key in this JSON file is treated as a page, and the associated object should contain `title`, `content`, and `filename` keys.
- Looks for templates in the `trouble/templates/` directory. It expects files ending with `.md.template` or `.html.template`.
- Uses Python's `string.Template` for templating (e.g., `${title}`, `${content}`).
- Outputs the generated files to the `docs/` directory by default.

(Further details on more advanced configuration and templating will be added here.)

## Development

(Instructions for setting up the development environment and running tests will be added here.)

## GitHub Actions

The `.github/workflows/publish.yml` file defines the GitHub Action that runs this tool on PR merges to publish generated content.
