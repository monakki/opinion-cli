"""Market display functionality."""

from typing import Any

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config.constants import DisplayConstants

from .formatters import (
    format_date,
    format_id,
    format_market_type,
    format_price_with_percentage,
    format_status,
    format_volume,
)


class MarketDisplayer:
    """Pure market display functionality."""

    @staticmethod
    def create_markets_table(markets: list[Any], title: str | None = None) -> Table:
        """Create a formatted table for markets list."""
        if not title:
            title = f"Opinion Open API Markets ({len(markets)} found)"

        table = Table(title=title)

        # Add columns
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column(
            "Title", style="white", max_width=DisplayConstants.MAX_TITLE_WIDTH
        )
        table.add_column("Status", style="green")
        table.add_column("Type", style="magenta")
        table.add_column("Volume 24h", style="yellow", justify="right")

        # Add rows
        for market in markets:
            table.add_row(
                format_id(market.id),
                market.title,
                format_status(market.status_enum, market.status),
                format_market_type(market.market_type),
                format_volume(market.volume_24h_float),
            )

        return table

    @staticmethod
    def create_orderbook_table(bids: list[dict], asks: list[dict]) -> Table:
        """Create orderbook table from bids and asks data."""

        # Calculate running totals
        def calculate_totals(orders):
            totals = []
            running_total = 0.0
            for order in orders:
                try:
                    price = float(order["price"])
                    size = float(order["size"])
                    total = price * size
                    running_total += total
                    totals.append((price, size, total, running_total))
                except (ValueError, TypeError, KeyError):
                    continue
            return totals

        bid_totals = calculate_totals(bids)
        ask_totals = calculate_totals(asks)

        # Create Rich table for orderbook
        orderbook_table = Table(
            show_header=True, header_style="dim", box=None, padding=(0, 1)
        )

        # Add columns with proper alignment using constants
        cols = DisplayConstants.ORDERBOOK_COLUMNS
        orderbook_table.add_column("Total (USDT)", justify="left", width=cols["total"])
        orderbook_table.add_column("Size", justify="right", width=cols["size"])
        orderbook_table.add_column("Bids", justify="right", width=cols["price"])
        orderbook_table.add_column("", justify="center", width=cols["separator"])
        orderbook_table.add_column("Asks", justify="left", width=cols["price"])
        orderbook_table.add_column("Size", justify="left", width=cols["size"])
        orderbook_table.add_column("Total (USDT)", justify="right", width=cols["total"])

        # Display top levels
        max_rows = max(len(bid_totals), len(ask_totals))

        for i in range(min(max_rows, DisplayConstants.ORDERBOOK_LEVELS)):
            # Bid side
            if i < len(bid_totals):
                bid_price, bid_size, bid_total, bid_running = bid_totals[i]
                bid_total_str = f"{bid_running:,.0f}"
                bid_size_str = f"{int(bid_size):,}"
                bid_price_str = f"{bid_price * 100:.1f}"
            else:
                bid_total_str = ""
                bid_size_str = ""
                bid_price_str = ""

            # Ask side
            if i < len(ask_totals):
                ask_price, ask_size, ask_total, ask_running = ask_totals[i]
                ask_total_str = f"{ask_running:,.0f}"
                ask_size_str = f"{int(ask_size):,}"
                ask_price_str = f"{ask_price * 100:.1f}"
            else:
                ask_total_str = ""
                ask_size_str = ""
                ask_price_str = ""

            # Add row to table
            orderbook_table.add_row(
                bid_total_str,
                f"[dim]{bid_size_str}[/dim]" if bid_size_str else "",
                f"[green]{bid_price_str}[/green]" if bid_price_str else "",
                "|",
                f"[red]{ask_price_str}[/red]" if ask_price_str else "",
                f"[dim]{ask_size_str}[/dim]" if ask_size_str else "",
                ask_total_str,
            )

        return orderbook_table

    @staticmethod
    def create_market_panel(market: Any) -> Panel:
        """Create a formatted panel for market details."""
        content = Text()

        # Basic market info
        content.append(f"ID: {market.id}\n", style="cyan")
        content.append(f"Title: {market.market_title}\n", style="bold white")
        content.append(
            f"Status: {format_status(market.status_enum, market.status)}\n",
            style="green",
        )
        content.append(
            f"Type: {format_market_type(market.market_type)}\n", style="magenta"
        )
        content.append(
            f"24h Volume: {format_volume(market.volume_24h_float)}\n", style="yellow"
        )
        content.append(
            f"7d Volume: {format_volume(market.volume_7d_float)}\n", style="yellow"
        )
        content.append(
            f"Total Volume: {format_volume(market.total_volume)}\n", style="yellow"
        )

        if market.created_at:
            content.append(f"Created: {format_date(market.created_at)}\n", style="dim")

        if hasattr(market, "cutoff_at") and market.cutoff_at:
            content.append(f"Cutoff: {format_date(market.cutoff_at)}\n", style="dim")

        # Add binary market options
        MarketDisplayer._add_binary_options(content, market)

        # Add orderbook for binary markets
        MarketDisplayer._add_binary_orderbook(content, market)

        # Add child markets for categorical markets
        MarketDisplayer._add_child_markets(content, market)

        # Add description
        if market.description:
            content.append(f"\n\nDescription:\n{market.description}", style="white")

        return Panel(content, title=f"[bold]{market.title}[/bold]", border_style="blue")

    @staticmethod
    def _add_binary_options(content: Text, market: Any) -> None:
        """Add binary market options to content."""
        if (
            hasattr(market, "yes_label")
            and hasattr(market, "no_label")
            and market.yes_label
            and market.no_label
        ):
            content.append("\nBinary Market Options:\n", style="bold blue")

            # YES option
            content.append(f"  {market.yes_label}", style="green")
            if hasattr(market, "yes_latest_price") and market.yes_latest_price:
                price_str = format_price_with_percentage(market.yes_latest_price)
                if price_str:
                    content.append(f" - {price_str}", style="bright_yellow")
            content.append("\n")

            # NO option
            content.append(f"  {market.no_label}", style="red")
            if hasattr(market, "no_latest_price") and market.no_latest_price:
                price_str = format_price_with_percentage(market.no_latest_price)
                if price_str:
                    content.append(f" - {price_str}", style="bright_yellow")
            content.append("\n")

    @staticmethod
    def _add_binary_orderbook(content: Text, market: Any) -> None:
        """Add binary market orderbook to content."""
        if hasattr(market, "yes_orderbook") and hasattr(market, "no_orderbook"):
            if market.yes_orderbook or market.no_orderbook:
                content.append("\nOrderbook (Top 5 levels):\n", style="bold blue")

                # YES Token Orderbook
                if market.yes_orderbook:
                    yes_label = getattr(market, "yes_label", "YES Token")
                    content.append(f"\n{yes_label}:\n", style="bold green")
                    MarketDisplayer._add_orderbook_to_content(
                        content, market.yes_orderbook
                    )

                # NO Token Orderbook
                if market.no_orderbook:
                    no_label = getattr(market, "no_label", "NO Token")
                    content.append(f"\n\n{no_label}:\n", style="bold red")
                    MarketDisplayer._add_orderbook_to_content(
                        content, market.no_orderbook
                    )

    @staticmethod
    def _add_child_markets(content: Text, market: Any) -> None:
        """Add child markets to content."""
        if hasattr(market, "child_markets") and market.child_markets:
            total_children = len(market.child_markets)
            content.append(f"\nChild Markets ({total_children}):\n", style="bold blue")

            for i, child in enumerate(market.child_markets, 1):
                child_volume = 0.0
                if hasattr(child, "volume") and child.volume:
                    try:
                        child_volume = float(child.volume)
                    except (ValueError, TypeError):
                        child_volume = 0.0

                content.append(f"  {i}. ", style="dim")
                content.append(f"[{child.market_id}] ", style="cyan")
                content.append(f"{child.market_title}", style="white")

                # Try to display price from various possible fields
                price_displayed = False

                # Check for latest_price
                if hasattr(child, "latest_price") and child.latest_price:
                    price_str = format_price_with_percentage(child.latest_price)
                    if price_str:
                        content.append(f" - {price_str}", style="bright_yellow")
                        price_displayed = True

                # Check for price field
                if not price_displayed and hasattr(child, "price") and child.price:
                    price_str = format_price_with_percentage(child.price)
                    if price_str:
                        content.append(f" - {price_str}", style="bright_yellow")
                        price_displayed = True

                # Check for yes_latest_price (for binary markets)
                if (
                    not price_displayed
                    and hasattr(child, "yes_latest_price")
                    and child.yes_latest_price
                ):
                    price_str = format_price_with_percentage(child.yes_latest_price)
                    if price_str:
                        content.append(f" - YES: {price_str}", style="bright_yellow")
                        price_displayed = True

                content.append(f" ({format_volume(child_volume)})", style="yellow")

                if hasattr(child, "status_enum") and child.status_enum:
                    content.append(f" - {child.status_enum}", style="green")
                content.append("\n")

            # Display orderbooks for child markets if available
            MarketDisplayer._add_child_orderbooks(content, market.child_markets)

    @staticmethod
    def _add_child_orderbooks(content: Text, child_markets: list) -> None:
        """Add child market orderbooks to content."""
        content.append("\nOrderbooks (Top 5 levels each):\n", style="bold blue")

        for i, child in enumerate(child_markets, 1):
            if hasattr(child, "orderbook") and child.orderbook:
                child_label = getattr(child, "market_title", f"Option {i}")

                # Add extra spacing between orderbooks (except for the first one)
                if i > 1:
                    content.append(f"\n\n{child_label}:\n", style="bold cyan")
                else:
                    content.append(f"\n{child_label}:\n", style="bold cyan")

                MarketDisplayer._add_orderbook_to_content(content, child.orderbook)

    @staticmethod
    def _add_orderbook_to_content(content: Text, orderbook_data: dict) -> None:
        """Add orderbook table to content."""
        # Get bids and asks
        bids = []
        asks = []

        if "bids" in orderbook_data:
            bids_raw = orderbook_data["bids"]
            bids = sorted(
                bids_raw, key=lambda x: float(x.get("price", 0)), reverse=True
            )[: DisplayConstants.ORDERBOOK_LEVELS]

        if "asks" in orderbook_data:
            asks_raw = orderbook_data["asks"]
            asks = sorted(
                asks_raw, key=lambda x: float(x.get("price", 0)), reverse=False
            )[: DisplayConstants.ORDERBOOK_LEVELS]

        # Create orderbook table
        orderbook_table = MarketDisplayer.create_orderbook_table(bids, asks)

        # Convert table to renderable and add to content
        temp_console = RichConsole(width=DisplayConstants.TABLE_WIDTH, file=None)
        with temp_console.capture() as capture:
            temp_console.print(orderbook_table)

        # Add the captured table output as plain text to preserve formatting
        table_text = Text.from_ansi(capture.get())
        content.append("\n")
        content.append(table_text)
