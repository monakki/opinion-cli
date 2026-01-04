"""Trades commands for Opinion CLI."""

import asyncio
import click
import os
from typing import Dict, Any, List
from display import JSONDisplayer, TradesDisplayer
from config.settings import OpinionConfig
from clients.opinion_api_client import OpinionOpenAPIError
from clients.models import Trade
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


def display_trades_table(
    trades: List[Trade], wallet_address: str, pagination_info: Dict[str, Any] = None
) -> None:
    """Display trades in a formatted table."""
    if not trades:
        console.print(f"📊 No trades found for wallet {wallet_address}")
        return

    # Convert Trade objects to dictionaries for display
    trades_data = []

    for trade in trades:
        trades_data.append(
            {
                "tx_hash": trade.tx_hash,
                "market_id": trade.market_id,
                "market_title": trade.market_title,
                "root_market_title": trade.root_market_title,
                "side": trade.side,
                "outcome": trade.outcome,
                "outcome_side": trade.outcome_side_enum,
                "price": trade.price,
                "shares": trade.shares,
                "amount": trade.amount,
                "fee": trade.fee,
                "profit": trade.profit,
                "status": trade.status_enum,
                "created_at": trade.created_at,
            }
        )

    # Create the table using TradesDisplayer
    table = TradesDisplayer.create_trades_table(
        trades_data, wallet_address, pagination_info
    )
    console.print(table)

    # Print wallet info
    wallet_short = TradesDisplayer._format_wallet_address(wallet_address)
    console.print(f"\n📍 Wallet: [cyan]{wallet_short}[/cyan]")

    if pagination_info:
        page = pagination_info.get("page", 1)
        limit = pagination_info.get("limit", 10)
        total = pagination_info.get("total_count", 0)
        if total > limit:
            console.print(f"📄 Page {page} of {(total + limit - 1) // limit}")

    console.print(f"\n📊 Total: {len(trades)} trades")


@click.command()
@click.argument("wallet_address", required=False)
@click.option("--page", "-p", default=1, help="Page number")
@click.option("--limit", "-l", default=20, help="Number of trades per page (max 1000)")
@click.option("--market-id", "-m", type=int, help="Filter by market ID")
@click.option("--chain-id", "-c", help="Filter by chain ID")
@click.option("--json", "-j", is_flag=True, help="Output trades data in JSON format")
def trades(
    wallet_address: str,
    page: int,
    limit: int,
    market_id: int,
    chain_id: str,
    json: bool,
):
    """Show user's trade history for a specific wallet address.

    Wallet address can be provided as argument or via WALLET_ADDRESS environment variable.
    Only returns filled (successful) trades. Results are sorted by creation time (descending).

    Examples:
      trades 0x1234...abcd           # Show trades for specific wallet
      trades --limit 20              # Show 20 trades from env wallet
      trades --market-id 217         # Filter by market ID
      trades --json                  # Output in JSON format

    Requires: API_KEY environment variable.
    """

    async def fetch_trades():
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
                console.print("- Argument: uv run trades 0x1234...abcd")
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
                # Fetch trades using the API client with automatic pagination
                all_trades = []
                current_page = page
                remaining_limit = limit
                
                while remaining_limit > 0:
                    # Calculate how many records to fetch on this page (max 100 per API call)
                    page_limit = min(remaining_limit, 100)
                    
                    trades_batch = await client.get_user_trades(
                        wallet_address=target_wallet,
                        page=current_page,
                        limit=page_limit,
                        market_id=market_id,
                        chain_id=chain_id,
                    )
                    
                    if not trades_batch:
                        # No more trades available
                        break
                    
                    all_trades.extend(trades_batch)
                    
                    # If we got fewer trades than requested, we've reached the end
                    if len(trades_batch) < page_limit:
                        break
                    
                    remaining_limit -= len(trades_batch)
                    current_page += 1
                
                trades_list = all_trades

                if json:
                    # Convert trades to dictionaries for JSON output
                    trades_data = []

                    for trade in trades_list:
                        trade_dict = trade.model_dump()
                        trade_dict = convert_datetime_to_string(trade_dict)
                        trades_data.append(trade_dict)

                    output_data = {
                        "trades": trades_data,
                        "total_count": len(trades_data),
                        "page": page,
                        "limit": limit,
                        "wallet_address": target_wallet,
                    }
                    console.print(JSONDisplayer.to_json_string(output_data))
                    return

                # Display table format
                pagination_info = {
                    "page": page,
                    "limit": limit,
                    "total_count": len(trades_list),
                }

                display_trades_table(trades_list, target_wallet, pagination_info)

        except OpinionOpenAPIError as e:
            console.print(f"❌ API Error: {e.message}", style="red")
            if e.status_code:
                console.print(f"Status Code: {e.status_code}")
        except ValueError as e:
            console.print(f"❌ Configuration error: {e}", style="red")
            console.print("\n💡 Trades viewing requires:")
            console.print("   • API_KEY - Your Opinion API key")
            console.print("\n📖 See README.md for setup instructions")
        except Exception as e:
            console.print(f"❌ Error getting trades: {e}", style="red")
            console.print("\nNote: Trade retrieval requires valid API_KEY.")
            console.print("Check your API_KEY configuration.")

    # Run the async function
    try:
        asyncio.run(fetch_trades())
    except KeyboardInterrupt:
        console.print("\n⚠️ Operation cancelled by user", style="yellow")
