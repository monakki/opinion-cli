"""Positions display functionality."""

from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table

from .formatters import format_number, format_currency


class PositionsDisplayer:
    """Positions display functionality."""

    # Constants
    DEFAULT_DECIMALS = 2
    ADDRESS_DISPLAY_LENGTH = 10

    @staticmethod
    def create_positions_table(
        positions: List[Dict[str, Any]], 
        wallet_address: str,
        pagination_info: Dict[str, Any] = None
    ) -> Table:
        """Create a formatted table for positions data."""
        # Create title with pagination info
        title = f"💼 User Positions ({len(positions)} found)"
        if pagination_info:
            page = pagination_info.get("page", 1)
            limit = pagination_info.get("limit", 10)
            total = pagination_info.get("total_count", len(positions))
            title = f"💼 User Positions (Page {page}, {len(positions)}/{total} total)"

        # Create Rich table
        table = Table(
            show_header=True, 
            header_style="bold magenta", 
            title=title
        )

        # Add columns
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Market", style="white", max_width=30)
        table.add_column("Outcome", style="magenta")
        table.add_column("Shares", style="yellow", justify="right")
        table.add_column("PnL", justify="right")  # Combined PnL column
        table.add_column("Value", style="yellow", justify="right")
        table.add_column("Status", style="dim")

        # Add rows with formatted numbers
        for position in positions:
            # Format market title with root market title
            market_display = position.get("market_title", "N/A")
            root_market_title = position.get("root_market_title", "")
            
            # Add root market title if it exists and is different from market title
            if root_market_title and root_market_title != market_display:
                market_display = f"{market_display} [dim italic not bold]({root_market_title})[/dim italic not bold]"
            
            # Format PnL with color
            pnl_value = float(position.get("unrealized_pnl", "0"))
            pnl_percent = float(position.get("unrealized_pnl_percent", "0"))
            
            if pnl_value > 0:
                pnl_color = "green"
                pnl_prefix = "+"
            elif pnl_value < 0:
                pnl_color = "red"
                pnl_prefix = ""
            else:
                pnl_color = "dim"
                pnl_prefix = ""

            # Combine PnL value and percentage in one column
            pnl_combined = f"[{pnl_color}]{pnl_prefix}{format_currency(pnl_value)} ({pnl_prefix}{pnl_percent:.1f}%)[/{pnl_color}]"

            table.add_row(
                str(position.get("market_id", "N/A")),
                market_display,
                position.get("outcome", "N/A"),
                format_number(
                    float(position.get("shares_owned", "0")),
                    PositionsDisplayer.DEFAULT_DECIMALS,
                ),
                pnl_combined,
                format_currency(float(position.get("current_value", "0"))),
                position.get("claim_status", "N/A"),
            )

        return table

    @staticmethod
    def _format_wallet_address(address: str) -> str:
        """Format wallet address to shortened version."""
        if len(address) > PositionsDisplayer.ADDRESS_DISPLAY_LENGTH:
            return f"{address[:6]}...{address[-4:]}"
        return address