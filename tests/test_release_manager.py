import unittest
from datetime import datetime
from trouble.release_manager import ReleaseManager

class TestReleaseManager(unittest.TestCase):

    def test_tag_generation(self):
        """Test that tags are generated in the correct format."""
        manager = ReleaseManager(prefix="test-release-")
        test_date = datetime(2024, 7, 14)
        expected_tag = "test-release-2024-07-14"
        self.assertEqual(manager.get_release_tag(test_date), expected_tag)

    def test_valid_tags(self):
        """Test the tag validation logic with valid tags."""
        manager = ReleaseManager()
        self.assertTrue(manager.is_valid_tag("data-daily-2024-07-14"))
        self.assertTrue(manager.is_valid_tag("v1.0.0"))
        self.assertTrue(manager.is_valid_tag("my-feature_branch"))
        self.assertTrue(manager.is_valid_tag("a/b/c")) # Slashes are valid in refs

    def test_invalid_tags(self):
        """Test the tag validation logic with invalid tags."""
        manager = ReleaseManager()
        self.assertFalse(manager.is_valid_tag("invalid tag with spaces"))
        self.assertFalse(manager.is_valid_tag("invalid~tag"))
        self.assertFalse(manager.is_valid_tag("invalid:tag"))
        self.assertFalse(manager.is_valid_tag("invalid\\tag"))
        self.assertFalse(manager.is_valid_tag(""))
        self.assertFalse(manager.is_valid_tag(None))

    def test_get_release_info_success(self):
        """Test that release info is generated correctly with a valid tag."""
        manager = ReleaseManager(prefix="data-test-")
        test_date = datetime(2024, 7, 14)
        info = manager.get_release_info(test_date)
        self.assertEqual(info["tag_name"], "data-test-2024-07-14")
        self.assertIn("data-test-2024-07-14", info["release_name"])

    def test_get_release_info_failure(self):
        """Test that get_release_info raises an error for an invalid prefix."""
        with self.assertRaises(ValueError):
            # Initialize with an invalid prefix containing a space
            manager = ReleaseManager(prefix="invalid prefix ")
            manager.get_release_info(datetime.utcnow())

if __name__ == '__main__':
    unittest.main()
