"""Configuration display functionality."""

from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel


class ConfigDisplayer:
    """Configuration display functionality."""

    @staticmethod
    def format_config_info(config_info: Dict[str, Any]) -> str:
        """Format configuration information for display."""
        console = Console()

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
                f"   ├─ Rate Limit: [cyan]{config_info['rate_limit']} req/s[/cyan]"
            )
            content.append(f"   └─ Timeout: [cyan]{config_info['timeout']}s[/cyan]")
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
                f"   ├─ Rate Limit: [cyan]{config_info['rate_limit']} req/s[/cyan]"
            )
            content.append(f"   └─ Timeout: [cyan]{config_info['timeout']}s[/cyan]")

        content.append("")
        content.append("🔐 Credentials Status:")

        # Credentials status using helper function
        icon, color, text = ConfigDisplayer._get_status_display(
            config_info["api_key_set"]
        )
        content.append(f"  {icon} API Key: [{color}]{text}[/{color}]")

        icon, color, text = ConfigDisplayer._get_status_display(
            config_info["rpc_url_set"], "Set", "Not set (read-only mode)"
        )
        content.append(f"  {icon} RPC URL: [{color}]{text}[/{color}]")

        icon, color, text = ConfigDisplayer._get_status_display(
            config_info["private_key_set"], "Set", "Not set (read-only mode)"
        )
        content.append(f"  {icon} Private Key: [{color}]{text}[/{color}]")

        # Create panel
        panel = Panel(
            "\n".join(content),
            title="📋 Opinion CLI Configuration",
            border_style="blue",
        )

        # Capture output to string
        with console.capture() as capture:
            console.print(panel)
        return capture.get()

    @staticmethod
    def format_connection_test(result: Dict[str, Any]) -> str:
        """Format connection test result for display."""
        console = Console()

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
                "\n".join(content),
                title="❌ Connection Test: FAILED",
                border_style="red",
            )

        with console.capture() as capture:
            console.print(panel)
        return capture.get()

    @staticmethod
    def _get_status_display(
        condition: bool, true_text: str = "Set", false_text: str = "Not set"
    ) -> tuple[str, str, str]:
        """Get status icon, color, and text based on condition."""
        # Status indicators
        STATUS_ICONS = {"success": "✅", "warning": "⚠️", "error": "❌", "info": "📊"}
        STATUS_COLORS = {
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "info": "cyan",
        }

        if condition:
            return STATUS_ICONS["success"], STATUS_COLORS["success"], true_text
        else:
            return STATUS_ICONS["warning"], STATUS_COLORS["warning"], false_text
