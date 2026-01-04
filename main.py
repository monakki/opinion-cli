#!/usr/bin/env python3
"""Opinion CLI - Command line interface for Opinion prediction market."""

import click
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Opinion CLI - Command line interface for Opinion prediction market."""
    pass


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
