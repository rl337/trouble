import argparse

def main():
    parser = argparse.ArgumentParser(description="Trouble: A multi-purpose CLI tool.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generator sub-command
    parser_generate = subparsers.add_parser("generate", help="Generate documentation from templates.")
    # Add arguments specific to generate if needed in the future
    # parser_generate.add_argument("--output-dir", default="docs/", help="Directory to output generated files.")

    # Daily sub-command
    parser_daily = subparsers.add_parser("daily", help="Run daily tasks for all etudes.")
    # Add arguments specific to daily if needed in the future
    # parser_daily.add_argument("--force-rerun", action="store_true", help="Force rerun of tasks.")

    args = parser.parse_args()

    if args.command == "generate":
        from . import generator
        # Assuming generator.run_generation() takes output_dir as an argument
        # For now, using default "docs/" as per its definition.
        # If parser_generate had an --output-dir argument, it would be args.output_dir
        generator.run_generation()
    elif args.command == "daily":
        import json
        from .etude_core import EtudeRegistry
        from .daily_runner import execute_daily_etude_tasks # Import the new runner function

        print("Starting daily tasks...")
        registry = EtudeRegistry()
        registry.discover_etudes(package_name="trouble.etudes")

        results = execute_daily_etude_tasks(registry)

        # Output the results as a JSON string to stdout
        # This can be captured by the GitHub Action
        print("\n--- Daily Tasks Output JSON Start ---")
        print(json.dumps(results, indent=2))
        print("--- Daily Tasks Output JSON End ---")
        print("Daily tasks finished.")

    elif args.command is None:
        parser.print_help()
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()

if __name__ == "__main__":
    main()
