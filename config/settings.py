"""Configuration settings for Opinion CLI."""

from dataclasses import dataclass
import os
from opinion_clob_sdk import Client
from .constants import (
    DEFAULT_CHAIN_ID,
    DEFAULT_OPINION_HOST,
    DEFAULT_CACHE_TTL,
    DUMMY_PRIVATE_KEY,
    DUMMY_MULTI_SIG_ADDRESS,
    ENV_API_KEY,
    ENV_RPC_URL,
    ENV_PRIVATE_KEY,
    ENV_MULTI_SIG_ADDRESS,
    ENV_CHAIN_ID,
    ENV_OPINION_HOST,
    ENV_MARKET_CACHE_TTL,
    ENV_QUOTE_TOKENS_CACHE_TTL,
    ENV_ENABLE_TRADING_CHECK_INTERVAL,
)


@dataclass
class OpinionConfig:
    """Configuration class for Opinion CLOB prediction market client."""

    api_key: str
    rpc_url: str
    private_key: str
    multi_sig_address: str
    chain_id: int = DEFAULT_CHAIN_ID
    host: str = DEFAULT_OPINION_HOST
    market_cache_ttl: int = DEFAULT_CACHE_TTL  # No caching by default
    quote_tokens_cache_ttl: int = DEFAULT_CACHE_TTL  # No caching by default
    enable_trading_check_interval: int = DEFAULT_CACHE_TTL  # No interval by default

    @classmethod
    def from_env(cls) -> "OpinionConfig":
        """Load configuration from environment variables.

        Required environment variables for full functionality:
        - API_KEY: Opinion API key
        - RPC_URL: Blockchain RPC URL
        - PRIVATE_KEY: Private key for transactions
        - MULTI_SIG_ADDRESS: Multi-signature wallet address

        For read-only access, only API_KEY is required.

        Optional environment variables:
        - CHAIN_ID: Blockchain chain ID (default: 56)
        - OPINION_HOST: Opinion API host (default: https://proxy.opinion.trade:8443)
        - MARKET_CACHE_TTL: Market cache TTL in seconds (default: 0 - no caching)
        - QUOTE_TOKENS_CACHE_TTL: Quote tokens cache TTL in seconds (default: 0 - no caching)
        - ENABLE_TRADING_CHECK_INTERVAL: Trading check interval in seconds (default: 0 - disabled)
        """
        # Only API_KEY is required for read-only access
        api_key = os.getenv(ENV_API_KEY)
        if not api_key:
            raise ValueError(f"{ENV_API_KEY} environment variable is required")

        return cls(
            api_key=api_key,
            rpc_url=os.getenv(ENV_RPC_URL, ""),  # Empty for read-only
            private_key=os.getenv(
                ENV_PRIVATE_KEY, DUMMY_PRIVATE_KEY
            ),  # Dummy key for read-only
            multi_sig_address=os.getenv(
                ENV_MULTI_SIG_ADDRESS, DUMMY_MULTI_SIG_ADDRESS
            ),  # Dummy address
            chain_id=int(os.getenv(ENV_CHAIN_ID, DEFAULT_CHAIN_ID)),
            host=os.getenv(ENV_OPINION_HOST, DEFAULT_OPINION_HOST),
            market_cache_ttl=int(os.getenv(ENV_MARKET_CACHE_TTL, DEFAULT_CACHE_TTL)),
            quote_tokens_cache_ttl=int(
                os.getenv(ENV_QUOTE_TOKENS_CACHE_TTL, DEFAULT_CACHE_TTL)
            ),
            enable_trading_check_interval=int(
                os.getenv(ENV_ENABLE_TRADING_CHECK_INTERVAL, DEFAULT_CACHE_TTL)
            ),
        )

    def create_client(self) -> Client:
        """Create Opinion CLOB Client from this configuration.

        By default, creates client with no caching for real-time monitoring.
        """
        return Client(
            host=self.host,
            apikey=self.api_key,
            chain_id=self.chain_id,
            rpc_url=self.rpc_url,
            private_key=self.private_key,
            multi_sig_addr=self.multi_sig_address,
            market_cache_ttl=self.market_cache_ttl,
            quote_tokens_cache_ttl=self.quote_tokens_cache_ttl,
            enable_trading_check_interval=self.enable_trading_check_interval,
        )

    def validate(self) -> bool:
        """Validate configuration parameters."""
        if not self.api_key:
            raise ValueError("API key is required")

        # Validate chain_id is positive
        if self.chain_id <= 0:
            raise ValueError("Chain ID must be positive")

        # Validate URLs if provided
        if self.rpc_url and not (
            self.rpc_url.startswith("http://") or self.rpc_url.startswith("https://")
        ):
            raise ValueError("RPC URL must start with http:// or https://")

        if not (self.host.startswith("http://") or self.host.startswith("https://")):
            raise ValueError("Host URL must start with http:// or https://")

        return True

    def is_read_only_mode(self) -> bool:
        """Check if configuration is in read-only mode."""
        return (
            not self.rpc_url
            or self.private_key == DUMMY_PRIVATE_KEY
            or self.multi_sig_address == DUMMY_MULTI_SIG_ADDRESS
        )

    def can_trade(self) -> bool:
        """Check if configuration allows trading operations."""
        return (
            bool(self.api_key)
            and bool(self.rpc_url)
            and self.private_key != DUMMY_PRIVATE_KEY
            and self.multi_sig_address != DUMMY_MULTI_SIG_ADDRESS
        )
