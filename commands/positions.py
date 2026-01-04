"""Positions commands for Opinion CLI."""

import asyncio
import click
import os
from typing import Dict, Any, List
from display import JSONDisplayer, PositionsDisplayer
from config.settings import OpinionConfig
from clients.opinion_api_client import OpinionOpenAPIError
from clients.models import Position
from utils.logging import setup_logging
from utils.wallet import get_wallet_address
from rich.console import Console

# Setup logging based on environment variables
setup_logging()

console = Console()


def convert_datetime_to_string(data_dict: dict) -> dict:
    """Convert datetime objects to strings in dictionary."""
    for key, value in data_dict.items():
        if hasattr(value, "isoformat"):  # datetime object
            data_dict[key] = value.isoformat()
    return data_dict


def display_positions_table(
    positions: List[Position],
    wallet_address: str,
    pagination_info: Dict[str, Any] = None,
) -> None:
    """Display positions in a formatted table."""
    if not positions:
        console.print(f"📊 No positions found for wallet {wallet_address}")
        return

    # Convert Position objects to dictionaries for display and calculate totals
    positions_data = []
    total_current_value = 0.0
    total_unrealized_pnl = 0.0

    for position in positions:
        current_value = float(position.current_value_in_quote_token)
        unrealized_pnl = float(position.unrealized_pnl)

        total_current_value += current_value
        total_unrealized_pnl += unrealized_pnl

        positions_data.append(
            {
                "market_id": position.market_id,
                "market_title": position.market_title,
                "root_market_title": position.root_market_title,
                "outcome": position.outcome,
                "outcome_side": position.outcome_side_enum,
                "shares_owned": position.shares_owned,
                "unrealized_pnl": position.unrealized_pnl,
                "unrealized_pnl_percent": position.unrealized_pnl_percent,
                "current_value": position.current_value_in_quote_token,
                "claim_status": position.claim_status_enum,
            }
        )

    # Create the table using PositionsDisplayer
    table = PositionsDisplayer.create_positions_table(
        positions_data, wallet_address, pagination_info
    )
    console.print(table)

    # Print wallet info and totals
    wallet_short = PositionsDisplayer._format_wallet_address(wallet_address)
    console.print(f"\n📍 Wallet: [cyan]{wallet_short}[/cyan]")

    # Format total PnL with color
    if total_unrealized_pnl > 0:
        pnl_color = "green"
        pnl_prefix = "+"
    elif total_unrealized_pnl < 0:
        pnl_color = "red"
        pnl_prefix = ""
    else:
        pnl_color = "white"
        pnl_prefix = ""

    console.print(f"💰 Total Value: [yellow]${total_current_value:.2f}[/yellow]")
    console.print(
        f"📈 Total PnL: [{pnl_color}]{pnl_prefix}${total_unrealized_pnl:.2f}[/{pnl_color}]"
    )

    if pagination_info:
        page = pagination_info.get("page", 1)
        limit = pagination_info.get("limit", 10)
        total = pagination_info.get("total_count", 0)
        if total > limit:
            console.print(f"📄 Page {page} of {(total + limit - 1) // limit}")

    console.print(f"\n📊 Total: {len(positions)} positions")


@click.command()
@click.argument("wallet_address", required=False)
@click.option("--page", "-p", default=1, help="Page number")
@click.option(
    "--limit", "-l", default=20, help="Number of positions per page (max 1000)"
)
@click.option("--market-id", "-m", type=int, help="Filter by market ID")
@click.option("--chain-id", "-c", help="Filter by chain ID")
@click.option("--json", "-j", is_flag=True, help="Output positions data in JSON format")
def positions(
    wallet_address: str,
    page: int,
    limit: int,
    market_id: int,
    chain_id: str,
    json: bool,
):
    """Show user's positions (portfolio) for a specific wallet address.

    Wallet address can be provided as argument or via WALLET_ADDRESS environment variable.

    Examples:
      positions 0x1234...abcd           # Show positions for specific wallet
      positions --limit 20              # Show 20 positions from env wallet
      positions --market-id 217         # Filter by market ID
      positions --json                  # Output in JSON format

    Requires: API_KEY environment variable.
    """

    async def fetch_positions():
        try:
            # Get wallet address from multiple sources
            private_key = os.getenv("PRIVATE_KEY")
            wallet_address_env = os.getenv("WALLET_ADDRESS")

            target_wallet = get_wallet_address(
                wallet_address_arg=wallet_address,
                private_key_env=private_key,
                wallet_address_env=wallet_address_env,
            )

            if not target_wallet:
                console.print("❌ Wallet address is required", style="red")
                console.print("\nProvide wallet address via:")
                console.print("- Argument: uv run positions 0x1234...abcd")
                console.print("- Environment: WALLET_ADDRESS=0x1234...abcd")
                console.print(
                    "- Private key: PRIVATE_KEY=0x1234...abcd (address will be derived)"
                )
                return

            # Validate limit
            if limit < 1 or limit > 1000:
                console.print("❌ Limit must be between 1 and 1000", style="red")
                return

            # Validate page
            if page < 1:
                console.print("❌ Page must be >= 1", style="red")
                return

            config = OpinionConfig.from_env()

            async with config.create_open_api_client() as client:
                # Fetch positions using the API client
                positions_list = await client.get_user_positions(
                    wallet_address=target_wallet,
                    page=page,
                    limit=limit,
                    market_id=market_id,
                    chain_id=chain_id,
                )

                if json:
                    # Convert positions to dictionaries for JSON output and calculate totals
                    positions_data = []
                    total_current_value = 0.0
                    total_unrealized_pnl = 0.0

                    for position in positions_list:
                        position_dict = position.model_dump()
                        position_dict = convert_datetime_to_string(position_dict)
                        positions_data.append(position_dict)

                        # Add to totals
                        total_current_value += float(
                            position.current_value_in_quote_token
                        )
                        total_unrealized_pnl += float(position.unrealized_pnl)

                    output_data = {
                        "positions": positions_data,
                        "total_count": len(positions_data),
                        "page": page,
                        "limit": limit,
                        "wallet_address": target_wallet,
                        "summary": {
                            "total_current_value": round(total_current_value, 2),
                            "total_unrealized_pnl": round(total_unrealized_pnl, 2),
                        },
                    }
                    console.print(JSONDisplayer.to_json_string(output_data))
                    return

                # Display table format
                pagination_info = {
                    "page": page,
                    "limit": limit,
                    "total_count": len(positions_list),
                }

                display_positions_table(positions_list, target_wallet, pagination_info)

        except OpinionOpenAPIError as e:
            console.print(f"❌ API Error: {e.message}", style="red")
            if e.status_code:
                console.print(f"Status Code: {e.status_code}")
        except ValueError as e:
            console.print(f"❌ Configuration error: {e}", style="red")
            console.print("\n💡 Positions viewing requires:")
            console.print("   • API_KEY - Your Opinion API key")
            console.print("\n📖 See README.md for setup instructions")
        except Exception as e:
            console.print(f"❌ Error getting positions: {e}", style="red")
            console.print("\nNote: Position retrieval requires valid API_KEY.")
            console.print("Check your API_KEY configuration.")

    # Run the async function
    try:
        asyncio.run(fetch_positions())
    except KeyboardInterrupt:
        console.print("\n⚠️ Operation cancelled by user", style="yellow")
