import re
from datetime import datetime

class ReleaseManager:
    """
    Manages the logic for creating and validating release tags and names.
    """
    # According to Git documentation, a ref (which includes tags) cannot:
    # 1. Have a path component that begins with '.'
    # 2. Have a double dot '..'
    # 3. Contain an ASCII control character, '~', '^', ':', or whitespace
    # 4. Contain '?', '[', or '*'
    # 5. End with a '/' or a '.'
    # 6. Contain a sequence '@{'
    # A simplified regex for our specific tag format is sufficient and safer.
    # We expect 'prefix-YYYY-MM-DD'.
    VALID_TAG_REGEX = re.compile(r"^[a-zA-Z0-9_./-]+$")

    def __init__(self, prefix: str = "data-daily-"):
        if not prefix or not self.is_valid_prefix(prefix):
            raise ValueError(f"Invalid prefix '{prefix}'. Prefix must be simple and contain no invalid tag characters.")
        self.prefix = prefix

    def is_valid_prefix(self, prefix: str) -> bool:
        """Checks if the prefix itself is valid."""
        return bool(self.VALID_TAG_REGEX.match(prefix))

    def get_release_tag(self, date_obj: datetime) -> str:
        """
        Generates a release tag string for a given date.
        e.g., 'data-daily-2024-07-14'
        """
        date_str = date_obj.strftime('%Y-%m-%d')
        return f"{self.prefix}{date_str}"

    def is_valid_tag(self, tag: str) -> bool:
        """
        Validates if a given tag name is well-formed according to our rules.
        """
        if not tag:
            return False
        # Check against the general regex for allowed characters
        if not self.VALID_TAG_REGEX.match(tag):
            return False
        # Add any other specific structural checks if needed
        return True

    def get_release_info(self, date_obj: datetime) -> dict:
        """
        Generates and validates a dictionary of release information.
        Raises ValueError if the generated tag is invalid.
        """
        tag = self.get_release_tag(date_obj)
        if not self.is_valid_tag(tag):
            raise ValueError(f"Generated tag '{tag}' is invalid.")

        return {
            "tag_name": tag,
            "release_name": f"Daily Etude Data - {tag}"
        }

if __name__ == '__main__':
    # Example usage
    manager = ReleaseManager()
    now = datetime.utcnow()
    release_info = manager.get_release_info(now)
    print(f"Generated Release Info: {release_info}")

    # Test validation
    print(f"Is 'valid-tag_1.0' valid? {manager.is_valid_tag('valid-tag_1.0')}")
    print(f"Is 'invalid tag' valid? {manager.is_valid_tag('invalid tag')}")
    print(f"Is 'invalid~tag' valid? {manager.is_valid_tag('invalid~tag')}")
