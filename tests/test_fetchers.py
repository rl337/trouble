import unittest
from unittest.mock import patch, Mock
from trouble.fetchers import URLFetcher, StaticFetcher, EtudeDailyStatus, DailyEtudeResult

# Mocking requests.get
class MockResponse:
    def __init__(self, json_data, status_code, text_data=None):
        self.json_data = json_data
        self.status_code = status_code
        self.text = text_data if text_data is not None else str(json_data)

    def json(self):
        import json # Need to import json module
        if isinstance(self.json_data, dict) or isinstance(self.json_data, list):
            return self.json_data
        # This needs to raise the specific error the main code is expecting.
        raise json.JSONDecodeError("Mock JSON decode error", "", 0)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code} Client Error", response=self)

class TestFetchers(unittest.TestCase):

    def test_static_fetcher(self):
        """Test that StaticFetcher returns the data it was initialized with."""
        data = {"key": "value", "number": 123}
        fetcher = StaticFetcher(static_data=data)
        success, fetched_data, error_msg = fetcher.fetch()

        self.assertTrue(success)
        self.assertEqual(fetched_data, data)
        self.assertIsNone(error_msg)

    @patch('requests.get')
    def test_url_fetcher_success_json(self, mock_get):
        """Test URLFetcher with a successful JSON response."""
        mock_response_data = {"id": 1, "title": "Test Todo"}
        mock_get.return_value = MockResponse(json_data=mock_response_data, status_code=200)

        fetcher = URLFetcher("https://example.com/api/data")
        success, fetched_data, error_msg = fetcher.fetch()

        self.assertTrue(success)
        self.assertEqual(fetched_data, mock_response_data)
        self.assertIsNone(error_msg)
        mock_get.assert_called_once_with("https://example.com/api/data", timeout=10)

    @patch('requests.get')
    def test_url_fetcher_success_text(self, mock_get):
        """Test URLFetcher with a successful non-JSON (text) response."""
        mock_response_text = "<html><body>Hello</body></html>"
        # Mock a response that would fail .json()
        mock_get.return_value = MockResponse(json_data=None, status_code=200, text_data=mock_response_text)

        fetcher = URLFetcher("https://example.com/page.html")
        success, fetched_data, error_msg = fetcher.fetch()

        self.assertTrue(success)
        self.assertEqual(fetched_data, mock_response_text)
        self.assertIsNone(error_msg)

    @patch('requests.get')
    def test_url_fetcher_http_error(self, mock_get):
        """Test URLFetcher with a 404 HTTP error."""
        import requests

        # Configure the mock response object that requests.get() will return
        mock_response = Mock()
        mock_response.status_code = 404
        # Configure the raise_for_status method on the mock to raise the error
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{mock_response.status_code} Client Error", response=mock_response
        )
        mock_get.return_value = mock_response

        fetcher = URLFetcher("https://example.com/notfound")
        success, fetched_data, error_msg = fetcher.fetch()

        self.assertFalse(success)
        self.assertIsNone(fetched_data)
        self.assertIn("404", error_msg) # Check that the status code is in the error message

    @patch('requests.get')
    def test_url_fetcher_timeout_error(self, mock_get):
        """Test URLFetcher with a timeout error."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        fetcher = URLFetcher("https://example.com/slow")
        success, fetched_data, error_msg = fetcher.fetch()

        self.assertFalse(success)
        self.assertIsNone(fetched_data)
        self.assertIn("Timeout error", error_msg)

    def test_url_fetcher_invalid_url(self):
        """Test that URLFetcher raises ValueError for invalid URL protocols."""
        with self.assertRaises(ValueError):
            URLFetcher("ftp://example.com") # Should raise error on init

if __name__ == '__main__':
    unittest.main()
