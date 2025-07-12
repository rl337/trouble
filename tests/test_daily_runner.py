import unittest
from unittest.mock import MagicMock, patch
from typing import List, Tuple, Any, Optional

from trouble.etude_core import Etude, EtudeRegistry
from trouble.fetchers import Fetcher, DailyEtudeResult, EtudeDailyStatus
from trouble.daily_runner import execute_daily_etude_tasks

# --- Mock Implementations for Testing ---

class MockFetcher(Fetcher):
    """A mock fetcher that can be configured to succeed or fail."""
    def __init__(self, should_succeed: bool, return_data: Any, error_msg: str = "Mock fetch error"):
        self.should_succeed = should_succeed
        self.return_data = return_data
        self.error_msg = error_msg

    def fetch(self) -> Tuple[bool, Any, Optional[str]]:
        if self.should_succeed:
            return True, self.return_data, None
        else:
            return False, None, self.error_msg

class MockEtude(Etude):
    """A mock etude that can be configured with daily resources."""
    def __init__(self, name: str, description: str, daily_resources: List[Tuple[str, Fetcher]]):
        super().__init__(name, description)
        self._daily_resources = daily_resources

    def generate_content(self, output_dir: str, registry: 'EtudeRegistry') -> None:
        pass # Not needed for testing the daily runner

    def get_metrics(self, registry: 'EtudeRegistry') -> dict[str, any]:
        return {"static_metric": 1} # Not needed, but must be implemented

    def get_daily_resources(self) -> List[Tuple[str, Fetcher]]:
        return self._daily_resources

# --- Test Cases ---

class TestDailyRunner(unittest.TestCase):

    def test_no_etudes(self):
        """Test that the runner handles an empty registry correctly."""
        registry = EtudeRegistry()
        results = execute_daily_etude_tasks(registry)
        self.assertEqual(results, {})

    def test_etude_with_no_resources(self):
        """Test an etude that returns an empty list for daily resources."""
        etude_no_op = MockEtude(name="no_op_etude", description="", daily_resources=[])
        registry = EtudeRegistry()
        registry.register_etude(etude_no_op)

        results = execute_daily_etude_tasks(registry)

        self.assertIn("no_op_etude", results)
        result = results["no_op_etude"]
        self.assertEqual(result["status"], EtudeDailyStatus.NO_OP.value)
        self.assertIsNone(result["data"])
        self.assertIn("No daily resources defined", result["actions_log"][0])

    def test_etude_with_all_successful_fetches(self):
        """Test an etude where all resource fetches succeed."""
        etude_success = MockEtude(
            name="success_etude",
            description="",
            daily_resources=[
                ("resource1", MockFetcher(should_succeed=True, return_data={"a": 1})),
                ("resource2", MockFetcher(should_succeed=True, return_data=[1, 2, 3])),
            ]
        )
        registry = EtudeRegistry()
        registry.register_etude(etude_success)

        results = execute_daily_etude_tasks(registry)

        self.assertIn("success_etude", results)
        result = results["success_etude"]
        self.assertEqual(result["status"], EtudeDailyStatus.OK.value)
        self.assertIsNotNone(result["data"])
        self.assertEqual(result["data"]["resource1"], {"a": 1})
        self.assertEqual(result["data"]["resource2"], [1, 2, 3])
        self.assertEqual(len(result["actions_log"]), 2)
        self.assertIn("Successfully fetched resource 'resource1'", result["actions_log"][0])
        self.assertIn("Successfully fetched resource 'resource2'", result["actions_log"][1])

    def test_etude_with_all_failed_fetches(self):
        """Test an etude where all resource fetches fail."""
        etude_fail = MockEtude(
            name="fail_etude",
            description="",
            daily_resources=[
                ("resource1", MockFetcher(should_succeed=False, return_data=None, error_msg="API down")),
                ("resource2", MockFetcher(should_succeed=False, return_data=None, error_msg="Timeout")),
            ]
        )
        registry = EtudeRegistry()
        registry.register_etude(etude_fail)

        results = execute_daily_etude_tasks(registry)

        self.assertIn("fail_etude", results)
        result = results["fail_etude"]
        self.assertEqual(result["status"], EtudeDailyStatus.FAILED.value)
        self.assertIsNotNone(result["data"]) # data dict is created, but values are None
        self.assertIsNone(result["data"]["resource1"])
        self.assertIsNone(result["data"]["resource2"])
        self.assertEqual(len(result["actions_log"]), 2)
        self.assertIn("Failed to fetch resource 'resource1': API down", result["actions_log"][0])
        self.assertIn("Failed to fetch resource 'resource2': Timeout", result["actions_log"][1])

    def test_etude_with_partial_success(self):
        """Test an etude with a mix of successful and failed fetches."""
        etude_partial = MockEtude(
            name="partial_etude",
            description="",
            daily_resources=[
                ("good_resource", MockFetcher(should_succeed=True, return_data={"status": "ok"})),
                ("bad_resource", MockFetcher(should_succeed=False, return_data=None, error_msg="404 Not Found")),
            ]
        )
        registry = EtudeRegistry()
        registry.register_etude(etude_partial)

        results = execute_daily_etude_tasks(registry)

        self.assertIn("partial_etude", results)
        result = results["partial_etude"]
        self.assertEqual(result["status"], EtudeDailyStatus.PARTIAL_SUCCESS.value)
        self.assertIsNotNone(result["data"])
        self.assertEqual(result["data"]["good_resource"], {"status": "ok"})
        self.assertIsNone(result["data"]["bad_resource"])
        self.assertEqual(len(result["actions_log"]), 2)
        self.assertIn("Successfully fetched resource 'good_resource'", result["actions_log"][0])
        self.assertIn("Failed to fetch resource 'bad_resource': 404 Not Found", result["actions_log"][1])

if __name__ == '__main__':
    unittest.main()
