"""Opinion CLOB client wrapper with enhanced functionality."""

import asyncio
from typing import Dict, Optional, Any
from aiolimiter import AsyncLimiter
from opinion_clob_sdk import Client
from config.settings import OpinionConfig
from config.constants import DUMMY_PRIVATE_KEY


class OpinionClobClientWrapper:
    """Wrapper around Opinion CLOB SDK client with additional CLI-friendly methods."""

    def __init__(self, config: OpinionConfig):
        """Initialize the CLOB client wrapper with configuration."""
        self.config = config
        self._client: Optional[Client] = None
        self._rate_limiter = AsyncLimiter(
            config.rate_limit, 1.0
        )  # rate_limit per second

    @property
    def client(self) -> Client:
        """Lazy initialization of the Opinion CLOB client."""
        if self._client is None:
            self._client = self.config.create_clob_client()
        return self._client

    async def _rate_limited_call(self, func, *args, **kwargs):
        """Execute a function call with rate limiting."""
        async with self._rate_limiter:
            return func(*args, **kwargs)

    def _sync_rate_limited_call(self, func, *args, **kwargs):
        """Synchronous wrapper for rate limited calls."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self._rate_limited_call(func, *args, **kwargs))

    def get_config_info(self) -> Dict[str, Any]:
        """Get current configuration information (without sensitive data)."""
        return {
            "host": self.config.host,
            "chain_id": self.config.chain_id,
            "multi_sig_address": self.config.multi_sig_address,
            "market_cache_ttl": self.config.market_cache_ttl,
            "quote_tokens_cache_ttl": self.config.quote_tokens_cache_ttl,
            "enable_trading_check_interval": self.config.enable_trading_check_interval,
            "rate_limit": self.config.rate_limit,
            "timeout": self.config.timeout,
            "realtime_mode": self.config.market_cache_ttl == 0,  # True if no caching
            "read_only_mode": self.config.is_read_only_mode(),
            "can_trade": self.config.can_trade(),
            "api_key_set": bool(self.config.api_key),
            "rpc_url_set": bool(self.config.rpc_url),
            "private_key_set": bool(
                self.config.private_key and self.config.private_key != DUMMY_PRIVATE_KEY
            ),
        }

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Opinion CLOB API."""
        try:
            # Try to get markets to test connection with rate limiting
            self._sync_rate_limited_call(self.client.get_markets)

            # If we got here without exception, connection is successful
            return {
                "status": "success",
                "message": "Successfully connected to Opinion CLOB API",
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to connect: {str(e)}"}

    def get_markets(self) -> Any:
        """Get all available markets with rate limiting.

        Returns the raw response from Opinion CLOB API.
        The response structure may vary depending on the API version.
        """
        return self._sync_rate_limited_call(self.client.get_markets)

    def get_market_info(self, market_id: str) -> Any:
        """Get detailed information about a specific market with rate limiting."""
        return self._sync_rate_limited_call(self.client.get_market, market_id)

    def get_orders(self) -> Any:
        """Get user's orders with rate limiting."""
        return self._sync_rate_limited_call(self.client.get_orders)

    def get_positions(self) -> Any:
        """Get user's positions with rate limiting."""
        return self._sync_rate_limited_call(self.client.get_positions)

    def get_balances(self) -> Any:
        """Get user's token balances with rate limiting."""
        return self._sync_rate_limited_call(self.client.get_my_balances)

    @classmethod
    def from_env(cls) -> "OpinionClobClientWrapper":
        """Create CLOB client wrapper from environment variables."""
        config = OpinionConfig.from_env()
        return cls(config)
