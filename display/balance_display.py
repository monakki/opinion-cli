"""Balance display functionality."""

from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table

from .formatters import format_number


class BalanceDisplayer:
    """Balance display functionality."""

    # Constants
    DEFAULT_DECIMALS = 2
    ADDRESS_DISPLAY_LENGTH = 10

    # Token address to symbol mapping
    TOKEN_SYMBOLS = {
        "0x55d398326f99059ff775485246999027b3197955": "USDT",
        # Add more token mappings here as needed
    }

    @staticmethod
    def format_balance_table(
        balances: List[Dict[str, Any]], wallet_info: Dict[str, str]
    ) -> str:
        """Format balance data as a Rich table with additional info."""
        if not balances:
            return "📊 No balances found"

        console = Console()

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
                BalanceDisplayer._format_token_address(
                    balance.get("quote_token", "N/A")
                ),
                format_number(
                    float(balance.get("available_balance", "0")),
                    BalanceDisplayer.DEFAULT_DECIMALS,
                ),
                format_number(
                    float(balance.get("frozen_balance", "0")),
                    BalanceDisplayer.DEFAULT_DECIMALS,
                ),
                format_number(
                    float(balance.get("total_balance", "0")),
                    BalanceDisplayer.DEFAULT_DECIMALS,
                ),
            )

        # Create info panel
        info_content = []
        if wallet_info.get("wallet_address"):
            info_content.append(
                f"📍 Wallet: [cyan]{wallet_info['wallet_address']}[/cyan]"
            )
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

    @staticmethod
    def _format_token_address(address: str) -> str:
        """Format token address to symbol if known, otherwise return shortened address."""
        if address in BalanceDisplayer.TOKEN_SYMBOLS:
            return BalanceDisplayer.TOKEN_SYMBOLS[address]

        # If unknown token, show shortened address (first 6 + last 4 characters)
        if len(address) > BalanceDisplayer.ADDRESS_DISPLAY_LENGTH:
            return f"{address[:6]}...{address[-4:]}"

        return address
