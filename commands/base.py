"""Base command functionality for Opinion CLI."""

import click
import os
from typing import Callable, Any
from client.opinion_clob_client import OpinionClobClientWrapper
from config.constants import DUMMY_PRIVATE_KEY


class BaseCommand:
    """Base class for CLI commands with common error handling."""

    @staticmethod
    def handle_errors(func: Callable) -> Callable:
        """Decorator for common error handling in commands."""

        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                click.echo(f"❌ Configuration error: {e}", err=True)
                BaseCommand._show_config_help()
            except Exception as e:
                click.echo(f"❌ Error: {e}", err=True)

        return wrapper

    @staticmethod
    def _show_config_help():
        """Show configuration help message."""
        click.echo("\nMinimal configuration for read-only access:")
        click.echo("- API_KEY (required)")
        click.echo("\nFull configuration for trading:")
        click.echo("- API_KEY (required)")
        click.echo("- RPC_URL (required)")
        click.echo("- PRIVATE_KEY (required)")
        click.echo("- MULTI_SIG_ADDRESS (required)")

    @staticmethod
    def get_client() -> OpinionClobClientWrapper:
        """Get Opinion CLOB client with error handling."""
        return OpinionClobClientWrapper.from_env()

    @staticmethod
    def validate_balance_requirements() -> bool:
        """Validate that required credentials are set for balance operations."""
        api_key = os.getenv("API_KEY")
        private_key = os.getenv("PRIVATE_KEY")

        missing_credentials = []

        if not api_key:
            missing_credentials.append("API_KEY")

        if not private_key or private_key == DUMMY_PRIVATE_KEY:
            missing_credentials.append("PRIVATE_KEY")

        if missing_credentials:
            click.echo(
                "❌ Missing required credentials for balance operations:", err=True
            )
            for cred in missing_credentials:
                click.echo(f"   • {cred}", err=True)

            click.echo("\n💡 Balance operations require:")
            click.echo("   • API_KEY - Your Opinion API key")
            click.echo("   • PRIVATE_KEY - Your wallet's private key")
            click.echo("\n📖 See README.md for setup instructions")
            return False

        return True
