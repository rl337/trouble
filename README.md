# Trouble: Etude-Based Static Site Generator

## Overview & Data Flow

Trouble is a Python tool for generating static websites organized into "Etudes." A key feature is its ability to perform daily data fetching tasks and make this data available to the live site without requiring a new site deployment.

The architecture follows this data flow:
1.  **Daily Data Fetch (`daily` command):** A scheduled GitHub Action (`daily-data-release.yml`) runs `python -m trouble daily`.
2.  **Resource Definition:** Each Etude can define data sources to be fetched daily via its `get_daily_resources()` method, using `Fetcher` classes (`URLFetcher`, `StaticFetcher`).
3.  **Data Aggregation:** The `daily` command orchestrates the fetching for all etudes, aggregates the results (including status, data, and action logs) into a single JSON object.
4.  **Publishing to Release:** The daily workflow creates a new GitHub Release tagged with the current date (e.g., `data-YYYY-MM-DD`) and uploads the aggregated JSON as a release asset (`daily_etude_data.json`).
5.  **Static Site Generation (`generate` command):** A separate workflow (`publish.yml`) runs `python -m trouble generate` on pushes to `main`. This generates the HTML "app shell" for the site, including all necessary JavaScript assets.
6.  **Client-Side Rendering:** When a user visits the live GitHub Pages site, client-side JavaScript (`data_fetcher.js`) fetches the latest `daily_etude_data.json` from the GitHub Releases. It has fallback logic to try previous days if today's release is missing.
7.  **UI Updates:** Etude-specific JavaScript (`ui.js`) fetches a client-side template (`.mustache`), fetches the daily data, and then uses Mustache.js to render the final HTML into the app shell.

## Core Concepts

*   **Etude (`trouble.etude_core.Etude`)**: Abstract base class for a site section. Implements `get_metrics()` for build-time data and `get_daily_resources()` for defining daily data fetches.
*   **Fetcher (`trouble.fetchers.Fetcher`)**: Abstract base class for data fetchers. `URLFetcher` and `StaticFetcher` are provided.
*   **EtudeRegistry (`trouble.etude_core.EtudeRegistry`)**: Discovers and registers all Etude instances from the `trouble.etudes` package.
*   **DailyEtudeResult (`trouble.fetchers.DailyEtudeResult`)**: A structured `NamedTuple` (`status`, `data`, `actions_log`) that holds the result of an etude's daily tasks.

## Commands

### `generate`
Generates the static HTML and JavaScript "app shell" for the site.
**Usage:** `poetry run trouble generate`

### `daily`
Runs the daily data fetching tasks for all etudes and prints the aggregated results as a JSON string to standard output.
**Usage:** `poetry run trouble daily`

### `generate-mock-data`
Generates a mock `daily_etude_data.json` structure for a given test scenario. The output is printed as a JSON string to standard output.
**Usage:** `poetry run trouble generate-mock-data --scenario <success|partial_failure|no_data>`

## Creating a New Etude

To add a new Etude to the project:

1.  **Create Etude Sub-Package**: Create a directory `trouble/etudes/my_new_etude/`.
2.  **Add `__init__.py`**: Create `trouble/etudes/my_new_etude/__init__.py` and import your Etude class into it to ensure discovery.
3.  **Implement `etude_impl.py`**:
    *   Define a class inheriting from `trouble.etude_core.Etude`.
    *   Set `NAME` and `DESCRIPTION` class attributes.
    *   Implement `get_metrics()`.
    *   To fetch daily data, override `get_daily_resources()` and return a list of `(name, Fetcher)` tuples.
    *   `generate_content()` should create the HTML app shell. Use a template from `trouble/templates/`.
4.  **Implement Client-Side UI (`js_src/ui.js`)**:
    *   Create `trouble/etudes/my_new_etude/js_src/ui.js`.
    *   This script is responsible for fetching the client-side template and the daily data, then using Mustache.js to render the final HTML.
5.  **Create Client-Side Template (`js_src/templates/`)**:
    *   Create `trouble/etudes/my_new_etude/js_src/templates/my_template.mustache`.
    *   Define the HTML structure for your dynamic content here using Mustache syntax.
6.  **Create/Update HTML App Shell Template**:
    *   Ensure your main HTML template in `trouble/templates/` has elements with `id`s for your JavaScript to target, and includes the necessary `<script>` tags to load `mustache.min.js` and your `ui.js`.

## Development & Testing

### Python with Poetry

1.  **Install Poetry**: Follow the [official installation instructions](https://python-poetry.org/docs/#installation).
2.  **Install Dependencies**: From the project root, run:
    ```bash
    poetry install
    ```
    This will create a virtual environment inside the project directory (`.venv`) and install all dependencies listed in `pyproject.toml`.

### Running Tests Locally

#### Unit Tests
To run all Python unit tests:
```bash
poetry run python -m unittest discover -s tests -p "test_*.py"
```

#### End-to-End (E2E) Tests
The E2E tests use Playwright to run tests in a headless browser, verifying client-side JavaScript rendering.

1.  **Install Playwright Browsers** (one-time setup):
    ```bash
    poetry run playwright install --with-deps
    ```
2.  **Run the E2E Tests**:
    ```bash
    poetry run pytest tests/e2e/
    ```
    The tests will automatically:
    *   Generate the static site.
    *   Generate the necessary mock data files.
    *   Start a local web server.
    *   Run Playwright to open a browser, intercept network calls to the GitHub API, and assert that the UI renders the mock data correctly.

### Manual Browser Testing
For manual debugging or development of the client-side UI:

1.  **Generate Mock Data**:
    ```bash
    poetry run trouble generate-mock-data --scenario success > mock_data.json
    ```
2.  **Generate the Site**:
    ```bash
    poetry run trouble generate
    ```
3.  **Serve Locally**:
    ```bash
    python -m http.server 8000 --directory docs
    ```
4.  **Intercept and Verify**:
    *   Use browser developer tools (e.g., Chrome's Sources > Overrides) or an extension (e.g., Requestly) to intercept the call to `https://api.github.com/repos/...` and respond with the content of your `mock_data.json` file.
    *   Open `http://localhost:8000` and check that the site renders the mock data as expected.

## GitHub Actions

*   **`daily-data-release.yml`**: Runs daily on a schedule. Executes `python -m trouble daily`, captures the output JSON, and creates a new GitHub Release tagged with the date, attaching the JSON as a release asset.
*   **`publish.yml`**: Runs on pushes to `main`. Executes `python -m trouble generate` to build the static site and deploys the `docs/` directory to GitHub Pages.
*   **`run-tests.yml`**: Runs tests on every push and pull request to `main`. It contains two jobs:
    *   `unit-tests`: Runs fast Python unit tests across multiple Python versions.
    *   `e2e-tests`: Runs slower Playwright end-to-end browser tests to verify client-side rendering. This job runs only after `unit-tests` succeed.
