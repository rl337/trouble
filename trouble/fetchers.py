import abc
import requests
import json
from typing import NamedTuple, Optional, List, Dict, Any, Tuple, Callable
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

class TransformingURLFetcher(URLFetcher):
    """Fetches data from a URL and applies a JSON transform before returning.

    The transform function should accept the parsed JSON (or text) returned by
    URLFetcher and return the transformed value that matches the expected schema.
    If the transform raises, the fetch is considered failed.
    """
    def __init__(self, url: str, schema: Dict[str, Any], transform: Callable[[Any], Any], timeout: int = 10):
        super().__init__(url=url, schema=schema, timeout=timeout)
        self.transform = transform

    def fetch(self) -> Tuple[bool, Any, Optional[str]]:
        success, data, error_message = super().fetch()
        if not success:
            return success, data, error_message
        try:
            transformed = self.transform(data)
            return True, transformed, None
        except Exception as e:
            return False, None, f"Error transforming data from {self.url}: {e}"

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
