"""Trades display functionality."""

from typing import Dict, Any, List
from rich.table import Table

from .formatters import format_number, format_currency


class TradesDisplayer:
    """Trades display functionality."""

    # Constants
    DEFAULT_DECIMALS = 4
    ADDRESS_DISPLAY_LENGTH = 10

    @staticmethod
    def create_trades_table(
        trades: List[Dict[str, Any]],
        wallet_address: str,
        pagination_info: Dict[str, Any] = None,
    ) -> Table:
        """Create a formatted table for trades data."""
        # Create title with pagination info
        title = f"📈 User Trades ({len(trades)} found)"
        if pagination_info:
            page = pagination_info.get("page", 1)
            total = pagination_info.get("total_count", len(trades))
            title = f"📈 User Trades (Page {page}, {len(trades)}/{total} total)"

        # Create Rich table
        table = Table(show_header=True, header_style="bold magenta", title=title)

        # Add columns
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Market", style="white", max_width=30)
        table.add_column("Side", style="blue")
        table.add_column("Outcome", style="magenta")
        table.add_column("Price", style="yellow", justify="right")
        table.add_column("Shares", style="yellow", justify="right")
        table.add_column("Amount", style="green", justify="right")
        table.add_column("Status", style="dim")

        # Add rows with formatted numbers
        for trade in trades:
            # Format market title with root market title
            market_display = trade.get("market_title", "N/A")
            root_market_title = trade.get("root_market_title", "")

            # Add root market title if it exists and is different from market title
            if root_market_title and root_market_title != market_display:
                market_display = f"{market_display} [dim italic not bold]({root_market_title})[/dim italic not bold]"

            table.add_row(
                str(trade.get("market_id", "N/A")),
                market_display,
                trade.get("side", "N/A"),
                trade.get("outcome", "N/A"),
                f"${format_number(float(trade.get('price', '0')), TradesDisplayer.DEFAULT_DECIMALS)}",
                format_number(
                    float(trade.get("shares", "0")),
                    TradesDisplayer.DEFAULT_DECIMALS,
                ),
                format_currency(float(trade.get("amount", "0"))),
                trade.get("status", "N/A"),
            )

        return table

    @staticmethod
    def _format_wallet_address(address: str) -> str:
        """Format wallet address to shortened version."""
        if len(address) > TradesDisplayer.ADDRESS_DISPLAY_LENGTH:
            return f"{address[:6]}...{address[-4:]}"
        return address
