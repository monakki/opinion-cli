"""Opinion Open API client with rate limiting."""

import asyncio
from typing import Any
from urllib.parse import urljoin

import httpx
from aiolimiter import AsyncLimiter
from loguru import logger
from pydantic import ValidationError

from config.constants import (
    APIConstants,
    DefaultValues,
    ErrorMessages,
    HTTPConstants,
    ResponseFormats,
    SuccessMessages,
)
from config.validators import InputValidator

from .models import (
    Market,
    MarketStatus,
    MarketType,
    Position,
    SortBy,
    Trade,
)


class OpinionOpenAPIError(Exception):
    """Custom exception for Opinion Open API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class OpinionOpenAPIClient:
    """
    Async client for Opinion Open API with rate limiting.

    Args:
        api_key: API key for authentication
        base_url: Base URL for the API (default: from APIConstants.DEFAULT_BASE_URL)
        rate_limit: Maximum requests per second (default: from APIConstants.DEFAULT_RATE_LIMIT)
        timeout: Request timeout in seconds (default: from APIConstants.DEFAULT_TIMEOUT)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = APIConstants.DEFAULT_BASE_URL,
        rate_limit: float = APIConstants.DEFAULT_RATE_LIMIT,
        timeout: float = APIConstants.DEFAULT_TIMEOUT,
    ):
        # Validate API key
        is_valid, error_msg = InputValidator.validate_api_key(api_key)
        if not is_valid:
            raise ValueError(error_msg)

        # Validate rate limit
        is_valid, error_msg = InputValidator.validate_rate_limit(rate_limit)
        if not is_valid:
            raise ValueError(error_msg)

        # Validate timeout
        is_valid, error_msg = InputValidator.validate_timeout(timeout)
        if not is_valid:
            raise ValueError(error_msg)

        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Rate limiter - allows rate_limit requests per second
        self.rate_limiter = AsyncLimiter(max_rate=rate_limit, time_period=1.0)

        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                HTTPConstants.HEADERS["api_key"]: self.api_key,
                HTTPConstants.HEADERS["content_type"]: HTTPConstants.CONTENT_TYPE_JSON,
                HTTPConstants.HEADERS["user_agent"]: APIConstants.USER_AGENT,
            },
        )

        logger.info(
            SuccessMessages.CLIENT_INITIALIZED.format(
                base_url=base_url, rate_limit=rate_limit
            )
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info(SuccessMessages.CLIENT_CLOSED)

    def _extract_markets_from_response(self, data: dict | list) -> list[dict]:
        """Extract markets data from API response with multiple format support."""
        if isinstance(data, list):
            return data

        if not isinstance(data, dict):
            logger.warning(f"Unexpected response format: {type(data)}")
            return DefaultValues.EMPTY_MARKET_LIST

        # Check for standard API format: {"errno": 0, "result": {"list": [...]}}
        if (
            ResponseFormats.RESULT_KEY in data
            and data.get(ResponseFormats.ERRNO_KEY) == ResponseFormats.SUCCESS_ERRNO
        ):
            result = data[ResponseFormats.RESULT_KEY]
            if isinstance(result, dict) and ResponseFormats.LIST_KEY in result:
                markets_list = result[ResponseFormats.LIST_KEY]
                total = result.get(ResponseFormats.TOTAL_KEY, "unknown")
                logger.info(f"Found {len(markets_list)} markets, total: {total}")
                return markets_list

        # Alternative format: {"code": 0, "result": {"list": [...]}}
        elif (
            ResponseFormats.RESULT_KEY in data
            and data.get(ResponseFormats.CODE_KEY) == ResponseFormats.SUCCESS_CODE
        ):
            result = data[ResponseFormats.RESULT_KEY]
            if isinstance(result, dict) and ResponseFormats.LIST_KEY in result:
                markets_list = result[ResponseFormats.LIST_KEY]
                total = result.get(ResponseFormats.TOTAL_KEY, "unknown")
                logger.info(f"Found {len(markets_list)} markets, total: {total}")
                return markets_list

        # Fallback formats
        for key in [ResponseFormats.DATA_KEY, "markets", "results"]:
            if key in data:
                return (
                    data[key]
                    if isinstance(data[key], list)
                    else DefaultValues.EMPTY_MARKET_LIST
                )

        logger.warning(f"Unknown API response format. Keys: {list(data.keys())}")
        return DefaultValues.EMPTY_MARKET_LIST

    def _parse_market_data(self, markets_data: list[dict]) -> list[Market]:
        """Parse market data with error handling."""
        markets = []

        for i, market_data in enumerate(markets_data):
            try:
                if not isinstance(market_data, dict):
                    logger.warning(
                        f"Market data {i} is not dict, skipping: {type(market_data)}"
                    )
                    continue

                market = Market(**market_data)
                markets.append(market)

            except ValidationError as e:
                logger.warning(f"Failed to parse market {i}: {e}")
                logger.debug(f"Market data that failed: {market_data}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error parsing market {i}: {e}")
                continue

        logger.info(
            f"Successfully parsed {len(markets)} markets out of {len(markets_data)} items"
        )
        return markets

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make a rate-limited HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON request body

        Returns:
            Response data as dictionary

        Raises:
            OpinionOpenAPIError: If the API returns an error
        """
        # Apply rate limiting
        async with self.rate_limiter:
            url = urljoin(self.base_url, endpoint)

            logger.debug(f"Making {method} request to {url} with params={params}")

            try:
                response = await self.client.request(
                    method=method, url=url, params=params, json=json_data
                )

                # Log response details
                logger.debug(f"Response status: {response.status_code}")

                # Handle different response status codes
                if response.status_code == HTTPConstants.STATUS_OK:
                    data = response.json()
                    logger.debug(f"Successful response: {len(str(data))} chars")
                    return data

                elif response.status_code == HTTPConstants.STATUS_RATE_LIMITED:
                    # Rate limit exceeded
                    retry_after = response.headers.get("Retry-After", "60")
                    logger.warning(
                        f"Rate limit exceeded, retry after {retry_after} seconds"
                    )
                    raise OpinionOpenAPIError(
                        ErrorMessages.RATE_LIMIT_EXCEEDED.format(
                            retry_after=retry_after
                        ),
                        status_code=HTTPConstants.STATUS_RATE_LIMITED,
                    )

                else:
                    # Try to parse error response
                    try:
                        error_data = response.json()
                        error_msg = error_data.get(
                            "message", f"HTTP {response.status_code}"
                        )
                    except Exception:
                        error_msg = f"HTTP {response.status_code}: {response.text}"

                    logger.error(f"API error: {error_msg}")
                    raise OpinionOpenAPIError(
                        error_msg,
                        status_code=response.status_code,
                        response_data=error_data if "error_data" in locals() else None,
                    )

            except httpx.TimeoutException as e:
                logger.error(f"Request timeout for {url}")
                raise OpinionOpenAPIError(ErrorMessages.REQUEST_TIMEOUT) from e

            except httpx.RequestError as e:
                logger.error(f"Request error for {url}: {e}")
                raise OpinionOpenAPIError(f"Request error: {e}") from e

    async def get_markets(
        self,
        status: MarketStatus | None = MarketStatus.ACTIVATED,
        sort_by: SortBy | None = SortBy.VOLUME_24H_DESC,
        limit: int = 10,
        page: int = 1,
        market_type: MarketType | None = MarketType.ALL,
        chain_id: str | None = None,
    ) -> list[Market]:
        """
        Get markets from the API with automatic pagination support.

        Args:
            status: Market status filter
            sort_by: Sorting option
            limit: Maximum number of markets to return (max 1000, will use pagination)
            page: Starting page number (starts from 1)
            market_type: Market type filter
            chain_id: Chain ID filter

        Returns:
            List of Market objects
        """
        all_markets = []
        current_page = page
        remaining_limit = min(
            limit, APIConstants.MAX_MARKETS_TOTAL
        )  # Cap at max for safety

        logger.info(
            f"Fetching up to {remaining_limit} markets starting from page {page}"
        )

        while remaining_limit > 0:
            # Calculate how many items to request for this page (max per API call)
            page_limit = min(remaining_limit, APIConstants.MAX_MARKETS_PER_REQUEST)

            params = {
                "limit": page_limit,
                "page": current_page,
            }

            if status:
                params["status"] = status.value

            if sort_by:
                params["sortBy"] = sort_by.value

            if market_type is not None:
                params["marketType"] = market_type.value

            if chain_id:
                params["chainId"] = chain_id

            logger.info(f"Fetching page {current_page} with {page_limit} items")

            try:
                data = await self._make_request("GET", "/openapi/market", params=params)
                markets_data = self._extract_markets_from_response(data)
                page_markets = self._parse_market_data(markets_data)

                if not page_markets:
                    logger.info("No more markets available, stopping pagination")
                    break

                all_markets.extend(page_markets)
                remaining_limit -= len(page_markets)

                # If we got fewer markets than requested, we've reached the end
                if len(page_markets) < page_limit:
                    logger.info(
                        f"Received {len(page_markets)} markets (less than requested {page_limit}), stopping pagination"
                    )
                    break

                current_page += 1

                # Add a small delay between requests to be respectful to the API
                if remaining_limit > 0:
                    await asyncio.sleep(APIConstants.PAGINATION_DELAY)

            except OpinionOpenAPIError:
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching page {current_page}: {e}")
                raise OpinionOpenAPIError(f"Unexpected error: {e}") from e

        logger.info(f"Successfully fetched {len(all_markets)} markets total")
        return all_markets

    async def get_market_by_id(self, market_id: str) -> Market | None:
        """
        Get a specific market by ID with automatic endpoint detection.

        Tries both categorical and binary endpoints to find the market.
        Starts with categorical since there are more categorical markets.

        Args:
            market_id: Market identifier

        Returns:
            Market object or None if not found
        """
        logger.info(f"Fetching market with ID: {market_id}")

        # Strategy: Try categorical endpoint first (more markets), then binary
        endpoints_to_try = [
            f"/openapi/market/categorical/{market_id}",  # Categorical market endpoint
            f"/openapi/market/{market_id}",  # Binary market endpoint
        ]

        for i, endpoint in enumerate(endpoints_to_try):
            endpoint_type = "categorical" if i == 0 else "binary"
            logger.debug(f"Trying {endpoint_type} endpoint: {endpoint}")

            try:
                data = await self._make_request("GET", endpoint)

                # Handle different response formats
                market_data = None
                if isinstance(data, dict):
                    # Handle format: {"errmsg": "", "errno": 0, "result": {"data": {...}}}
                    if "result" in data and data.get("errno") == 0:
                        result = data["result"]
                        if isinstance(result, dict) and "data" in result:
                            market_data = result["data"]
                        elif isinstance(result, dict):
                            market_data = result
                    # Handle format: {"code": 0, "msg": "success", "result": {"data": {...}}}
                    elif "result" in data and data.get("code") == 0:
                        result = data["result"]
                        if isinstance(result, dict) and "data" in result:
                            market_data = result["data"]
                        else:
                            market_data = result
                    # Handle direct data format
                    elif "data" in data:
                        market_data = data["data"]
                    # Handle case where data is the market itself
                    elif "marketId" in data or "marketTitle" in data:
                        market_data = data

                if market_data:
                    try:
                        market = Market(**market_data)
                        logger.info(
                            f"Successfully fetched {endpoint_type} market: {market.title}"
                        )
                        return market
                    except ValidationError as e:
                        logger.warning(
                            f"Failed to parse {endpoint_type} market data: {e}"
                        )
                        continue
                else:
                    logger.warning(f"No market data found in {endpoint_type} response")
                    continue

            except OpinionOpenAPIError as e:
                if e.status_code == HTTPConstants.STATUS_NOT_FOUND:
                    logger.debug(
                        f"Market {market_id} not found on {endpoint_type} endpoint"
                    )
                    continue
                else:
                    logger.warning(f"Error fetching from {endpoint_type} endpoint: {e}")
                    continue
            except Exception as e:
                logger.warning(f"Unexpected error with {endpoint_type} endpoint: {e}")
                continue

        logger.warning(ErrorMessages.MARKET_NOT_FOUND.format(market_id=market_id))
        return None

    async def get_market_by_id_parallel(self, market_id: str) -> Market | None:
        """
        Get a specific market by ID using parallel requests to both endpoints.

        Alternative implementation that makes both requests simultaneously.
        Prioritizes categorical result since there are more categorical markets.

        Args:
            market_id: Market identifier

        Returns:
            Market object or None if not found
        """
        logger.info(f"Fetching market with ID: {market_id} (parallel strategy)")

        # Create both requests simultaneously
        categorical_task = asyncio.create_task(
            self._make_request("GET", f"/openapi/market/categorical/{market_id}")
        )
        binary_task = asyncio.create_task(
            self._make_request("GET", f"/openapi/market/{market_id}")
        )

        # Wait for both requests to complete
        try:
            categorical_result, binary_result = await asyncio.gather(
                categorical_task, binary_task, return_exceptions=True
            )

            # Try to parse categorical result first (more likely to succeed)
            if not isinstance(categorical_result, Exception):
                try:
                    market_data = self._extract_market_data_from_response(
                        categorical_result
                    )
                    if market_data:
                        market = Market(**market_data)
                        logger.info(
                            f"Successfully fetched categorical market: {market.title}"
                        )
                        return market
                except Exception as e:
                    logger.debug(f"Failed to parse categorical market: {e}")

            # Try binary result as fallback
            if not isinstance(binary_result, Exception):
                try:
                    market_data = self._extract_market_data_from_response(binary_result)
                    if market_data:
                        market = Market(**market_data)
                        logger.info(
                            f"Successfully fetched binary market: {market.title}"
                        )
                        return market
                except Exception as e:
                    logger.debug(f"Failed to parse binary market: {e}")

            logger.warning(ErrorMessages.MARKET_NOT_FOUND.format(market_id=market_id))
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching market {market_id}: {e}")
            return None

    def _extract_market_data_from_response(self, data: dict) -> dict | None:
        """Extract market data from API response."""
        if isinstance(data, dict):
            # Handle format: {"errmsg": "", "errno": 0, "result": {"data": {...}}}
            if "result" in data and data.get("errno") == 0:
                result = data["result"]
                if isinstance(result, dict) and "data" in result:
                    return result["data"]
                elif isinstance(result, dict):
                    return result
            # Handle format: {"code": 0, "msg": "success", "result": {"data": {...}}}
            elif "result" in data and data.get("code") == 0:
                result = data["result"]
                if isinstance(result, dict) and "data" in result:
                    return result["data"]
                else:
                    return result
            # Handle direct data format
            elif "data" in data:
                return data["data"]
            # Handle case where data is the market itself
            elif "marketId" in data or "marketTitle" in data:
                return data
        return None

    async def health_check(self) -> bool:
        """
        Check if the API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Try to fetch a small number of markets as health check
            await self.get_markets(limit=1)
            logger.info("API health check passed")
            return True
        except Exception as e:
            logger.error(ErrorMessages.API_HEALTH_FAILED + f": {e}")
            return False

    async def get_latest_price(self, token_id: str) -> dict[str, Any] | None:
        """
        Get the latest trade price and details for a specific token.

        Args:
            token_id: Token ID to get price for

        Returns:
            Dictionary with price data or None if not found
        """
        logger.info(f"Fetching latest price for token: {token_id}")

        try:
            params = {"token_id": token_id}
            data = await self._make_request(
                "GET", "/openapi/token/latest-price", params=params
            )

            if isinstance(data, dict) and data.get("errno") == 0:
                result = data.get("result", {})
                logger.info(f"Successfully fetched latest price for token {token_id}")
                return result
            else:
                logger.warning(f"No price data found for token {token_id}")
                return None

        except OpinionOpenAPIError as e:
            if e.status_code == HTTPConstants.STATUS_NOT_FOUND:
                logger.warning(f"Token {token_id} not found")
                return None
            else:
                logger.error(f"Error fetching latest price for token {token_id}: {e}")
                raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching latest price for token {token_id}: {e}"
            )
            raise OpinionOpenAPIError(f"Unexpected error: {e}") from e

    async def get_orderbook(self, token_id: str) -> dict[str, Any] | None:
        """
        Get the orderbook (market depth) for a specific token.

        Args:
            token_id: Token ID to get orderbook for

        Returns:
            Dictionary with orderbook data or None if not found
        """
        logger.info(f"Fetching orderbook for token: {token_id}")

        try:
            params = {"token_id": token_id}
            data = await self._make_request(
                "GET", "/openapi/token/orderbook", params=params
            )

            if isinstance(data, dict) and data.get("errno") == 0:
                result = data.get("result", {})
                logger.info(f"Successfully fetched orderbook for token {token_id}")
                return result
            else:
                logger.warning(f"No orderbook data found for token {token_id}")
                return None

        except OpinionOpenAPIError as e:
            if e.status_code == HTTPConstants.STATUS_NOT_FOUND:
                logger.warning(f"Token {token_id} not found")
                return None
            else:
                logger.error(f"Error fetching orderbook for token {token_id}: {e}")
                raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching orderbook for token {token_id}: {e}"
            )
            raise OpinionOpenAPIError(f"Unexpected error: {e}") from e

    async def get_user_positions(
        self,
        wallet_address: str,
        page: int = 1,
        limit: int = 10,
        market_id: int | None = None,
        chain_id: str | None = None,
    ) -> list[Position]:
        """
        Get positions (portfolio) of a specific user by wallet address with automatic pagination support.

        Results are sorted by position size (descending).

        Args:
            wallet_address: Target user's wallet address
            page: Starting page number (starts from 1)
            limit: Maximum number of positions to return (max 1000, will use pagination)
            market_id: Market ID filter (optional)
            chain_id: Chain ID filter (optional)

        Returns:
            List of Position objects

        Raises:
            OpinionOpenAPIError: If the API returns an error
            ValueError: If wallet_address is invalid
        """
        # Validate wallet address
        if not wallet_address or not isinstance(wallet_address, str):
            raise ValueError("wallet_address must be a non-empty string")

        wallet_address = wallet_address.strip()
        if not wallet_address:
            raise ValueError("wallet_address cannot be empty")

        # Validate pagination parameters
        if page < 1:
            raise ValueError("page must be >= 1")

        if limit < 1:
            raise ValueError("limit must be >= 1")

        all_positions = []
        current_page = page
        remaining_limit = min(
            limit, APIConstants.MAX_POSITIONS_TOTAL
        )  # Cap at max for safety

        logger.info(
            f"Fetching up to {remaining_limit} positions for wallet {wallet_address} starting from page {page}"
        )

        while remaining_limit > 0:
            # Calculate how many items to request for this page (max per API call)
            page_limit = min(remaining_limit, APIConstants.MAX_POSITIONS_PER_REQUEST)

            params = {
                "page": current_page,
                "limit": page_limit,
            }

            if market_id is not None:
                params["marketId"] = market_id

            if chain_id:
                params["chainId"] = chain_id

            logger.info(f"Fetching page {current_page} with {page_limit} items")

            try:
                endpoint = f"/openapi/positions/user/{wallet_address}"
                data = await self._make_request("GET", endpoint, params=params)

                # Extract positions from response
                positions_data = self._extract_positions_from_response(data)
                page_positions = self._parse_positions_data(positions_data)

                if not page_positions:
                    logger.info("No more positions available, stopping pagination")
                    break

                all_positions.extend(page_positions)
                remaining_limit -= len(page_positions)

                # If we got fewer positions than requested, we've reached the end
                if len(page_positions) < page_limit:
                    logger.info(
                        f"Received {len(page_positions)} positions (less than requested {page_limit}), stopping pagination"
                    )
                    break

                current_page += 1

                # Add a small delay between requests to be respectful to the API
                if remaining_limit > 0:
                    await asyncio.sleep(APIConstants.PAGINATION_DELAY)

            except OpinionOpenAPIError:
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error fetching positions page {current_page} for wallet {wallet_address}: {e}"
                )
                raise OpinionOpenAPIError(f"Unexpected error: {e}") from e

        logger.info(
            f"Successfully fetched {len(all_positions)} positions total for wallet {wallet_address}"
        )
        return all_positions

    def _extract_positions_from_response(self, data: dict | list) -> list[dict]:
        """Extract positions data from API response."""
        if isinstance(data, list):
            return data

        if not isinstance(data, dict):
            logger.warning(f"Unexpected response format: {type(data)}")
            return []

        # Check for standard API format: {"code": 0, "msg": "success", "result": {"list": [...]}}
        if (
            ResponseFormats.RESULT_KEY in data
            and data.get(ResponseFormats.CODE_KEY) == ResponseFormats.SUCCESS_CODE
        ):
            result = data[ResponseFormats.RESULT_KEY]
            if isinstance(result, dict) and ResponseFormats.LIST_KEY in result:
                positions_list = result[ResponseFormats.LIST_KEY]
                total = result.get(ResponseFormats.TOTAL_KEY, "unknown")
                logger.info(f"Found {len(positions_list)} positions, total: {total}")
                return positions_list

        # Alternative format: {"errno": 0, "result": {"list": [...]}}
        elif (
            ResponseFormats.RESULT_KEY in data
            and data.get(ResponseFormats.ERRNO_KEY) == ResponseFormats.SUCCESS_ERRNO
        ):
            result = data[ResponseFormats.RESULT_KEY]
            if isinstance(result, dict) and ResponseFormats.LIST_KEY in result:
                positions_list = result[ResponseFormats.LIST_KEY]
                total = result.get(ResponseFormats.TOTAL_KEY, "unknown")
                logger.info(f"Found {len(positions_list)} positions, total: {total}")
                return positions_list

        # Fallback formats
        for key in [ResponseFormats.DATA_KEY, "positions", "results"]:
            if key in data:
                return data[key] if isinstance(data[key], list) else []

        logger.warning(f"Unknown API response format. Keys: {list(data.keys())}")
        return []

    def _parse_positions_data(self, positions_data: list[dict]) -> list[Position]:
        """Parse positions data with error handling."""
        positions = []

        for i, position_data in enumerate(positions_data):
            try:
                if not isinstance(position_data, dict):
                    logger.warning(
                        f"Position data {i} is not dict, skipping: {type(position_data)}"
                    )
                    continue

                position = Position(**position_data)
                positions.append(position)

            except ValidationError as e:
                logger.warning(f"Failed to parse position {i}: {e}")
                logger.debug(f"Position data that failed: {position_data}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error parsing position {i}: {e}")
                continue

        logger.info(
            f"Successfully parsed {len(positions)} positions out of {len(positions_data)} items"
        )
        return positions

    async def get_user_trades(
        self,
        wallet_address: str,
        page: int = 1,
        limit: int = 10,
        market_id: int | None = None,
        chain_id: str | None = None,
    ) -> list[Trade]:
        """
        Get trades of a specific user by wallet address with automatic pagination support.

        Only returns filled (successful) trades. Results are sorted by creation time (descending).

        Args:
            wallet_address: Target user's wallet address
            page: Starting page number (starts from 1)
            limit: Maximum number of trades to return (max 1000, will use pagination)
            market_id: Market ID filter (optional)
            chain_id: Chain ID filter (optional)

        Returns:
            List of Trade objects

        Raises:
            OpinionOpenAPIError: If the API returns an error
            ValueError: If wallet_address is invalid
        """
        # Validate wallet address
        if not wallet_address or not isinstance(wallet_address, str):
            raise ValueError("wallet_address must be a non-empty string")

        wallet_address = wallet_address.strip()
        if not wallet_address:
            raise ValueError("wallet_address cannot be empty")

        # Validate pagination parameters
        if page < 1:
            raise ValueError("page must be >= 1")

        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")

        all_trades = []
        current_page = page
        remaining_limit = min(
            limit, APIConstants.MAX_TRADES_TOTAL
        )  # Cap at max for safety

        logger.info(
            f"Fetching up to {remaining_limit} trades for wallet {wallet_address} starting from page {page}"
        )

        while remaining_limit > 0:
            # Calculate how many items to request for this page (max per API call)
            page_limit = min(remaining_limit, APIConstants.MAX_TRADES_PER_REQUEST)

            params = {
                "page": current_page,
                "limit": page_limit,
            }

            if market_id is not None:
                params["marketId"] = market_id

            if chain_id:
                params["chainId"] = chain_id

            logger.info(f"Fetching page {current_page} with {page_limit} items")

            try:
                endpoint = f"/openapi/trade/user/{wallet_address}"
                data = await self._make_request("GET", endpoint, params=params)

                # Extract trades from response
                trades_data = self._extract_trades_from_response(data)
                page_trades = self._parse_trades_data(trades_data)

                if not page_trades:
                    logger.info("No more trades available, stopping pagination")
                    break

                all_trades.extend(page_trades)
                remaining_limit -= len(page_trades)

                # If we got fewer trades than requested, we've reached the end
                if len(page_trades) < page_limit:
                    logger.info(
                        f"Received {len(page_trades)} trades (less than requested {page_limit}), stopping pagination"
                    )
                    break

                current_page += 1

                # Add a small delay between requests to be respectful to the API
                if remaining_limit > 0:
                    await asyncio.sleep(APIConstants.PAGINATION_DELAY)

            except OpinionOpenAPIError:
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error fetching trades page {current_page} for wallet {wallet_address}: {e}"
                )
                raise OpinionOpenAPIError(f"Unexpected error: {e}") from e

        logger.info(
            f"Successfully fetched {len(all_trades)} trades for wallet {wallet_address}"
        )
        return all_trades

    def _extract_trades_from_response(self, data: dict | list) -> list[dict]:
        """Extract trades data from API response."""
        if isinstance(data, list):
            return data

        if not isinstance(data, dict):
            logger.warning(f"Unexpected response format: {type(data)}")
            return []

        # Check for standard API format: {"code": 0, "msg": "success", "result": {"list": [...]}}
        if (
            ResponseFormats.RESULT_KEY in data
            and data.get(ResponseFormats.CODE_KEY) == ResponseFormats.SUCCESS_CODE
        ):
            result = data[ResponseFormats.RESULT_KEY]
            if isinstance(result, dict) and ResponseFormats.LIST_KEY in result:
                trades_list = result[ResponseFormats.LIST_KEY]
                total = result.get(ResponseFormats.TOTAL_KEY, "unknown")
                logger.info(f"Found {len(trades_list)} trades, total: {total}")
                return trades_list

        # Alternative format: {"errno": 0, "result": {"list": [...]}}
        elif (
            ResponseFormats.RESULT_KEY in data
            and data.get(ResponseFormats.ERRNO_KEY) == ResponseFormats.SUCCESS_ERRNO
        ):
            result = data[ResponseFormats.RESULT_KEY]
            if isinstance(result, dict) and ResponseFormats.LIST_KEY in result:
                trades_list = result[ResponseFormats.LIST_KEY]
                total = result.get(ResponseFormats.TOTAL_KEY, "unknown")
                logger.info(f"Found {len(trades_list)} trades, total: {total}")
                return trades_list

        # Fallback formats
        for key in [ResponseFormats.DATA_KEY, "trades", "results"]:
            if key in data:
                return data[key] if isinstance(data[key], list) else []

        logger.warning(f"Unknown API response format. Keys: {list(data.keys())}")
        return []

    def _parse_trades_data(self, trades_data: list[dict]) -> list[Trade]:
        """Parse trades data with error handling."""
        trades = []

        for i, trade_data in enumerate(trades_data):
            try:
                if not isinstance(trade_data, dict):
                    logger.warning(
                        f"Trade data {i} is not dict, skipping: {type(trade_data)}"
                    )
                    continue

                trade = Trade(**trade_data)
                trades.append(trade)

            except ValidationError as e:
                logger.warning(f"Failed to parse trade {i}: {e}")
                logger.debug(f"Trade data that failed: {trade_data}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error parsing trade {i}: {e}")
                continue

        logger.info(
            f"Successfully parsed {len(trades)} trades out of {len(trades_data)} items"
        )
        return trades
