"""Orders commands for Opinion CLI."""

import click
from typing import Dict, Any
from commands.base import BaseCommand
from display import JSONDisplayer, OrdersDisplayer
from rich.console import Console
from config.constants import OrdersConstants

console = Console()


class OrdersParser:
    """Parser for orders response data."""

    @staticmethod
    def parse_orders_response(response) -> Dict[str, Any]:
        """Parse orders response into a standardized format."""
        parsed = {
            "errno": getattr(response, "errno", None),
            "errmsg": getattr(response, "errmsg", None),
            "result": None,
        }

        if hasattr(response, "result") and response.result:
            result = response.result
            if hasattr(result, "list") and result.list:
                orders = []
                for order in result.list:
                    # Get order shares and filled shares
                    order_shares = getattr(order, "order_shares", "0")
                    filled_shares = getattr(order, "filled_shares", "0")

                    # Calculate remaining shares
                    try:
                        remaining_shares = str(
                            float(order_shares) - float(filled_shares)
                        )
                    except (ValueError, TypeError):
                        remaining_shares = "0"

                    orders.append(
                        {
                            "order_id": getattr(order, "order_id", ""),
                            "market_id": getattr(order, "market_id", ""),
                            "market_title": getattr(order, "market_title", ""),
                            "root_market_title": getattr(
                                order, "root_market_title", ""
                            ),
                            "side": getattr(order, "side", ""),
                            "outcome": getattr(order, "outcome", ""),
                            "price": getattr(order, "price", "0"),
                            "order_amount": getattr(order, "order_amount", "0"),
                            "size": order_shares,
                            "filled_size": filled_shares,
                            "remaining_size": remaining_shares,
                            "status": getattr(order, "status", ""),
                            "status_enum": getattr(order, "status_enum", ""),
                            "created_at": getattr(order, "created_at", ""),
                            "updated_at": getattr(order, "updated_at", ""),
                            "quote_token": getattr(order, "quote_token", ""),
                        }
                    )

                parsed["result"] = {
                    "orders": orders,
                    "total": getattr(result, "total", len(orders)),
                    "page": getattr(result, "page", 1),
                    "limit": getattr(result, "limit", 10),
                }

        return parsed

    @staticmethod
    def parse_orders_response_raw(response) -> Dict[str, Any]:
        """Parse orders response keeping all original fields."""
        parsed = {
            "errno": getattr(response, "errno", None),
            "errmsg": getattr(response, "errmsg", None),
            "result": None,
        }

        if hasattr(response, "result") and response.result:
            result = response.result
            if hasattr(result, "list") and result.list:
                orders = []
                for order in result.list:
                    # Convert order object to dict with all fields
                    order_dict = {}
                    for attr in dir(order):
                        if not attr.startswith("_") and not callable(
                            getattr(order, attr)
                        ):
                            try:
                                value = getattr(order, attr)
                                # Skip complex objects and methods
                                if (
                                    isinstance(value, (str, int, float, bool, list))
                                    or value is None
                                ):
                                    order_dict[attr] = value
                            except Exception:
                                continue
                    orders.append(order_dict)

                parsed["result"] = {
                    "orders": orders,
                    "total": getattr(result, "total", len(orders)),
                    "page": getattr(result, "page", 1),
                    "limit": getattr(result, "limit", 10),
                }

        return parsed
        """Parse orders response into a standardized format."""
        parsed = {
            "errno": getattr(response, "errno", None),
            "errmsg": getattr(response, "errmsg", None),
            "result": None,
        }

        if hasattr(response, "result") and response.result:
            result = response.result
            if hasattr(result, "list") and result.list:
                orders = []
                for order in result.list:
                    # Get order shares and filled shares
                    order_shares = getattr(order, "order_shares", "0")
                    filled_shares = getattr(order, "filled_shares", "0")

                    # Calculate remaining shares
                    try:
                        remaining_shares = str(
                            float(order_shares) - float(filled_shares)
                        )
                    except (ValueError, TypeError):
                        remaining_shares = "0"

                    orders.append(
                        {
                            "order_id": getattr(order, "order_id", ""),
                            "market_id": getattr(order, "market_id", ""),
                            "market_title": getattr(order, "market_title", ""),
                            "side": getattr(order, "side", ""),
                            "outcome": getattr(order, "outcome", ""),
                            "price": getattr(order, "price", "0"),
                            "size": order_shares,
                            "filled_size": filled_shares,
                            "remaining_size": remaining_shares,
                            "status": getattr(order, "status", ""),
                            "status_enum": getattr(order, "status_enum", ""),
                            "created_at": getattr(order, "created_at", ""),
                            "updated_at": getattr(order, "updated_at", ""),
                            "quote_token": getattr(order, "quote_token", ""),
                        }
                    )

                parsed["result"] = {
                    "orders": orders,
                    "total": getattr(result, "total", len(orders)),
                    "page": getattr(result, "page", 1),
                    "limit": getattr(result, "limit", 10),
                }

        return parsed


