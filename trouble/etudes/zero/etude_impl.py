import os
from string import Template # Using string.Template for simplicity for now
from trouble.etude_core import Etude, EtudeRegistry

class EtudeZero(Etude):
    NAME = "zero"
    DESCRIPTION = "Project Overview and Metrics. This etude provides meta-information about the 'Trouble' project and all registered etudes."

    def __init__(self):
        super().__init__(name=EtudeZero.NAME, description=EtudeZero.DESCRIPTION)

    def get_metrics(self, registry: EtudeRegistry) -> dict[str, any]:
        all_etudes = registry.get_all_etudes()
        return {
            "Total Etudes Registered": len(all_etudes),
            "Etude Names": [e.name for e in all_etudes],
            # Add more relevant meta-metrics here later
        }

    def generate_content(self, output_dir: str, registry: EtudeRegistry) -> None:
        os.makedirs(output_dir, exist_ok=True)

        # Prepare data for the template
        metrics_self = self.get_metrics(registry)

        all_etudes_details = []
        for etude in registry.get_all_etudes():
            if etude.name == self.name: # Skip self for the "all etudes" table if desired, or include
                continue
            all_etudes_details.append({
                "name": etude.name,
                "description": etude.description,
                "metrics": etude.get_metrics(registry) # Get metrics from each etude
            })


        # Build the HTML table for other etudes
        etudes_table_html = ""
        if not all_etudes_details:
            etudes_table_html = "<p>No other etudes are currently registered to display details for.</p>"
        else:
            table_rows = []
            for detail in all_etudes_details:
                metrics_html_list = "<ul>"
                if detail['metrics']:
                    for k, v in sorted(detail['metrics'].items()): # Sort metrics for consistent order
                        metrics_html_list += f"<li><strong>{k}:</strong> {v}</li>"
                else:
                    metrics_html_list += "<li>No metrics reported.</li>"
                metrics_html_list += "</ul>"

                table_rows.append(f"""
<tr>
    <td>{detail['name']}</td>
    <td>{detail['description']}</td>
    <td>{metrics_html_list}</td>
</tr>""")
            etudes_table_html = "<table><thead><tr><th>Etude Name</th><th>Description</th><th>Metrics</th></tr></thead><tbody>" + "".join(table_rows) + "</tbody></table>"

        template_data = {
            "etude_name": self.name,
            "etude_description": self.description,
            "metrics_self_total_etudes": str(metrics_self.get("Total Etudes Registered", "N/A")),
            "metrics_self_etude_names": ", ".join(metrics_self.get("Etude Names", [])),
            "etudes_table_html": etudes_table_html
        }

        # Determine path to templates directory, assuming it's relative to this file's package's parent
        # trouble/etudes/zero/etude_impl.py -> trouble/templates/
        # This assumes a certain project structure.
        # A more robust way might be to pass templates_dir path from generator.py
        # or have a global config for paths.
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # up to 'trouble'
        template_path = os.path.join(base_dir, "templates", "etude_zero_index.html.template")

        try:
            with open(template_path, "r") as f_template:
                template_str = f_template.read()
        except IOError as e:
            print(f"Error reading template for EtudeZero ({template_path}): {e}")
            # Fallback to a very basic output if template is missing
            output_content = f"<h1>Error</h1><p>Could not load template for Etude {self.name}.</p>"
        else:
            tmpl = Template(template_str)
            # Use safe_substitute to avoid KeyErrors if not all placeholders are filled
            output_content = tmpl.safe_substitute(template_data)


        output_file_path = os.path.join(output_dir, "index.html")
        try:
            with open(output_file_path, "w") as f:
                f.write(output_content)
            print(f"Generated content for EtudeZero at: {output_file_path}")
        except IOError as e:
            print(f"Error writing content for EtudeZero: {e}")

if __name__ == '__main__':
    # Example usage for direct testing (won't fully work without a populated registry)
    print("EtudeZero class defined. For testing, instantiate and call methods with a mock/test EtudeRegistry.")
    # mock_registry = EtudeRegistry()
    # etude_zero = EtudeZero()
    # mock_registry.register_etude(etude_zero) # Register itself for metrics count
    # print("Metrics:", etude_zero.get_metrics(mock_registry))
    # # etude_zero.generate_content("docs/zero", mock_registry) # Needs templates setup
    print("Note: Full testing of generate_content requires templates to be set up in trouble/templates/")
