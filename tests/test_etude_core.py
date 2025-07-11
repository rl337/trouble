import unittest
from trouble.etude_core import Etude, EtudeRegistry

# A minimal concrete Etude for testing purposes
class MockEtude(Etude):
    NAME = "mock_etude"
    DESCRIPTION = "A mock etude for testing."

    def __init__(self):
        super().__init__(name=self.NAME, description=self.DESCRIPTION)

    def generate_content(self, output_dir: str, registry: 'EtudeRegistry') -> None:
        # For testing, this might create a dummy file or just pass
        # print(f"MockEtude {self.name} generating content in {output_dir} with registry {registry}")
        pass

    def get_metrics(self, registry: 'EtudeRegistry') -> dict[str, any]:
        # For testing, return some simple metrics
        return {"mock_metric": 123, "registry_size_at_call": len(registry.get_all_etudes())}

class TestEtudeCore(unittest.TestCase):

    def test_etude_creation(self):
        """Test basic Etude instantiation and properties."""
        etude = MockEtude()
        self.assertEqual(etude.name, "mock_etude")
        self.assertEqual(etude.description, "A mock etude for testing.")

    def test_etude_registry_registration_and_retrieval(self):
        """Test registering and retrieving etudes from the registry."""
        registry = EtudeRegistry()
        etude1 = MockEtude()

        # Modify name for a second distinct etude if MockEtude.NAME is fixed
        # Or create another mock class. For now, let's assume we can change instance name for test
        # This is not ideal as NAME is a class attribute.
        # A better way would be to have different MockEtude classes or make NAME instance-settable for mocks.
        # For this initial test, we'll focus on the registry mechanics.

        # Let's create a second mock etude class for distinctness
        class MockEtudeTwo(Etude):
            NAME = "mock_etude_two"
            DESCRIPTION = "Another mock etude."
            def __init__(self): super().__init__(name=self.NAME, description=self.DESCRIPTION)
            def generate_content(self, od, reg): pass
            def get_metrics(self, reg): return {"val": 2}

        etude2 = MockEtudeTwo()

        registry.register_etude(etude1)
        registry.register_etude(etude2)

        self.assertEqual(len(registry.get_all_etudes()), 2)
        self.assertIn(etude1, registry.get_all_etudes())
        self.assertIn(etude2, registry.get_all_etudes())

        retrieved_etude1 = registry.get_etude("mock_etude")
        self.assertIsNotNone(retrieved_etude1)
        self.assertEqual(retrieved_etude1.name, "mock_etude")

        retrieved_etude2 = registry.get_etude("mock_etude_two")
        self.assertIsNotNone(retrieved_etude2)
        self.assertEqual(retrieved_etude2.name, "mock_etude_two")

        self.assertIsNone(registry.get_etude("non_existent_etude"))

    def test_etude_registry_discovery_placeholder(self):
        """
        Placeholder for testing etude discovery.
        This would require mocking the file system and import mechanisms,
        which is more involved and planned for the full testing phase.
        For now, this test just ensures the method runs without error with an empty/mock package.
        """
        registry = EtudeRegistry()
        # To properly test discovery, we'd need to:
        # 1. Create a temporary directory structure mimicking trouble/etudes/
        # 2. Add mock etude files there.
        # 3. Point registry.discover_etudes() to this temp package.
        # This is a simplified check for now.
        try:
            # Assuming 'trouble.etudes' exists but might be empty or have our actual etudes
            # This isn't a pure unit test of discovery logic itself without a controlled environment.
            registry.discover_etudes(package_name="trouble.etudes") # Should find EtudeZero and EtudeOne
            self.assertGreaterEqual(len(registry.get_all_etudes()), 0) # Should find at least 0, ideally 2

            # Check if actual etudes were found
            found_zero = registry.get_etude("zero")
            found_one = registry.get_etude("one")
            # Depending on test environment, these might be found.
            # For a CI environment, they should be.
            if found_zero:
                 self.assertEqual(found_zero.name, "zero")
            if found_one:
                 self.assertEqual(found_one.name, "one")

        except Exception as e:
            self.fail(f"discover_etudes raised an exception: {e}")

    def test_get_metrics_from_mock_etude(self):
        """Test that get_metrics can be called and uses the registry."""
        registry = EtudeRegistry()
        etude = MockEtude()
        registry.register_etude(etude)

        metrics = etude.get_metrics(registry)
        self.assertEqual(metrics["mock_metric"], 123)
        self.assertEqual(metrics["registry_size_at_call"], 1)


if __name__ == '__main__':
    unittest.main()
