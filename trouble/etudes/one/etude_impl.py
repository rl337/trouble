import os
from string import Template
from typing import List, Tuple # For type hinting
from trouble.etude_core import Etude, EtudeRegistry
from trouble.fetchers import Fetcher, URLFetcher, StaticFetcher
from trouble.log_config import get_logger

logger = get_logger(__name__)

class EtudeOne(Etude):
    NAME = "one"
    DESCRIPTION = "Placeholder Etude One. This is a sample etude to demonstrate the system."

    def __init__(self):
        super().__init__(name=EtudeOne.NAME, description=EtudeOne.DESCRIPTION)

    def get_metrics(self, registry: EtudeRegistry) -> dict[str, any]:
        # Example metrics. Could also use the registry if needed.
        return {
            "Status": "Pending Implementation",
            "Items Processed": 0,
            "Version": "0.1-alpha"
        }

    def get_daily_resources(self) -> List[Tuple[str, Fetcher]]:
        """
        Defines the daily data resources to be fetched for EtudeOne.
        Each resource includes a schema definition.
        """
        # Define schemas for the data we expect from the URLs
        quote_schema = {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "author": {"type": "string"},
            },
            "required": ["content", "author"]
        }

        todo_schema = {
            "type": "object",
            "properties": {
                "userId": {"type": "integer"},
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "completed": {"type": "boolean"}
            },
            "required": ["id", "title", "completed"]
        }

        resources = [
            ("random_quote", URLFetcher("https://api.quotable.io/random", schema=quote_schema)),
            ("sample_todo", URLFetcher("https://jsonplaceholder.typicode.com/todos/1", schema=todo_schema)),
            ("static_info", StaticFetcher({"version": "1.0", "status": "active for etude one", "message": "This is static data defined in EtudeOne."})) # Schema will be inferred
        ]
        return resources

    def generate_content(self, output_dir: str, registry: EtudeRegistry, build_info: dict) -> None:
        # This method will be updated in Phase 2 to generate an app shell
        # and expect client-side JS to render the data fetched by get_daily_resources.
        # For now, it might render based on its static metrics or placeholders.
        # Or, if we want to test the data flow earlier, it could try to read
        # a local file that daily_runner.py might write (though that's not the final plan).
        # For this step, let's keep generate_content as is, focusing on get_daily_resources.
        # The actual use of fetched data in generate_content is part of a later phase.
        os.makedirs(output_dir, exist_ok=True)

        metrics_self = self.get_metrics(registry)

        template_data = {
            "etude_name": self.name,
            "etude_description": self.description,
            "metrics_status": metrics_self.get("Status", "N/A"),
            "metrics_items": str(metrics_self.get("Items Processed", "N/A")),
            "metrics_version": metrics_self.get("Version", "N/A")
        }

        # Path to the generic etude template
        # Assumes trouble/templates/etude_generic_index.html.template exists
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # up to 'trouble'
        template_path = os.path.join(base_dir, "templates", "etude_generic_index.html.template")

        try:
            with open(template_path, "r") as f_template:
                template_str = f_template.read()
        except IOError as e:
            logger.error(f"Error reading generic template for {self.name} ({template_path}): {e}")
            output_content = f"<h1>Error</h1><p>Could not load template for Etude {self.name}.</p>"
        else:
            tmpl = Template(template_str)
            output_content = tmpl.safe_substitute(template_data)

        output_file_path = os.path.join(output_dir, "index.html")
        try:
            with open(output_file_path, "w") as f:
                f.write(output_content)
            logger.info(f"Generated content for {self.name} at: {output_file_path}")
        except IOError as e:
            logger.error(f"Error writing content for {self.name}: {e}")
