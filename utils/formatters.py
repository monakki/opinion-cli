"""Output formatting utilities for Opinion CLI."""

from typing import Dict, Any, List
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Constants
console = Console()
DEFAULT_DECIMALS = 2
ADDRESS_DISPLAY_LENGTH = 10

# Token address to symbol mapping
TOKEN_SYMBOLS = {
    "0x55d398326f99059ff775485246999027b3197955": "USDT",
    # Add more token mappings here as needed
}

# Status indicators
STATUS_ICONS = {"success": "✅", "warning": "⚠️", "error": "❌", "info": "📊"}

STATUS_COLORS = {
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "cyan",
}


def format_token_address(address: str) -> str:
    """Format token address to symbol if known, otherwise return shortened address."""
    if address in TOKEN_SYMBOLS:
        return TOKEN_SYMBOLS[address]

    # If unknown token, show shortened address (first 6 + last 4 characters)
    if len(address) > ADDRESS_DISPLAY_LENGTH:
        return f"{address[:6]}...{address[-4:]}"

    return address


def _get_status_display(
    condition: bool, true_text: str = "Set", false_text: str = "Not set"
) -> tuple[str, str, str]:
    """Get status icon, color, and text based on condition."""
    if condition:
        return STATUS_ICONS["success"], STATUS_COLORS["success"], true_text
    else:
        return STATUS_ICONS["warning"], STATUS_COLORS["warning"], false_text


def format_config_info(config_info: Dict[str, Any]) -> str:
    """Format configuration information for display."""
    # Create main panel content
    content = []

    # Connection settings
    content.append(f"🌐 Host: [cyan]{config_info['host']}[/cyan]")
    content.append(f"⛓️  Chain ID: [cyan]{config_info['chain_id']}[/cyan]")
    content.append(
        f"📦 Multi-sig Address: [cyan]{config_info['multi_sig_address']}[/cyan]"
    )
    content.append("")

    # Mode indicator
    if config_info["read_only_mode"]:
        content.append("📖 Mode: [yellow]READ-ONLY[/yellow]")
        content.append("   └─ Can view markets, orders, and positions")
    else:
        content.append("💰 Mode: [green]FULL ACCESS[/green]")
        content.append("   └─ Can view and place orders/trades")

    content.append("")
    content.append("⚙️  Real-time Monitoring Settings:")

    # Real-time mode is always enabled (no caching by default)
    if config_info["realtime_mode"]:
        content.append("🟢 Real-time Mode: [green]ENABLED[/green] (No caching)")
        content.append("   ├─ Market Cache TTL: [dim]0s (disabled)[/dim]")
        content.append("   ├─ Quote Tokens Cache TTL: [dim]0s (disabled)[/dim]")
        content.append("   ├─ Trading Check Interval: [dim]0s (disabled)[/dim]")
        content.append(
            f"   └─ Rate Limit: [cyan]{config_info['rate_limit']} req/s[/cyan]"
        )
    else:
        content.append("🔵 Cached Mode: [blue]ENABLED[/blue]")
        content.append(
            f"   ├─ Market Cache TTL: [cyan]{config_info['market_cache_ttl']}s[/cyan]"
        )
        content.append(
            f"   ├─ Quote Tokens Cache TTL: [cyan]{config_info['quote_tokens_cache_ttl']}s[/cyan]"
        )
        content.append(
            f"   ├─ Trading Check Interval: [cyan]{config_info['enable_trading_check_interval']}s[/cyan]"
        )
        content.append(
            f"   └─ Rate Limit: [cyan]{config_info['rate_limit']} req/s[/cyan]"
        )
        content.append(
            f"   └─ Trading Check Interval: [cyan]{config_info['enable_trading_check_interval']}s[/cyan]"
        )

    content.append("")
    content.append("🔐 Credentials Status:")

    # Credentials status using helper function
    icon, color, text = _get_status_display(config_info["api_key_set"])
    content.append(f"  {icon} API Key: [{color}]{text}[/{color}]")

    icon, color, text = _get_status_display(
        config_info["rpc_url_set"], "Set", "Not set (read-only mode)"
    )
    content.append(f"  {icon} RPC URL: [{color}]{text}[/{color}]")

    icon, color, text = _get_status_display(
        config_info["private_key_set"], "Set", "Not set (read-only mode)"
    )
    content.append(f"  {icon} Private Key: [{color}]{text}[/{color}]")

    # Create panel
    panel = Panel(
        "\n".join(content), title="📋 Opinion CLI Configuration", border_style="blue"
    )

    # Capture output to string
    with console.capture() as capture:
        console.print(panel)
    return capture.get()


