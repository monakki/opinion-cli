#!/usr/bin/env python3
"""Markets command for Opinion CLI."""

import asyncio
import click
import sys
from typing import Optional, Any

from config.constants import (
    MarketStatus,
    MarketType,
    SortBy,
    ErrorMessages,
)
from config.settings import OpinionConfig
from config.validators import InputValidator
from display import MarketDisplayer, JSONDisplayer
from utils.logging import setup_logging
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


def display_markets_table(markets: list) -> None:
    """Display markets in a formatted table."""
    if not markets:
        console.print("📊 No markets found")
        return

    # Use MarketDisplayer to create the table
    table = MarketDisplayer.create_markets_table(markets)
    console.print(table)
    console.print(f"\n📊 Total: {len(markets)} markets")


def display_market_panel(market: Any) -> None:
    """Display detailed market information in a panel."""
    panel = MarketDisplayer.create_market_panel(market)
    console.print(panel)


async def enrich_market_with_prices(market: Any, api_client: Any) -> Any:
    """Enrich market data with latest prices for child markets (parallel fetching)."""
    # Handle child markets (categorical)
    if hasattr(market, "child_markets") and market.child_markets:
        # Create tasks for parallel price and orderbook fetching
        async def fetch_price_and_orderbook_for_child(child):
            """Fetch price and orderbook for a single child market."""
            if hasattr(child, "yes_token_id") and child.yes_token_id:
                try:
                    # Get price
                    price_data = await api_client.get_latest_price(child.yes_token_id)
                    if price_data and "price" in price_data:
                        child.latest_price = price_data["price"]
                    else:
                        child.latest_price = None

                    # Get orderbook
                    orderbook_data = await api_client.get_orderbook(child.yes_token_id)
                    if orderbook_data:
                        child.orderbook = orderbook_data
                    else:
                        child.orderbook = None
                except Exception as e:
                    # If fetch fails, set to None and log the error
                    print(
                        f"Warning: Failed to fetch price/orderbook for child market {child.market_id}: {e}"
                    )
                    child.latest_price = None
                    child.orderbook = None
            else:
                child.latest_price = None
                child.orderbook = None
            return child

        # Create tasks for all child markets
        tasks = [
            fetch_price_and_orderbook_for_child(child) for child in market.child_markets
        ]

        # Execute all tasks in parallel
        await asyncio.gather(*tasks)

    # Handle binary market (get prices for YES and NO tokens)
    elif hasattr(market, "yes_token_id") and hasattr(market, "no_token_id"):
        if market.yes_token_id or market.no_token_id:
            tasks = []

            # Fetch YES token price and orderbook
            if market.yes_token_id:

                async def fetch_yes_data():
                    try:
                        # Get price
                        price_data = await api_client.get_latest_price(
                            market.yes_token_id
                        )
                        if price_data and "price" in price_data:
                            market.yes_latest_price = price_data["price"]
                        else:
                            market.yes_latest_price = None

                        # Get orderbook
                        orderbook_data = await api_client.get_orderbook(
                            market.yes_token_id
                        )
                        if orderbook_data:
                            market.yes_orderbook = orderbook_data
                        else:
                            market.yes_orderbook = None
                    except Exception as e:
                        print(f"Warning: Failed to fetch YES token data: {e}")
                        market.yes_latest_price = None
                        market.yes_orderbook = None

                tasks.append(fetch_yes_data())

            # Fetch NO token price and orderbook
            if market.no_token_id:

                async def fetch_no_data():
                    try:
                        # Get price
                        price_data = await api_client.get_latest_price(
                            market.no_token_id
                        )
                        if price_data and "price" in price_data:
                            market.no_latest_price = price_data["price"]
                        else:
                            market.no_latest_price = None

                        # Get orderbook
                        orderbook_data = await api_client.get_orderbook(
                            market.no_token_id
                        )
                        if orderbook_data:
                            market.no_orderbook = orderbook_data
                        else:
                            market.no_orderbook = None
                    except Exception as e:
                        print(f"Warning: Failed to fetch NO token data: {e}")
                        market.no_latest_price = None
                        market.no_orderbook = None

                tasks.append(fetch_no_data())

            # Execute tasks in parallel
            if tasks:
                await asyncio.gather(*tasks)

    return market