@click.command()
@click.option(
    "--market-id",
    "-m",
    type=int,
    default=0,
    help="Filter by market ID (0 = all markets)",
)
@click.option(
    "--status",
    "-s",
    default="open",
    help="Filter by status (open, filled, cancelled, or 'all' for all orders)",
)
@click.option(
    "--limit",
    "-l",
    default=OrdersConstants.DEFAULT_OPEN_ORDERS_LIMIT,
    help="Maximum number of orders to show (auto-paginated)",
)
@click.option(
    "--page", "-p", default=1, help="Page number (only used with --no-auto-paginate)"
)
@click.option(
    "--no-auto-paginate",
    is_flag=True,
    help="Disable automatic pagination (use manual pagination)",
)
@click.option("--json", "-j", is_flag=True, help="Output orders data in JSON format")
def orders(
    market_id: int,
    status: str,
    limit: int,
    page: int,
    no_auto_paginate: bool,
    json: bool,
):
    """Show user's orders with optional filters.

    By default uses automatic pagination to show all orders up to the limit.
    Use --no-auto-paginate for manual pagination.

    Examples:
      orders                           # Show ALL open orders (auto-paginated, up to 1000)
      orders --status all              # Show all orders (auto-paginated, up to 20)
      orders --status filled           # Show filled orders (auto-paginated, up to 20)
      orders --market-id 217           # Show ALL open orders for specific market
      orders --limit 50                # Show max 50 orders (auto-paginated)
      orders --no-auto-paginate        # Use manual pagination (10 per page)
      orders --json                    # Output in JSON format

    Requires: API_KEY and PRIVATE_KEY environment variables.
    """
    # Validate required credentials first
    if not BaseCommand.validate_balance_requirements():
        return

    try:
        # Convert status to numeric if provided
        status_numeric = ""
        if status and status.lower() != "all":
            status_lower = status.lower()
            if status_lower in OrdersConstants.STATUS_MAPPING:
                status_numeric = OrdersConstants.STATUS_MAPPING[status_lower]
            else:
                console.print(f"❌ Invalid status: {status}", style="red")
                console.print(
                    "Valid statuses: open, pending, filled, completed, cancelled, canceled, all"
                )
                return

        # Always use auto-pagination unless explicitly disabled
        use_auto_paginate = not no_auto_paginate

        # Adjust default limit based on status
        if limit == OrdersConstants.DEFAULT_OPEN_ORDERS_LIMIT:  # Default value
            if status and status.lower() == "all":
                # For all orders, use smaller default limit
                limit = OrdersConstants.DEFAULT_OTHER_ORDERS_LIMIT
            elif status and status.lower() in [
                "filled",
                "completed",
                "cancelled",
                "canceled",
            ]:
                # For specific statuses, use moderate limit
                limit = OrdersConstants.DEFAULT_OTHER_ORDERS_LIMIT
            else:
                # For open orders, keep high limit
                limit = OrdersConstants.DEFAULT_OPEN_ORDERS_LIMIT

        client = BaseCommand.get_client()
        response = client.get_my_orders(
            market_id=market_id,
            status=status_numeric,
            limit=limit,
            page=page,
            auto_paginate=use_auto_paginate,
        )

        if json:
            # For JSON output, use raw parser to get all fields
            raw_data = OrdersParser.parse_orders_response_raw(response)
            click.echo(JSONDisplayer.to_json_string(raw_data))
            return

        # For table output, use regular parser
        parsed_data = OrdersParser.parse_orders_response(response)

        # Handle table format
        if parsed_data["errno"] == 0:
            if parsed_data["result"] and parsed_data["result"]["orders"]:
                orders = parsed_data["result"]["orders"]
                pagination_info = {
                    "total": parsed_data["result"]["total"],
                    "page": parsed_data["result"]["page"],
                    "limit": parsed_data["result"]["limit"],
                }

                formatted_output = OrdersDisplayer.format_orders_table(
                    orders, pagination_info
                )
                console.print(formatted_output)
            else:
                click.echo("📊 No orders found")
                if market_id > 0:
                    click.echo(f"   Market ID: {market_id}")
                if status:
                    click.echo(f"   Status: {status}")
        else:
            error_msg = parsed_data["errmsg"] or "Unknown error"
            errno = parsed_data["errno"] or "Unknown"
            click.echo(
                f"❌ Failed to get orders (errno: {errno}): {error_msg}", err=True
            )

    except ValueError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        click.echo("\nTo view orders, you need:")
        click.echo("- API_KEY (required)")
        click.echo("- PRIVATE_KEY (required)")
    except Exception as e:
        click.echo(f"❌ Error getting orders: {e}", err=True)
        click.echo("\nNote: Orders retrieval requires valid credentials.")
        click.echo("Check your API_KEY and PRIVATE_KEY.")
