"""Configuration commands for Opinion CLI."""

import click
from client.opinion_client import OpinionClientWrapper
from utils.formatters import format_config_info, format_connection_test


@click.command()
def config():
    """Show current configuration and test connection."""
    try:
        client = OpinionClientWrapper.from_env()
        config_info = client.get_config_info()

        # Show configuration
        click.echo(format_config_info(config_info))

        # Test connection
        click.echo("\n" + "=" * 40)
        click.echo("🔗 Connection Test:")
        result = client.test_connection()
        click.echo(format_connection_test(result))

    except ValueError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        click.echo("\nMinimal configuration for read-only access:")
        click.echo("- API_KEY (required)")
        click.echo("\nFull configuration for trading:")
        click.echo("- API_KEY (required)")
        click.echo("- RPC_URL (required)")
        click.echo("- PRIVATE_KEY (required)")
        click.echo("- MULTI_SIG_ADDRESS (required)")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