@click.command()
@click.argument("market_id", required=False)
@click.option(
    "--status",
    "-s",
    type=click.Choice(["activated", "resolved"]),
    default="activated",
    help="Market status filter",
)
@click.option(
    "--sort-by",
    type=click.Choice(["1", "2", "3", "4", "5", "6", "7", "8"]),
    default="5",
    help="Sort by: 1=new, 2=ending_soon, 3=volume_desc, 4=volume_asc, 5=volume_24h_desc, 6=volume_24h_asc, 7=volume_7d_desc, 8=volume_7d_asc",
)
@click.option(
    "--limit",
    "-l",
    default=20,
    help="Number of markets to fetch (max 1000)",
)
@click.option("--page", "-p", default=1, help="Page number")
@click.option(
    "--market-type",
    "-t",
    type=click.Choice(["0", "1", "2"]),
    default="2",
    help="Market type: 0=Binary, 1=Categorical, 2=All",
)
@click.option(
    "--json",
    "-j",
    "json_output",
    is_flag=True,
    help="Output in JSON format",
)
def markets(
    market_id: Optional[str],
    status: str,
    sort_by: str,
    limit: int,
    page: int,
    market_type: str,
    json_output: bool,
):
    """Fetch and display markets from Opinion Open API.

    MARKET_ID can be either a numeric ID or an Opinion Trade URL from https://app.opinion.trade.
    If no MARKET_ID is provided, shows a list of markets based on filters.

    Examples:
      # Show specific market by ID
      markets 217

      # Show market from Opinion Trade URL
      markets https://app.opinion.trade/detail?topicId=217
      markets "https://app.opinion.trade/detail?topicId=61&type=multi"

      # List markets with filters
      markets -l 10                         # or --limit 10
      markets -s resolved                   # or --status resolved
      markets -t 0                          # or --market-type 0 (Binary)
      markets --sort-by 1                   # Sort by newest first
      markets --sort-by 3 -l 5              # Top 5 by total volume

      # Pagination and output
      markets -p 2 -l 20                    # or --page 2 --limit 20
      markets -j                            # or --json
      markets 217 --json                    # Specific market as JSON

    Sort options (--sort-by):
      1=new, 2=ending_soon, 3=volume_desc, 4=volume_asc,
      5=volume_24h_desc (default), 6=volume_24h_asc, 7=volume_7d_desc, 8=volume_7d_asc

    Market types (-t/--market-type):
      0=Binary, 1=Categorical, 2=All (default)
    """

    async def fetch_markets():
        try:
            config = OpinionConfig.from_env()

            async with config.create_open_api_client() as client:
                # Check if market_id is provided
                if market_id:
                    actual_market_id = None

                    # Check if it's a URL
                    if InputValidator.is_opinion_trade_url(market_id):
                        actual_market_id = InputValidator.extract_market_id_from_url(
                            market_id
                        )
                        if not actual_market_id:
                            console.print(
                                f"[red]Error: Could not extract market ID from URL: {market_id}[/red]"
                            )
                            sys.exit(1)
                    # Check if it's a direct market ID
                    elif InputValidator.validate_market_id(market_id):
                        actual_market_id = market_id
                    else:
                        # Invalid format
                        console.print(
                            f"[red]Error: Invalid market ID or URL format: {market_id}[/red]"
                        )
                        console.print("[dim]Supported formats:[/dim]")
                        console.print("[dim]  - Market ID: 217[/dim]")
                        console.print(
                            "[dim]  - URL: https://app.opinion.trade/detail?topicId=217[/dim]"
                        )
                        sys.exit(1)

                    # Fetch specific market
                    market = await client.get_market_by_id_parallel(actual_market_id)

                    if not market:
                        console.print(
                            f"[red]{ErrorMessages.MARKET_NOT_FOUND.format(market_id=actual_market_id)}[/red]"
                        )
                        sys.exit(1)

                    # Enrich with prices for better user experience
                    market = await enrich_market_with_prices(market, client)

                    if json_output:
                        market_dict = market.model_dump()
                        convert_datetime_to_string(market_dict)
                        console.print(JSONDisplayer.to_json_string(market_dict))
                    else:
                        display_market_panel(market)

                else:
                    # Fetch multiple markets
                    # Convert string parameters to enums
                    status_enum = MarketStatus(status)
                    sort_enum = SortBy(int(sort_by))
                    market_type_enum = MarketType(int(market_type))

                    markets = await client.get_markets(
                        status=status_enum,
                        sort_by=sort_enum,
                        limit=limit,
                        page=page,
                        market_type=market_type_enum,
                    )

                    if json_output:
                        markets_data = []
                        for market in markets:
                            market_dict = market.model_dump()
                            convert_datetime_to_string(market_dict)
                            markets_data.append(market_dict)
                        console.print(JSONDisplayer.to_json_string(markets_data))
                    else:
                        display_markets_table(markets)

        except ValueError as e:
            console.print(f"[red]❌ Configuration error: {e}[/red]")
            console.print("\nTo use markets command, you need:")
            console.print("- API_KEY (required)")
        except Exception as e:
            console.print(f"[red]❌ Error fetching markets: {e}[/red]")
            sys.exit(1)

    # Run the async function
    asyncio.run(fetch_markets())


if __name__ == "__main__":
    markets()
