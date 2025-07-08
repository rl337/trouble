import argparse

def main():
    parser = argparse.ArgumentParser(description="Trouble: A multi-purpose CLI tool.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generator sub-command
    parser_generate = subparsers.add_parser("generate", help="Generate documentation from templates.")
    # Add arguments specific to generate if needed in the future
    # parser_generate.add_argument("--output-dir", default="docs/", help="Directory to output generated files.")

    args = parser.parse_args()

    if args.command == "generate":
        # Import and call the generator logic
        from . import generator
        # Placeholder for passing arguments from CLI to generator.run_generation if any are added
        generator.run_generation()
    elif args.command is None:
        parser.print_help()
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()

if __name__ == "__main__":
    main()
