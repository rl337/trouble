import json
from typing import Dict, Any
from faker import Faker
from jsonschema import validate

# A simple faker instance for generating data
fake = Faker()

# This is a basic implementation. A more advanced version could use libraries
# that generate fake data directly from a JSON schema. For now, we'll use
# a mapping of schema types to faker methods.

def generate_data_from_schema(schema: Dict[str, Any]) -> Any:
    """
    Generates a single piece of mock data that conforms to a given JSON schema.
    This is a simplified implementation.
    """
    schema_type = schema.get("type")

    if schema_type == "object":
        obj = {}
        if "properties" in schema:
            for prop, prop_schema in schema["properties"].items():
                obj[prop] = generate_data_from_schema(prop_schema)
        return obj
    elif schema_type == "array":
        # Generate a small array of items for mock data
        num_items = fake.random_int(min=1, max=3)
        if "items" in schema:
            return [generate_data_from_schema(schema["items"]) for _ in range(num_items)]
        else:
            return []
    elif schema_type == "string":
        # A more sophisticated version could look at format (e.g., 'date-time')
        # or use property names to guess content (e.g., 'name', 'address').
        return fake.sentence(nb_words=5)
    elif schema_type == "integer":
        return fake.random_int(min=0, max=1000)
    elif schema_type == "number":
        return fake.pyfloat(left_digits=3, right_digits=2, positive=True)
    elif schema_type == "boolean":
        return fake.boolean()
    else:
        # Fallback for unknown or missing types
        return None

def generate_mock_data(scenario: str, registry) -> Dict[str, Any]:
    """
    Generates a complete mock data structure for all etudes based on a scenario.

    Args:
        scenario: The name of the scenario to generate ('success', 'partial_failure', 'no_data').
        registry: An EtudeRegistry instance with discovered etudes.

    Returns:
        A dictionary representing the full daily_etude_data.json structure.
    """
    print(f"Generating mock data for scenario: {scenario}")
    all_etudes_mock_data = {}
    etudes_list = registry.get_all_etudes()

    if scenario == "no_data":
        # For 'no_data' scenario, we just return an empty dict or indicate failure for all.
        for etude in etudes_list:
            all_etudes_mock_data[etude.name] = {
                "status": "NOT_FOUND", # Or a relevant status
                "data": None,
                "actions_log": [f"Mock scenario 'no_data': No data release found for {etude.name}."]
            }
        return all_etudes_mock_data

    for etude in etudes_list:
        etude_resources = etude.get_daily_resources()
        etude_data = {}
        actions_log = []

        if not etude_resources:
            all_etudes_mock_data[etude.name] = {
                "status": "NO_OP",
                "data": None,
                "actions_log": ["No daily resources defined."]
            }
            continue

        # For partial_failure, let's decide to fail the first resource of the first etude that has resources
        is_first_resource = True
        should_fail_this_etude = (scenario == "partial_failure" and any(etude_resources))

        for resource_name, fetcher in etude_resources:
            if should_fail_this_etude and is_first_resource:
                etude_data[resource_name] = None
                actions_log.append(f"Mock scenario 'partial_failure': Failed to fetch '{resource_name}'.")
                is_first_resource = False # Only fail the first one
                continue

            schema = fetcher.get_schema()
            mock_resource_data = generate_data_from_schema(schema)

            # Optional: Validate generated data against the schema
            try:
                validate(instance=mock_resource_data, schema=schema)
                etude_data[resource_name] = mock_resource_data
                actions_log.append(f"Mock scenario 'success': Generated data for '{resource_name}'.")
            except Exception as e:
                actions_log.append(f"Mock data validation failed for '{resource_name}': {e}")
                etude_data[resource_name] = None

        # Determine overall status for the mock etude result
        status = "OK"
        if scenario == "partial_failure" and any(etude_resources):
            status = "PARTIAL_SUCCESS"

        all_etudes_mock_data[etude.name] = {
            "status": status,
            "data": etude_data,
            "actions_log": actions_log
        }

        # Ensure we only apply the partial failure to the first possible etude
        if should_fail_this_etude:
            scenario = "success" # Reset scenario for subsequent etudes

    return all_etudes_mock_data

if __name__ == '__main__':
    # Example usage for direct testing of the generator
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from trouble.etude_core import EtudeRegistry

    registry = EtudeRegistry()
    registry.discover_etudes()

    print("\n--- Generating 'success' scenario ---")
    success_data = generate_mock_data("success", registry)
    print(json.dumps(success_data, indent=2))

    print("\n--- Generating 'partial_failure' scenario ---")
    partial_failure_data = generate_mock_data("partial_failure", registry)
    print(json.dumps(partial_failure_data, indent=2))

    print("\n--- Generating 'no_data' scenario ---")
    no_data = generate_mock_data("no_data", registry)
    print(json.dumps(no_data, indent=2))
