# Trouble: Etude-Based Static Site Generator

## Overview

Trouble is a Python-based command-line tool for generating static websites, with a particular focus on organizing content into "Etudes." An Etude represents a distinct sub-project or section of the website. The tool is designed to be executed by GitHub Actions for publishing to GitHub Pages.

The generated site features a main `index.html` with a tabbed navigation, where each tab corresponds to an Etude and displays its content.

## Core Concepts

*   **Etude (`trouble.etude_core.Etude`)**: An abstract base class representing a section of the site. Each Etude is responsible for generating its own `index.html` within its dedicated subdirectory in the output (e.g., `docs/etude_name/index.html`) and providing metrics about itself.
*   **EtudeRegistry (`trouble.etude_core.EtudeRegistry`)**: Discovers, registers, and provides access to all available Etude instances. Etudes are typically discovered from the `trouble.etudes` package.
*   **Generator (`trouble.generator.run_generation`)**: Orchestrates the site generation process:
    1.  Initializes the `EtudeRegistry`.
    2.  Triggers etude discovery.
    3.  Instructs each registered Etude to generate its content.
    4.  Generates the main `docs/index.html` which includes navigation tabs for all etudes.
*   **Templates**: HTML templates (using Python's `string.Template` syntax) are located in `trouble/templates/`. Key templates include:
    *   `main_index.html.template`: For the overall site structure with tabs.
    *   `etude_zero_index.html.template`: Specific template for Etude Zero.
    *   `etude_generic_index.html.template`: A general-purpose template for other etudes.

## Commands

### `generate`

This command runs the static site generation process.

**Usage:**

```bash
python -m trouble generate
```

This will:
1.  Discover all Etudes within the `trouble.etudes` package.
2.  Generate content for each Etude into a corresponding subdirectory within `docs/` (e.g., `docs/zero/index.html`, `docs/one/index.html`).
3.  Generate a main `docs/index.html` file with tabs that load the content from each Etude's subdirectory (typically via iframes).

The output is placed in the `docs/` directory by default.

## Creating a New Etude

To add a new Etude to the project:

1.  **Create a Sub-Package**:
    *   Inside the `trouble/etudes/` directory, create a new directory for your etude (e.g., `trouble/etudes/my_new_etude/`). This directory name will typically be used as the `name` of your etude.
2.  **Add `__init__.py`**:
    *   Create an `__init__.py` file inside your new etude's directory (`trouble/etudes/my_new_etude/__init__.py`).
    *   In this `__init__.py`, import your main Etude class (see next step) to make it easily discoverable. Example:
        ```python
        # trouble/etudes/my_new_etude/__init__.py
        from .etude_impl import MyNewEtude
        print(f"trouble.etudes.my_new_etude package loaded, {MyNewEtude.NAME} available.")
        ```
3.  **Implement the Etude Class (`etude_impl.py`)**:
    *   Create a Python file in your etude's directory, conventionally named `etude_impl.py` (e.g., `trouble/etudes/my_new_etude/etude_impl.py`).
    *   Define a class that inherits from `trouble.etude_core.Etude`.
    *   Set `NAME` and `DESCRIPTION` as class attributes. The `NAME` should match your subdirectory name for consistency.
    *   Implement the `__init__` method, calling `super().__init__(name=self.NAME, description=self.DESCRIPTION)`.
    *   Implement the abstract methods:
        *   `get_metrics(self, registry: EtudeRegistry) -> dict[str, any]`: Return a dictionary of metrics for this etude.
        *   `generate_content(self, output_dir: str, registry: EtudeRegistry) -> None`: Generate the `index.html` for this etude in the `output_dir`. Use a template from `trouble/templates/` (e.g., `etude_generic_index.html.template` or a custom one).
    *   Example structure:
        ```python
        # trouble/etudes/my_new_etude/etude_impl.py
        import os
        from string import Template
        from trouble.etude_core import Etude, EtudeRegistry

        class MyNewEtude(Etude):
            NAME = "my_new_etude" # Should match directory name
            DESCRIPTION = "A brief description of what this new etude does."

            def __init__(self):
                super().__init__(name=MyNewEtude.NAME, description=MyNewEtude.DESCRIPTION)

            def get_metrics(self, registry: EtudeRegistry) -> dict[str, any]:
                return {"ExampleMetric": 123, "Status": "Under Development"}

            def generate_content(self, output_dir: str, registry: EtudeRegistry) -> None:
                os.makedirs(output_dir, exist_ok=True)
                # ... (load template, prepare data, write output_dir/index.html) ...
                # Example using a generic template:
                template_data = {
                    "etude_name": self.name,
                    "etude_description": self.description,
                    # Add any other fields your generic template expects
                    "metrics_status": self.get_metrics(registry).get("Status", "N/A"),
                    "metrics_items": "N/A", # Placeholder
                    "metrics_version": "N/A" # Placeholder
                }
                # Simplified template loading and rendering logic:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                template_path = os.path.join(base_dir, "templates", "etude_generic_index.html.template")
                try:
                    with open(template_path, "r") as f_template:
                        template_str = f_template.read()
                    tmpl = Template(template_str)
                    output_content = tmpl.substitute(template_data)
                    with open(os.path.join(output_dir, "index.html"), "w") as f_out:
                        f_out.write(output_content)
                    print(f"Generated content for {self.name}")
                except Exception as e:
                    print(f"Error generating content for {self.name}: {e}")
        ```
4.  **Create Templates (Optional but Recommended)**:
    *   If your etude needs a unique layout, create a new HTML template in `trouble/templates/`.
    *   Otherwise, you can reuse `etude_generic_index.html.template` or `etude_zero_index.html.template` as a base.
5.  **Run the Generator**:
    *   Execute `python -m trouble generate`. Your new etude should be automatically discovered and included in the site.

## Development

### Setting up Environment (Recommended)

It's recommended to use a virtual environment for development:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt # If you add any dependencies
```

### Running Tests Locally

The project uses Python's built-in `unittest` framework. Tests are located in the `tests/` directory.

To run all tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

You can also run a specific test file:

```bash
python -m unittest tests.test_etude_core
```

Or a specific test class or method:

```bash
python -m unittest tests.test_etude_core.TestEtudeCore
python -m unittest tests.test_etude_core.TestEtudeCore.test_etude_creation
```

## GitHub Actions

*   **`publish.yml`**: This workflow runs `python -m trouble generate` on pushes to the `main` branch to build the site and deploy the `docs/` directory to GitHub Pages.
*   **`run-tests.yml`**: This workflow runs all unit tests (using `python -m unittest discover`) on every push to any branch and on pull requests targeting `main`. It tests against multiple Python versions (3.9, 3.10, 3.11). Branch protection rules can be set on the `main` branch to require these tests to pass before merging.
