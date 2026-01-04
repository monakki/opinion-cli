"""Opinion client wrapper with enhanced functionality."""

from typing import Dict, List, Optional, Any
from opinion_clob_sdk import Client
from config.settings import OpinionConfig
from config.constants import DUMMY_PRIVATE_KEY


class OpinionClientWrapper:
    """Wrapper around Opinion CLOB SDK client with additional CLI-friendly methods."""

    def __init__(self, config: OpinionConfig):
        """Initialize the client wrapper with configuration."""
        self.config = config
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Lazy initialization of the Opinion client."""
        if self._client is None:
            self._client = self.config.create_client()
        return self._client

    def get_config_info(self) -> Dict[str, Any]:
        """Get current configuration information (without sensitive data)."""
        return {
            "host": self.config.host,
            "chain_id": self.config.chain_id,
            "multi_sig_address": self.config.multi_sig_address,
            "market_cache_ttl": self.config.market_cache_ttl,
            "quote_tokens_cache_ttl": self.config.quote_tokens_cache_ttl,
            "enable_trading_check_interval": self.config.enable_trading_check_interval,
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
        """Test connection to Opinion API."""
        try:
            # Try to get markets to test connection
            markets = self.client.get_markets()
            return {
                "status": "success",
                "message": "Successfully connected to Opinion API",
                "markets_count": len(markets) if markets else 0,
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to connect: {str(e)}"}

    def get_markets(self) -> List[Dict[str, Any]]:
        """Get all available markets."""
        return self.client.get_markets()

    def get_market_info(self, market_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific market."""
        return self.client.get_market(market_id)

    def get_orders(self) -> List[Dict[str, Any]]:
        """Get user's orders."""
        return self.client.get_orders()

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get user's positions."""
        return self.client.get_positions()

    @classmethod
    def from_env(cls) -> "OpinionClientWrapper":
        """Create client wrapper from environment variables."""
        config = OpinionConfig.from_env()
        return cls(config)
