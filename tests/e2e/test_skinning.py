import pytest
from playwright.sync_api import Page, expect, Route, Request
from pathlib import Path
import re

# Re-use the API URL pattern from the other E2E test
from .test_etude_rendering import API_URL_PATTERN

@pytest.mark.parametrize("mock_data_path", ["success"], indirect=True)
def test_skin_is_applied(page: Page, live_server: str, mock_data_path: Path):
    """
    Test that a skin's CSS file is dynamically loaded and its classes are applied.
    """
    mock_data_content = mock_data_path.read_text()

    def handle_api_route(route: Route, request: Request):
        """Intercept the GitHub API call and respond with our mock data."""
        route.fulfill(status=200, content_type="application/json", body=mock_data_content)

    page.route(API_URL_PATTERN, handle_api_route)

    etude_one_url = f"{live_server}/one/index.html"
    page.goto(etude_one_url)

    # --- Assertions ---

    # 1. Assert that a skin's CSS file was loaded.
    # We can check for the <link> tag in the <head>.
    # The specific skin chosen depends on the time the test is run.
    # We can check for any of the expected skin CSS files.
    css_link = page.locator('head > link[rel="stylesheet"][id^="skin-css-"]')
    expect(css_link).to_have_count(1, timeout=10000) # Wait for JS to apply the skin

    loaded_css_href = css_link.get_attribute("href")
    print(f"Detected loaded skin CSS: {loaded_css_href}")
    assert loaded_css_href in ["/assets/skins/css/shade.css", "/assets/skins/css/sun.css", "/assets/skins/css/default.css"]

    # 2. Assert that a widget class from the skin is applied.
    # The `content.mustache` template applies `widget_classes.title`.
    title_element = page.locator("#dynamic-content-container > h3")

    # We need to get the class attribute and check if it matches one of the skin classes.
    title_class = title_element.get_attribute("class")
    print(f"Detected title class: {title_class}")

    # The class could be from any of the skins, e.g., 'shade-title-day', 'sun-title-morning', etc.
    # A simple check is to ensure it's not empty and contains "title".
    assert title_class is not None
    assert "title" in title_class

    # 3. Check the status footer for the skin name.
    status_footer = page.locator("#etude_status_footer")
    expect(status_footer).to_contain_text("Skin:")


@pytest.mark.parametrize("mock_data_path", ["success"], indirect=True)
def test_skin_context_logic(page: Page, live_server: str, mock_data_path: Path):
    """
    Test the skin selection logic by mocking the date to force a specific context.
    This demonstrates how time-based skins would be tested in a real CI environment.
    """
    mock_data_content = mock_data_path.read_text()

    # Mock the date to be a summer morning (e.g., June 21st, 10:00 AM)
    # Playwright can do this by evaluating script on the page before other scripts run.
    # The ISO string for a summer morning date
    mock_iso_date = "2024-06-21T10:00:00.000Z"

    page.add_init_script(f"""
        // Mock the Date object
        const OriginalDate = window.Date;
        class MockDate extends OriginalDate {{
            constructor() {{
                super('{mock_iso_date}');
            }}
            static now() {{
                return new OriginalDate('{mock_iso_date}').getTime();
            }}
        }}
        window.Date = MockDate;
    """)

    def handle_api_route(route: Route, request: Request):
        route.fulfill(status=200, content_type="application/json", body=mock_data_content)

    page.route(API_URL_PATTERN, handle_api_route)

    etude_one_url = f"{live_server}/one/index.html"
    page.goto(etude_one_url)

    # --- Assertions ---
    # Now we can assert a specific skin was chosen deterministically.
    # Context is: ['etude:one', 'time_of_day:morning', 'day_period:day', 'season:summer']
    # `shade_day` (score 1) and `sun_morning` (score 1) are tied.
    # The tie-breaking logic sorts by name, so 'shade_day' should be chosen over 'sun_morning'.

    status_footer = page.locator("#etude_status_footer")
    expect(status_footer).to_contain_text("Skin: shade_day")

    # And check that the specific class from the 'shade_day' skin is applied
    title_element = page.locator("#dynamic-content-container > h3")
    expect(title_element).to_have_class("shade-title-day")
