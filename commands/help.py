"""Help command for Opinion CLI."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.command()
def help():
    """Show help information for Opinion CLI."""

    # Create main help panel
    help_content = [
        "🚀 Opinion CLI - Command line interface for Opinion prediction market",
        "",
        "Available commands:",
    ]

    # Create commands table
    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row("config", "Show current configuration and test connection")
    table.add_row("balance", "Show user's token balances")
    table.add_row("positions", "Show user's positions (portfolio)")
    table.add_row("trades", "Show user's trade history")
    table.add_row("orders", "Show user's orders with optional filters")
    table.add_row("markets", "Fetch and display markets from Opinion Open API")
    table.add_row("help", "Show this help message")

    # Display help
    with console.capture() as capture:
        console.print(
            Panel(
                "\n".join(help_content),
                title="📚 Opinion CLI Help",
                border_style="blue",
            )
        )
        console.print("\n")
        console.print(table)
        console.print("\n📖 For detailed help on a specific command, use:")
        console.print("   [cyan]uv run <command> --help[/cyan]")
        console.print("\n🔗 Documentation: https://github.com/monakki/opinion-cli")

    click.echo(capture.get())
