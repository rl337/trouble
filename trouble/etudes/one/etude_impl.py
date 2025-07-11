import os
from string import Template
from trouble.etude_core import Etude, EtudeRegistry

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

    def generate_content(self, output_dir: str, registry: EtudeRegistry) -> None:
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
            print(f"Error reading generic template for {self.name} ({template_path}): {e}")
            output_content = f"<h1>Error</h1><p>Could not load template for Etude {self.name}.</p>"
        else:
            tmpl = Template(template_str)
            # Use safe_substitute to avoid KeyErrors if not all placeholders are filled
            output_content = tmpl.safe_substitute(template_data)


        output_file_path = os.path.join(output_dir, "index.html")
        try:
            with open(output_file_path, "w") as f:
                f.write(output_content)
            print(f"Generated content for {self.name} at: {output_file_path}")
        except IOError as e:
            print(f"Error writing content for {self.name}: {e}")

if __name__ == '__main__':
    print("EtudeOne class defined. For testing, instantiate and call methods with a mock/test EtudeRegistry.")
    # mock_registry = EtudeRegistry()
    # etude_one = EtudeOne()
    # mock_registry.register_etude(etude_one)
    # print("Metrics for EtudeOne:", etude_one.get_metrics(mock_registry))
    # # etude_one.generate_content("docs/one", mock_registry) # Needs templates setup
    print("Note: Full testing of generate_content requires etude_generic_index.html.template to be set up.")
