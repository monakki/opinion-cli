#!/usr/bin/env python3
"""Standalone config command for Opinion CLI."""

from dotenv import load_dotenv
from commands.config import config

# Load environment variables from .env file
load_dotenv()


def main():
    """Main entry point for config command."""
    config()


if __name__ == "__main__":
    main()
