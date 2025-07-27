import pytest
from playwright.sync_api import Page, expect, Route, Request
from pathlib import Path
import re

# Define the direct download URL pattern to intercept.
# This should match the URL constructed in data_fetcher.js
REPO_OWNER = 'greple-test'
REPO_NAME = 'test-1'
API_URL_PATTERN = re.compile(
    f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/data-\\d{{4}}-\\d{{2}}-\\d{{2}}/daily_etude_data.json"
)

@pytest.mark.parametrize("mock_data_path", ["success"], indirect=True)
def test_etude_one_renders_success_scenario(page: Page, live_server: str, mock_data_path: Path):
    """
    Test that Etude One correctly renders content when the data fetch is successful.
    """
    # Read the mock data that the server will respond with
    mock_data_content = mock_data_path.read_text()

    def handle_route(route: Route, request: Request):
        """Intercept the GitHub API call and respond with our mock data."""
        print(f"Intercepted request to: {request.url}")
        route.fulfill(
            status=200,
            content_type="application/json",
            body=mock_data_content
        )

    # Navigate to the Etude One page on the live server
    etude_one_url = f"{live_server}/one/index.html"
    print(f"Navigating to {etude_one_url}")
    page.goto(etude_one_url, wait_until="domcontentloaded")

    # Inject the mock data URL into the page
    page.evaluate(f"window.MOCK_DATA_URL = '{mock_data_path.name}'")

    # Reload the page to ensure the mock data is used
    page.reload()

    # --- Assertions ---

    # 1. Check the status footer for the success message, which includes the skin name
    status_footer = page.locator("#etude_status_footer")
    expect(status_footer).to_contain_text("Skin:")
    expect(status_footer).to_contain_text("Data:")

    # 2. Check that the dynamic content is rendered
    dynamic_content_container = page.locator("#dynamic-content-container")

    # Assert that the mock quote content is visible
    # We get this from our mock data file to ensure the test is consistent
    import json
    mock_json = json.loads(mock_data_content)
    quote_content = mock_json["one"]["data"]["random_quote"]["content"]
    expect(dynamic_content_container).to_contain_text(quote_content)

    # Assert that the todo item is visible
    todo_title = mock_json["one"]["data"]["sample_todo"]["title"]
    expect(dynamic_content_container).to_contain_text(todo_title)

    # Assert that the placeholder is gone
    expect(page.locator("p.placeholder")).to_have_count(0)


@pytest.mark.parametrize("mock_data_path", ["success"], indirect=True)
def test_etude_zero_renders_status_table(page: Page, live_server: str, mock_data_path: Path):
    """
    Test that Etude Zero correctly renders the status table for all etudes.
    """
    mock_data_content = mock_data_path.read_text()

    def handle_route(route: Route, request: Request):
        route.fulfill(status=200, content_type="application/json", body=mock_data_content)

    etude_zero_url = f"{live_server}/zero/index.html"
    page.goto(etude_zero_url, wait_until="domcontentloaded")

    # Inject the mock data URL into the page
    page.evaluate(f"window.MOCK_DATA_URL = '{mock_data_path.name}'")

    # Reload the page to ensure the mock data is used
    page.reload()

    # --- Assertions ---
    status_footer = page.locator("#etude_status_footer")
    expect(status_footer).to_contain_text("Skin:")
    expect(status_footer).to_contain_text("Data:")

    status_container = page.locator("#daily-status-container")

    # Check that the table was rendered
    expect(status_container.locator("table")).to_have_count(1)

    # Check for Etude One's status from the mock data
    import json
    mock_json = json.loads(mock_data_content)
    etude_one_log_message = mock_json["one"]["actions_log"][0]
    expect(status_container).to_contain_text("one") # Etude name
    expect(status_container).to_contain_text("OK") # Status
    expect(status_container).to_contain_text(etude_one_log_message) # Part of the log

    # Check for Etude Zero's status
    expect(status_container).to_contain_text("zero")
    expect(status_container).to_contain_text("NO_OP")

def test_etude_one_handles_no_data_scenario(page: Page, live_server: str):
    """
    Test that Etude One displays an appropriate message when no data release is found.
    This test does not need to generate mock data, as it simulates a total fetch failure.
    """
    def handle_route_404(route: Route, request: Request):
        """Intercept the GitHub API call and respond with a 404 Not Found."""
        print(f"Intercepted request to: {request.url} -> Responding with 404")
        route.fulfill(
            status=404,
            content_type="application/json",
            body='{"message": "Not Found"}'
        )

    etude_one_url = f"{live_server}/one/index.html"
    page.goto(etude_one_url, wait_until="domcontentloaded")

    # Inject the mock data URL for a 'not_found' scenario
    page.evaluate("window.MOCK_DATA_URL = 'mock_data_not_found.json'")

    # Reload the page to ensure the mock data is used
    page.reload()

    # --- Assertions ---

    # 1. Check the status footer for the specific "not_found" message
    status_footer = page.locator("#etude_status_footer")
    expect(status_footer).to_contain_text("No recent data found")

    # 2. Check that the dynamic content container shows the corresponding message
    dynamic_content_container = page.locator("#dynamic-content-container")
    expect(dynamic_content_container).to_contain_text("No recent daily data could be found")

    # 3. Ensure the original "Loading..." placeholder text is gone
    expect(dynamic_content_container).not_to_contain_text("Loading daily content...")
