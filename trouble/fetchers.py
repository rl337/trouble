import abc
import requests
import json
from typing import NamedTuple, Optional, List, Dict, Any, Tuple
from enum import Enum

class EtudeDailyStatus(Enum):
    OK = "OK"
    FAILED = "FAILED"  # Indicates one or more resources failed to fetch
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS" # Indicates some resources fetched, others failed
    NO_OP = "NO_OP"    # Indicates an etude had no daily resources to process

class DailyEtudeResult(NamedTuple):
    status: EtudeDailyStatus
    data: Optional[Dict[str, Any]] # Aggregated data from all successful fetches for this etude
    actions_log: List[str]         # Log of actions, including errors for failed fetches

class Fetcher(abc.ABC):
    """Abstract base class for a data fetcher."""
    @abc.abstractmethod
    def fetch(self) -> Tuple[bool, Any, Optional[str]]:
        """
        Fetches data.
        Returns:
            A tuple: (success: bool, fetched_data: Any, error_message: Optional[str])
        """
        pass

    @abc.abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Returns the JSON schema for the data this fetcher is expected to return.
        """
        pass

class URLFetcher(Fetcher):
    """Fetches data from a URL using requests."""
    def __init__(self, url: str, schema: Dict[str, Any], timeout: int = 10):
        if not url.startswith(('http://', 'https://')):
            raise ValueError("Invalid URL provided. Must start with http:// or https://")
        self.url = url
        self.schema = schema
        self.timeout = timeout

    def get_schema(self) -> Dict[str, Any]:
        return self.schema

    def fetch(self) -> Tuple[bool, Any, Optional[str]]:
        try:
            response = requests.get(self.url, timeout=self.timeout)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            try:
                data = response.json()
                return True, data, None
            except json.JSONDecodeError:
                # If response is not JSON, return as text
                return True, response.text, None
        except requests.exceptions.Timeout:
            return False, None, f"Timeout error when fetching {self.url} after {self.timeout}s."
        except requests.exceptions.HTTPError as e:
            return False, None, f"HTTP error {e.response.status_code} when fetching {self.url}: {e}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Request error when fetching {self.url}: {e}"
        except Exception as e: # Catch any other unexpected error during fetch
            return False, None, f"Unexpected error fetching {self.url}: {e}"

class StaticFetcher(Fetcher):
    """Returns predefined static data."""
    def __init__(self, static_data: Any, schema: Optional[Dict[str, Any]] = None):
        self.static_data = static_data
        # If no schema is provided, we can try to infer a very basic one.
        if schema:
            self.schema = schema
        else:
            self.schema = self._infer_schema(static_data)

    def get_schema(self) -> Dict[str, Any]:
        return self.schema

    def _infer_schema(self, data: Any) -> Dict[str, Any]:
        """A very basic schema inference for static data."""
        data_type = type(data)
        if data_type is dict:
            return {"type": "object", "properties": {k: self._infer_schema(v) for k, v in data.items()}}
        elif data_type is list:
            if data:
                # Assume all items in the list are of the same type as the first
                return {"type": "array", "items": self._infer_schema(data[0])}
            else:
                return {"type": "array"} # Cannot infer item type from empty list
        elif data_type is str:
            return {"type": "string"}
        elif data_type is int:
            return {"type": "integer"}
        elif data_type is float:
            return {"type": "number"}
        elif data_type is bool:
            return {"type": "boolean"}
        else:
            return {} # Fallback for unknown types

    def fetch(self) -> Tuple[bool, Any, Optional[str]]:
        # Static data is always considered a "successful" fetch
        return True, self.static_data, None

if __name__ == '__main__':
    # Example Usage (for quick testing if run directly)
    print("Fetcher examples:")

    # URL Fetcher - Quotable (JSON)
    quote_fetcher = URLFetcher("https://api.quotable.io/random")
    success, data, error = quote_fetcher.fetch()
    if success:
        print(f"Quotable API (JSON) Success! Data: {str(data)[:100]}...")
    else:
        print(f"Quotable API (JSON) Failed! Error: {error}")

    # URL Fetcher - JSONPlaceholder (JSON)
    todo_fetcher = URLFetcher("https://jsonplaceholder.typicode.com/todos/1")
    success, data, error = todo_fetcher.fetch()
    if success:
        print(f"JSONPlaceholder API (JSON) Success! Data: {data}")
    else:
        print(f"JSONPlaceholder API (JSON) Failed! Error: {error}")

    # URL Fetcher - Example.com (HTML/Text)
    html_fetcher = URLFetcher("http://example.com")
    success, data, error = html_fetcher.fetch()
    if success:
        print(f"Example.com (HTML/Text) Success! Data: {str(data)[:100]}...")
    else:
        print(f"Example.com (HTML/Text) Failed! Error: {error}")

    # URL Fetcher - Non-existent URL (Error)
    error_fetcher = URLFetcher("https://thissitedoesnotexist12345.com/api")
    success, data, error = error_fetcher.fetch()
    if success:
        print(f"Non-existent URL Success! Data: {data}") # Should not happen
    else:
        print(f"Non-existent URL Failed! Error: {error}")

    # URL Fetcher - URL that returns 404 (Error)
    notfound_fetcher = URLFetcher("https://jsonplaceholder.typicode.com/nonexistentpath")
    success, data, error = notfound_fetcher.fetch()
    if success:
        print(f"404 URL Success! Data: {data}") # Should not happen
    else:
        print(f"404 URL Failed! Error: {error}")

    # Static Fetcher
    static_data_example = {"message": "Hello from StaticFetcher!", "version": 1.2}
    static_fetcher_instance = StaticFetcher(static_data_example)
    success, data, error = static_fetcher_instance.fetch()
    if success:
        print(f"StaticFetcher Success! Data: {data}")
    else:
        print(f"StaticFetcher Failed! Error: {error}") # Should not happen

    print("\nDailyEtudeResult example:")
    result_ok = DailyEtudeResult(EtudeDailyStatus.OK, {"key": "value"}, ["Action 1", "Action 2"])
    print(result_ok)
    result_failed = DailyEtudeResult(EtudeDailyStatus.FAILED, None, ["Failed to fetch X", "API Y returned 500"])
    print(result_failed)
    result_noop = DailyEtudeResult(EtudeDailyStatus.NO_OP, None, ["No daily tasks for this etude."])
    print(result_noop)
