import pytest
import subprocess
import threading
import http.server
import socketserver
import os
import json
from pathlib import Path

# Define the port for the test server
PORT = 8008

@pytest.fixture(scope="session")
def project_root() -> Path:
    """A fixture to provide the project root directory."""
    return Path(__file__).parent.parent.parent # Up three levels from tests/e2e/conftest.py

@pytest.fixture(scope="session")
def static_site_path(project_root: Path) -> Path:
    """
    A fixture that generates the static site once per test session
    and returns the path to the 'docs' directory.
    """
    docs_path = project_root / "docs"

    # Run the generate command to build the site
    # Using subprocess to ensure we run it in the correct environment
    # and capture output.
    print("\nGenerating static site for E2E tests...")
    result = subprocess.run(
        ["poetry", "run", "trouble", "generate"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Site generation failed: {result.stderr}"
    print("Static site generated successfully.")

    return docs_path

@pytest.fixture(scope="session")
def live_server(static_site_path: Path):
    """
    A fixture that serves the generated static site on a local server
    for the entire test session.
    """
    Handler = http.server.SimpleHTTPRequestHandler

    # We need to change directory so the handler serves from 'docs'
    # but we must do it in a thread-safe way.
    class CWD_Handler(Handler):
        def __init__(self, *args, **kwargs):
            # The directory is passed to the server, so we don't need to os.chdir
            super().__init__(*args, **kwargs)

    # Use socketserver to handle requests in a separate thread
    with socketserver.TCPServer(("", PORT), lambda *args, **kwargs: CWD_Handler(*args, directory=str(static_site_path), **kwargs)) as httpd:
        print(f"\nServing static site from '{static_site_path}' at http://localhost:{PORT}")

        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True # Allow main thread to exit even if server is running
        server_thread.start()

        yield f"http://localhost:{PORT}" # Yield the base URL to the tests

        print(f"\nShutting down live server at http://localhost:{PORT}")
        httpd.shutdown()
        server_thread.join()

@pytest.fixture(scope="function")
def mock_data_path(request, static_site_path: Path, project_root: Path) -> Path:
    """
    A fixture that generates a mock data JSON file for a given scenario
    and returns the path to it.
    `request.param` will hold the scenario name string.
    """
    scenario = request.param
    # The mock data needs to be created in the directory served by the live_server
    output_file = static_site_path / f"mock_data_{scenario}.json"


    print(f"Generating mock data for scenario: '{scenario}' into {output_file}")

    result = subprocess.run(
        ["poetry", "run", "trouble", "generate-mock-data", "--scenario", scenario, "--output", str(output_file)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Mock data generation failed for scenario '{scenario}': {result.stderr}"

    assert output_file.exists(), f"Mock data file was not created at {output_file}"

    return output_file
