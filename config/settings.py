"""Configuration settings for Opinion CLI."""

from dataclasses import dataclass
import os
from typing import TYPE_CHECKING
from opinion_clob_sdk import Client

if TYPE_CHECKING:
    from clients.opinion_api_client import OpinionOpenAPIClient

from .constants import (
    DEFAULT_CHAIN_ID,
    DEFAULT_OPINION_HOST,
    DEFAULT_CACHE_TTL,
    DEFAULT_RATE_LIMIT,
    DEFAULT_TIMEOUT,
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
    ENV_RATE_LIMIT,
    ENV_TIMEOUT,
    ValidationConstants,
    ErrorMessages,
)


@dataclass
class OpinionConfig:
    """Unified configuration class for Opinion CLI supporting both CLOB and Open API clients."""

    api_key: str
    rpc_url: str = ""
    private_key: str = DUMMY_PRIVATE_KEY
    multi_sig_address: str = DUMMY_MULTI_SIG_ADDRESS
    chain_id: int = DEFAULT_CHAIN_ID
    host: str = DEFAULT_OPINION_HOST
    market_cache_ttl: int = DEFAULT_CACHE_TTL
    quote_tokens_cache_ttl: int = DEFAULT_CACHE_TTL
    enable_trading_check_interval: int = DEFAULT_CACHE_TTL
    rate_limit: float = DEFAULT_RATE_LIMIT
    timeout: float = DEFAULT_TIMEOUT

    @classmethod
    def from_env(cls) -> "OpinionConfig":
        """Load configuration from environment variables.

        Required environment variables:
        - API_KEY: Opinion API key (required for all operations)

        Optional environment variables for CLOB trading:
        - RPC_URL: Blockchain RPC URL
        - PRIVATE_KEY: Private key for transactions
        - MULTI_SIG_ADDRESS: Multi-signature wallet address

        Optional configuration:
        - CHAIN_ID: Blockchain chain ID (default: 56)
        - OPINION_HOST: Opinion API host (default: https://proxy.opinion.trade:8443)
        - MARKET_CACHE_TTL: Market cache TTL in seconds (default: 0 - no caching)
        - QUOTE_TOKENS_CACHE_TTL: Quote tokens cache TTL in seconds (default: 0 - no caching)
        - ENABLE_TRADING_CHECK_INTERVAL: Trading check interval in seconds (default: 0 - disabled)
        - RATE_LIMIT: API requests per second (default: 12)
        - TIMEOUT: Request timeout in seconds (default: 30.0)
        """
        # API_KEY is required for all operations
        api_key = os.getenv(ENV_API_KEY)
        if not api_key:
            raise ValueError(f"{ENV_API_KEY} environment variable is required")

        return cls(
            api_key=api_key,
            rpc_url=os.getenv(ENV_RPC_URL, ""),
            private_key=os.getenv(ENV_PRIVATE_KEY, DUMMY_PRIVATE_KEY),
            multi_sig_address=os.getenv(ENV_MULTI_SIG_ADDRESS, DUMMY_MULTI_SIG_ADDRESS),
            chain_id=int(os.getenv(ENV_CHAIN_ID, DEFAULT_CHAIN_ID)),
            host=os.getenv(ENV_OPINION_HOST, DEFAULT_OPINION_HOST),
            market_cache_ttl=int(os.getenv(ENV_MARKET_CACHE_TTL, DEFAULT_CACHE_TTL)),
            quote_tokens_cache_ttl=int(
                os.getenv(ENV_QUOTE_TOKENS_CACHE_TTL, DEFAULT_CACHE_TTL)
            ),
            enable_trading_check_interval=int(
                os.getenv(ENV_ENABLE_TRADING_CHECK_INTERVAL, DEFAULT_CACHE_TTL)
            ),
            rate_limit=float(os.getenv(ENV_RATE_LIMIT, DEFAULT_RATE_LIMIT)),
            timeout=float(os.getenv(ENV_TIMEOUT, DEFAULT_TIMEOUT)),
        )

    def create_clob_client(self) -> Client:
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

    def create_open_api_client(self) -> "OpinionOpenAPIClient":
        """Create Opinion Open API Client from this configuration."""
        from clients.opinion_api_client import OpinionOpenAPIClient

        return OpinionOpenAPIClient(
            api_key=self.api_key,
            base_url=self.host,
            rate_limit=self.rate_limit,
            timeout=self.timeout,
        )

    def validate(self) -> bool:
        """Validate configuration parameters."""
        if not self.api_key:
            raise ValueError(ErrorMessages.API_KEY_REQUIRED)

        # Validate API key length
        if len(self.api_key) < ValidationConstants.MIN_API_KEY_LENGTH:
            raise ValueError(
                ErrorMessages.API_KEY_TOO_SHORT.format(
                    min_length=ValidationConstants.MIN_API_KEY_LENGTH
                )
            )

        if len(self.api_key) > ValidationConstants.MAX_API_KEY_LENGTH:
            raise ValueError(
                ErrorMessages.API_KEY_TOO_LONG.format(
                    max_length=ValidationConstants.MAX_API_KEY_LENGTH
                )
            )

        # Validate chain_id is positive
        if self.chain_id <= 0:
            raise ValueError("Chain ID must be positive")

        # Validate rate limit
        if (
            self.rate_limit < ValidationConstants.MIN_RATE_LIMIT
            or self.rate_limit > ValidationConstants.MAX_RATE_LIMIT
        ):
            raise ValueError(
                ErrorMessages.RATE_LIMIT_INVALID.format(
                    min_limit=ValidationConstants.MIN_RATE_LIMIT,
                    max_limit=ValidationConstants.MAX_RATE_LIMIT,
                )
            )

        # Validate timeout
        if (
            self.timeout < ValidationConstants.MIN_TIMEOUT
            or self.timeout > ValidationConstants.MAX_TIMEOUT
        ):
            raise ValueError(
                ErrorMessages.TIMEOUT_INVALID.format(
                    min_timeout=ValidationConstants.MIN_TIMEOUT,
                    max_timeout=ValidationConstants.MAX_TIMEOUT,
                )
            )

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

    def supports_open_api(self) -> bool:
        """Check if configuration supports Open API operations."""
        return bool(self.api_key)

    def supports_clob_api(self) -> bool:
        """Check if configuration supports CLOB API operations."""
        return bool(self.api_key) and not self.is_read_only_mode()
