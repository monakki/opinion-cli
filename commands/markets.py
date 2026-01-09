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


def determine_query_type(query: str) -> tuple[str, str | None]:
    """Determine the type of query and return (type, processed_value).

    Returns:
        - ("market_id", market_id) for numeric IDs
        - ("url", market_id) for Opinion Trade URLs
        - ("search", search_query) for text search
        - ("invalid", None) for invalid input
    """
    if not query or not query.strip():
        return ("invalid", None)

    query = query.strip()

    # Check if it's a URL
    if InputValidator.is_opinion_trade_url(query):
        market_id = InputValidator.extract_market_id_from_url(query)
        if market_id:
            return ("url", market_id)
        else:
            return ("invalid", None)

    # Check if it's a numeric market ID
    if InputValidator.validate_market_id(query):
        return ("market_id", query)

    # Otherwise, treat as search query
    return ("search", query)


def search_markets_by_title(markets: list[Any], search_query: str) -> list[Any]:
    """Search markets by title (case-insensitive)."""
    if not search_query:
        return markets

    search_query_lower = search_query.lower()
    filtered_markets = []

    for market in markets:
        # Search in main market title
        if search_query_lower in market.title.lower():
            filtered_markets.append(market)
            continue

        # Search in child markets titles for categorical markets
        if hasattr(market, "child_markets") and market.child_markets:
            found_in_child = False
            for child in market.child_markets:
                if (
                    hasattr(child, "market_title")
                    and search_query_lower in child.market_title.lower()
                ):
                    found_in_child = True
                    break
            if found_in_child:
                filtered_markets.append(market)
                continue

    return filtered_markets


async def get_all_markets_for_search(
    client, status_enum, sort_enum, market_type_enum, limit=0
):
    """Get all markets for search functionality."""
    from config.constants import APIConstants

    all_markets = []
    current_page = 1

    # If limit is 0, we search through all available markets
    # If limit is specified, we respect it
    remaining_limit = limit if limit > 0 else float("inf")

    while remaining_limit > 0:
        # Calculate how many items to request for this page (max per API call is still 20)
        if remaining_limit == float("inf"):
            page_limit = APIConstants.MAX_MARKETS_PER_REQUEST
        else:
            page_limit = min(int(remaining_limit), APIConstants.MAX_MARKETS_PER_REQUEST)

        params = {
            "limit": page_limit,
            "page": current_page,
        }

        if status_enum:
            params["status"] = status_enum.value

        if sort_enum:
            params["sortBy"] = sort_enum.value

        if market_type_enum is not None:
            params["marketType"] = market_type_enum.value

        try:
            data = await client._make_request("GET", "/openapi/market", params=params)
            markets_data = client._extract_markets_from_response(data)
            page_markets = client._parse_market_data(markets_data)

            if not page_markets:
                break

            all_markets.extend(page_markets)

            if remaining_limit != float("inf"):
                remaining_limit -= len(page_markets)

            # If we got fewer markets than requested, we've reached the end
            if len(page_markets) < page_limit:
                break

            current_page += 1

            # Add a small delay between requests to be respectful to the API
            await asyncio.sleep(APIConstants.PAGINATION_DELAY)

        except Exception:
            break

    return all_markets


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


