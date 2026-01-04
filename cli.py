#!/usr/bin/env python3
"""Universal CLI entry point for Opinion CLI commands."""

import sys
from dotenv import load_dotenv
from commands.config import config
from commands.balance import balance
from commands.help import help
from commands.markets import markets

# Load environment variables from .env file
load_dotenv()


def main():
    """Main entry point that routes to the correct command based on script name."""
    import os

    # Use os.path.basename for cross-platform compatibility
    script_name = os.path.basename(sys.argv[0])

    # Define available commands mapping
    COMMANDS = {
        "config": config,
        "balance": balance,
        "help": help,
        "markets": markets,
    }

    if script_name in COMMANDS:
        COMMANDS[script_name]()
    else:
        # Show help when unknown command is used
        print("❌ Unknown command.")
        print("\n📚 Available commands:")
        for cmd_name in COMMANDS.keys():
            print(f"   • {cmd_name}")
        print("\n💡 Run 'uv run help' for detailed information")
        sys.exit(1)


if __name__ == "__main__":
    main()
