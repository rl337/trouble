"""Sphinx configuration for the inspiration static site."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

project = "Inspiration"
author = "rl337"
copyright = "2026, rl337"
release = "0.1.0"

extensions = [
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

myst_enable_extensions = ["colon_fence", "deflist", "replacements"]

html_theme = "basic"
html_static_path = ["_static"]
html_css_files = ["inspiration.css"]
html_title = "Inspiration"
html_short_title = "Inspiration"

html_theme_options = {
    "sidebarwidth": "220px",
}

html_sidebars = {
    "**": ["localtoc.html", "relations.html", "searchbox.html"],
}

html_use_modindex = False
html_domain_indices = False

# Slashdot-ish nav header via layout template
html_context = {
    "topics_yaml": str(REPO_ROOT / "topics.yaml"),
}