def format_connection_test(result: Dict[str, Any]) -> str:
    """Format connection test result for display."""
    if result["status"] == "success":
        content = [f"💬 {result['message']}"]
        panel = Panel(
            "\n".join(content),
            title="✅ Connection Test: SUCCESS",
            border_style="green",
        )
    else:
        content = [f"💬 {result['message']}"]
        panel = Panel(
            "\n".join(content), title="❌ Connection Test: FAILED", border_style="red"
        )

    with console.capture() as capture:
        console.print(panel)
    return capture.get()


def format_json(data: Any, indent: int = 2) -> str:
    """Format data as pretty JSON."""
    return json.dumps(data, indent=indent, ensure_ascii=False)


def format_table(headers: List[str], rows: List[List[str]], title: str = None) -> str:
    """Format data as a Rich table."""
    if not rows:
        return "No data to display"

    # Create Rich table
    table = Table(show_header=True, header_style="bold magenta")

    # Add columns
    for header in headers:
        table.add_column(header, style="cyan", no_wrap=False)

    # Add rows
    for row in rows:
        formatted_row = [str(cell) for cell in row]
        table.add_row(*formatted_row)

    # Capture output to string
    with console.capture() as capture:
        if title:
            console.print(f"\n[bold]{title}[/bold]")
        console.print(table)
    return capture.get()


def format_number(value: str, decimals: int = DEFAULT_DECIMALS) -> str:
    """Format number string to specified decimal places."""
    try:
        # Convert to float and format
        num = float(value)
        return f"{num:.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)


def format_balance_table(
    balances: List[Dict[str, Any]], wallet_info: Dict[str, str]
) -> str:
    """Format balance data as a Rich table with additional info."""
    if not balances:
        return "📊 No balances found"

    # Create Rich table
    table = Table(
        show_header=True, header_style="bold magenta", title="💰 Token Balances"
    )

    # Add columns
    table.add_column("Token", style="yellow", no_wrap=True)
    table.add_column("Available", style="green", justify="right")
    table.add_column("Frozen", style="red", justify="right")
    table.add_column("Total", style="cyan", justify="right")

    # Add rows with formatted numbers
    for balance in balances:
        table.add_row(
            format_token_address(balance.get("quote_token", "N/A")),
            format_number(balance.get("available_balance", "0")),
            format_number(balance.get("frozen_balance", "0")),
            format_number(balance.get("total_balance", "0")),
        )

    # Create info panel
    info_content = []
    if wallet_info.get("wallet_address"):
        info_content.append(f"📍 Wallet: [cyan]{wallet_info['wallet_address']}[/cyan]")
    if wallet_info.get("chain_id"):
        info_content.append(f"🔗 Chain ID: [cyan]{wallet_info['chain_id']}[/cyan]")
    if wallet_info.get("multi_sign_address"):
        info_content.append(
            f"🔐 Multi-sig: [cyan]{wallet_info['multi_sign_address']}[/cyan]"
        )

    # Capture output to string
    with console.capture() as capture:
        console.print(table)
        if info_content:
            console.print("\n" + "\n".join(info_content))
    return capture.get()
