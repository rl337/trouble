import argparse
from .log_config import get_logger

logger = get_logger(__name__)

# --- Command Handlers ---

def handle_generate(args):
    from . import generator
    generator.run_generation(git_hash=args.git_hash)

def handle_daily(args):
    import json
    from .etude_core import EtudeRegistry
    from .daily_runner import execute_daily_etude_tasks

    logger.info("Starting daily tasks...")
    registry = EtudeRegistry()
    registry.discover_etudes(package_name="trouble.etudes")
    results = execute_daily_etude_tasks(registry)

    # This command's primary output is the JSON data to stdout for capture.
    # We add markers to make extraction from workflow logs easier.
    print("\n--- Daily Tasks Output JSON Start ---")
    print(json.dumps(results, indent=2))
    print("--- Daily Tasks Output JSON End ---")
    logger.info("Daily tasks finished.")

def handle_generate_mock_data(args):
    import json
    from .etude_core import EtudeRegistry
    from .mock_data_generator import generate_mock_data

    logger.info(f"Generating mock data for scenario: {args.scenario}")
    registry = EtudeRegistry()
    registry.discover_etudes(package_name="trouble.etudes")
    mock_data = generate_mock_data(args.scenario, registry)

    if args.output:
        try:
            with open(args.output, "w") as f:
                json.dump(mock_data, f, indent=2)
            logger.info(f"Mock data written to {args.output}")
        except IOError as e:
            logger.error(f"Error writing mock data to file: {e}")
            exit(1)
    else:
        # The primary output for this command is the JSON data.
        print(json.dumps(mock_data, indent=2))
    logger.info("Mock data generation finished.")

def handle_github_actions(args):
    if args.action == "create-release-info":
        import json
        from datetime import datetime
        from .release_manager import ReleaseManager

        manager = ReleaseManager(prefix="data-daily-")
        try:
            info = manager.get_release_info(datetime.utcnow())
            # This command's primary output is the JSON data for the workflow.
            print(json.dumps(info))
        except ValueError as e:
            logger.error(f"Error creating release info: {e}")
            exit(1)
    else:
        logger.error(f"Unknown github-actions action: {args.action}")
        # Consider printing help for the github-actions subparser
        exit(1)

def main():
    # The log_config module is imported at the top, which sets up logging.
    parser = argparse.ArgumentParser(description="Trouble: A multi-purpose CLI tool.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # --- Top-level Commands ---
    parser_generate = subparsers.add_parser("generate", help="Generate documentation from templates.")
    parser_generate.add_argument("--git-hash", type=str, default="N/A", help="The git hash of the build, passed from CI.")
    parser_generate.set_defaults(func=handle_generate)

    parser_daily = subparsers.add_parser("daily", help="Run daily tasks for all etudes.")
    parser_daily.set_defaults(func=handle_daily)

    parser_mock_data = subparsers.add_parser("generate-mock-data", help="Generate mock data for testing.")
    parser_mock_data.add_argument("--scenario", type=str, required=True, choices=["success", "partial_failure", "no_data"], help="The mock data scenario to generate.")
    parser_mock_data.add_argument("--output", type=str, default=None, help="Optional path to write the output JSON file. If not provided, prints to stdout.")
    parser_mock_data.set_defaults(func=handle_generate_mock_data)

    # --- GitHub Actions Command Group ---
    parser_gh = subparsers.add_parser("github-actions", help="Commands for use in GitHub Actions workflows.")
    gh_subparsers = parser_gh.add_subparsers(dest="action", help="GitHub Actions sub-command", required=True)

    # Sub-command for creating release info
    parser_gh_release_info = gh_subparsers.add_parser("create-release-info", help="Generate and validate release info (tag, name) as JSON.")
    parser_gh_release_info.set_defaults(func=handle_github_actions)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