def display_search_results_table(
    markets: list, search_query: str, total_searched: int = 0
) -> None:
    """Display search results in a formatted table."""
    if not markets:
        if total_searched > 0:
            console.print(
                f"🔍 No markets found for search query: '{search_query}' (searched {total_searched} markets)"
            )
        else:
            console.print(f"🔍 No markets found for search query: '{search_query}'")
        return

    # Create title with search info including total searched
    if total_searched > 0:
        title = f"🔍 Search Results for '{search_query}' ({len(markets)} found from {total_searched} markets)"
    else:
        title = f"🔍 Search Results for '{search_query}' ({len(markets)} found)"

    table = MarketDisplayer.create_markets_table(markets, title)
    console.print(table)
    console.print(f"\n📊 Found: {len(markets)} markets")


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
@click.argument("query", required=False)
@click.option(
    "--search",
    "-q",
    help="Search markets by title (case-insensitive). When used, fetches all available markets and filters locally.",
)
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
    help="Number of markets to fetch (default: 20 for listing, unlimited for search). Set to 0 for unlimited.",
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
    query: Optional[str],
    search: Optional[str],
    status: str,
    sort_by: str,
    limit: int,
    page: int,
    market_type: str,
    json_output: bool,
):
    """Fetch and display markets from Opinion Open API.

    QUERY can be:
    - Empty: shows a list of markets based on filters
    - Number: shows specific market by ID (e.g., 217)
    - URL: shows market from Opinion Trade URL
    - Text: searches markets by title (case-insensitive)

    Examples:
      # Show default market list
      markets

      # Show specific market by ID
      markets 217

      # Show market from Opinion Trade URL
      markets https://app.opinion.trade/detail?topicId=217
      markets "https://app.opinion.trade/detail?topicId=61&type=multi"

      # Search markets by title (automatic detection)
      markets bitcoin                       # Search for "bitcoin"
      markets "AI prediction"               # Search for "AI prediction"
      markets crypto                        # Search for "crypto"

      # Search with explicit --search option (same as above)
      markets --search bitcoin              # or -q bitcoin
      markets -q "AI prediction"            # Explicit search option

      # List markets with filters
      markets -l 10                         # Show 10 markets
      markets -s resolved                   # Show resolved markets
      markets -t 0                          # Show binary markets only
      markets --sort-by 1                   # Sort by newest first
      markets --sort-by 3 -l 5              # Top 5 by total volume

      # Search with filters
      markets bitcoin -s resolved           # Search "bitcoin" in resolved markets
      markets crypto -t 0                   # Search "crypto" in binary markets only
      markets "AI" -l 100                   # Search "AI" in first 100 markets

      # Pagination and output
      markets -p 2 -l 20                    # Page 2, 20 markets
      markets -j                            # JSON output
      markets 217 --json                    # Specific market as JSON
      markets bitcoin --json                # Search results as JSON

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
                # Determine what to do based on query and search parameters
                market_id = None
                search_query = None

                # Priority: explicit --search option overrides query auto-detection
                if search:
                    search_query = search
                elif query:
                    query_type, processed_value = determine_query_type(query)

                    if query_type == "market_id":
                        market_id = processed_value
                    elif query_type == "url":
                        market_id = processed_value
                    elif query_type == "search":
                        search_query = processed_value
                    else:
                        console.print(
                            f"[red]Error: Invalid query format: {query}[/red]"
                        )
                        console.print("[dim]Supported formats:[/dim]")
                        console.print("[dim]  - Market ID: 217[/dim]")
                        console.print(
                            "[dim]  - URL: https://app.opinion.trade/detail?topicId=217[/dim]"
                        )
                        console.print("[dim]  - Search text: bitcoin[/dim]")
                        sys.exit(1)

                # Handle specific market by ID
                if market_id:
                    # Fetch specific market
                    market = await client.get_market_by_id_parallel(market_id)

                    if not market:
                        console.print(
                            f"[red]{ErrorMessages.MARKET_NOT_FOUND.format(market_id=market_id)}[/red]"
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
                    # Convert string parameters to enums
                    status_enum = MarketStatus(status)
                    sort_enum = SortBy(int(sort_by))
                    market_type_enum = MarketType(int(market_type))

                    # Check if search is requested (either via --search or auto-detected from query)
                    if search_query:
                        # For search, use unlimited by default unless limit is explicitly set
                        # If limit is default (20) and search is used, make it unlimited (0)
                        if limit == 20:  # Default limit for regular markets command
                            search_limit = 0  # Unlimited search
                        else:
                            search_limit = limit

                        markets = await get_all_markets_for_search(
                            client,
                            status_enum,
                            sort_enum,
                            market_type_enum,
                            search_limit,
                        )

                        # Filter markets by search query
                        filtered_markets = search_markets_by_title(
                            markets, search_query
                        )

                        if json_output:
                            markets_data = []
                            for market in filtered_markets:
                                market_dict = market.model_dump()
                                convert_datetime_to_string(market_dict)
                                markets_data.append(market_dict)
                            console.print(JSONDisplayer.to_json_string(markets_data))
                        else:
                            display_search_results_table(
                                filtered_markets, search_query, len(markets)
                            )
                    else:
                        # Regular market listing (existing functionality)
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
