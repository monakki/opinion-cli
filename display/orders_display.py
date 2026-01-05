"""Orders display formatting for Opinion CLI."""

from typing import List, Dict, Any
from rich.table import Table
from rich.text import Text
from display.formatters import format_number, format_date
from config.constants import OrdersConstants


class OrdersDisplayer:
    """Formatter for orders data display."""

    @staticmethod
    def format_orders_table(
        orders: List[Dict[str, Any]], pagination_info: Dict[str, Any] = None
    ) -> Table:
        """Create a formatted table for orders data."""
        table = Table(
            title="📋 My Orders", show_header=True, header_style="bold magenta"
        )

        # Add columns
        table.add_column(
            "Order ID", style="cyan", width=OrdersConstants.ORDER_ID_MAX_LENGTH
        )
        table.add_column("Market", style="white", max_width=30)
        table.add_column("Side", style="bold")
        table.add_column("Outcome", style="yellow")
        table.add_column("Price", style="green", justify="right")
        table.add_column("Size", style="blue", justify="right")
        table.add_column("Total", style="cyan", justify="right")
        table.add_column("Filled", style="magenta", justify="right")
        table.add_column("Status", style="bold")
        table.add_column("Created", style="dim")

        for order in orders:
            # Format order ID (truncate if too long)
            order_id = str(order.get("order_id", ""))
            if len(order_id) > OrdersConstants.ORDER_ID_MAX_LENGTH:
                order_id = order_id[: OrdersConstants.ORDER_ID_TRUNCATE_LENGTH] + "..."

            # Format market title with root market title
            market_title = str(order.get("market_title", ""))
            root_market_title = str(order.get("root_market_title", ""))

            # Create market display with root market title if available
            if root_market_title and root_market_title != market_title:
                market_display = f"{market_title} [dim italic not bold]({root_market_title})[/dim italic not bold]"
            else:
                market_display = market_title

            # Format side with color
            side_raw = order.get("side", "")
            if str(side_raw) == OrdersConstants.SIDE_BUY:
                side_text = Text("BUY", style="green")
            elif str(side_raw) == OrdersConstants.SIDE_SELL:
                side_text = Text("SELL", style="red")
            else:
                side_text = Text(str(side_raw), style="white")

            # Format outcome
            outcome = str(order.get("outcome", ""))
            if len(outcome) > OrdersConstants.OUTCOME_MAX_LENGTH:
                outcome = outcome[: OrdersConstants.OUTCOME_TRUNCATE_LENGTH] + "..."

            # Format price
            try:
                price = float(order.get("price", 0))
                price_str = f"${price:.{OrdersConstants.PRICE_PRECISION}f}"
            except (ValueError, TypeError):
                price_str = "N/A"

            # Format sizes
            try:
                size = float(order.get("size", 0))
                size_str = format_number(size, OrdersConstants.SIZE_PRECISION)
            except (ValueError, TypeError):
                size_str = "N/A"
                size = 0

            # Calculate and format total from order_amount
            try:
                total = float(order.get("order_amount", 0))
                total_str = f"${total:.2f}"
            except (ValueError, TypeError):
                total_str = "N/A"

            try:
                filled_size = float(order.get("filled_size", 0))
                filled_str = format_number(filled_size, OrdersConstants.SIZE_PRECISION)
            except (ValueError, TypeError):
                filled_str = "N/A"

            # Format status with color
            status = str(order.get("status_enum", order.get("status", ""))).upper()
            if status in ["OPEN", "PENDING"]:
                status_text = Text(status, style="yellow")
            elif status in ["FILLED", "COMPLETED"]:
                status_text = Text(status, style="green")
            elif status in ["CANCELLED", "CANCELED"]:
                status_text = Text(status, style="red")
            else:
                status_text = Text(status, style="white")

            # Format created date
            created_at = order.get("created_at", "")
            if created_at and str(created_at).isdigit():
                # Convert timestamp to readable date
                from datetime import datetime

                try:
                    dt = datetime.fromtimestamp(int(created_at))
                    created_str = dt.strftime("%Y-%m-%d")
                except (ValueError, OSError):
                    created_str = str(created_at)[
                        : OrdersConstants.DATE_TRUNCATE_LENGTH
                    ]
            else:
                created_str = format_date(created_at)

            table.add_row(
                order_id,
                market_display,
                side_text,
                outcome,
                price_str,
                size_str,
                total_str,
                filled_str,
                status_text,
                created_str,
            )

        # Add pagination info if available
        if pagination_info:
            total = pagination_info.get("total", 0)
            page = pagination_info.get("page", 1)
            limit = pagination_info.get("limit", 10)

            if total > limit:
                total_pages = (total + limit - 1) // limit
                table.caption = f"Page {page} of {total_pages} • Total: {total} orders"
            else:
                table.caption = f"Total: {total} orders"

        return table

    @staticmethod
    def _format_wallet_address(address: str) -> str:
        """Format wallet address for display (show first 6 and last 4 characters)."""
        if len(address) > OrdersConstants.WALLET_ADDRESS_MIN_LENGTH:
            return f"{address[: OrdersConstants.WALLET_ADDRESS_PREFIX_LENGTH]}...{address[-OrdersConstants.WALLET_ADDRESS_SUFFIX_LENGTH :]}"
        return address
