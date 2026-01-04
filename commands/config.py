"""Configuration commands for Opinion CLI."""

import click
from commands.base import BaseCommand
from utils.formatters import format_config_info, format_connection_test
from config.constants import SEPARATOR_LENGTH


@click.command()
@BaseCommand.handle_errors
def config():
    """Show current configuration and test connection."""
    client = BaseCommand.get_client()
    config_info = client.get_config_info()

    # Show configuration
    click.echo(format_config_info(config_info))

    # Test connection
    click.echo("\n" + "=" * SEPARATOR_LENGTH)
    click.echo("🔗 Connection Test:")
    result = client.test_connection()
    click.echo(format_connection_test(result))
