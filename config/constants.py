"""Constants for Opinion CLI configuration."""

from enum import Enum

# Default configuration values
DEFAULT_CHAIN_ID = 56
DEFAULT_OPINION_HOST = "https://proxy.opinion.trade:8443"
DEFAULT_CACHE_TTL = 0
DEFAULT_RATE_LIMIT = 12
DEFAULT_TIMEOUT = 30.0

# Read-only mode dummy values
DUMMY_PRIVATE_KEY = "0x0000000000000000000000000000000000000000000000000000000000000000"
DUMMY_MULTI_SIG_ADDRESS = "0x0000000000000000000000000000000000000000"

# UI Constants
SEPARATOR_LENGTH = 40

# Environment variable names
ENV_API_KEY = "API_KEY"
ENV_RPC_URL = "RPC_URL"
ENV_PRIVATE_KEY = "PRIVATE_KEY"
ENV_MULTI_SIG_ADDRESS = "MULTI_SIG_ADDRESS"
ENV_CHAIN_ID = "CHAIN_ID"
ENV_OPINION_HOST = "OPINION_HOST"
ENV_MARKET_CACHE_TTL = "MARKET_CACHE_TTL"
ENV_QUOTE_TOKENS_CACHE_TTL = "QUOTE_TOKENS_CACHE_TTL"
ENV_ENABLE_TRADING_CHECK_INTERVAL = "ENABLE_TRADING_CHECK_INTERVAL"
ENV_RATE_LIMIT = "RATE_LIMIT"
ENV_TIMEOUT = "TIMEOUT"
ENV_LOG_LEVEL = "LOG_LEVEL"


class MarketStatus(str, Enum):
    """Market status enumeration."""

    ACTIVATED = "activated"
    RESOLVED = "resolved"


class MarketType(int, Enum):
    """Market type enumeration."""

    BINARY = 0
    CATEGORICAL = 1
    ALL = 2


class SortBy(int, Enum):
    """Market sorting options."""

    NEW = 1
    ENDING_SOON = 2
    VOLUME_DESC = 3
    VOLUME_ASC = 4
    VOLUME_24H_DESC = 5
    VOLUME_24H_ASC = 6
    VOLUME_7D_DESC = 7
    VOLUME_7D_ASC = 8


# API Constants
class APIConstants:
    """API-related constants."""

    DEFAULT_BASE_URL = DEFAULT_OPINION_HOST
    DEFAULT_RATE_LIMIT = DEFAULT_RATE_LIMIT
    DEFAULT_TIMEOUT = DEFAULT_TIMEOUT
    MAX_MARKETS_PER_REQUEST = 20
    MAX_MARKETS_TOTAL = 1000
    MAX_POSITIONS_PER_REQUEST = 20
    MAX_POSITIONS_TOTAL = 1000
    MAX_TRADES_PER_REQUEST = 20
    MAX_TRADES_TOTAL = 1000
    PAGINATION_DELAY = 0.1
    USER_AGENT = "opinion-cli/0.1.0"

    # API Endpoints
    ENDPOINTS = {
        "markets": "/openapi/market",
        "market_categorical": "/openapi/market/categorical/{market_id}",
        "market_binary": "/openapi/market/{market_id}",
        "latest_price": "/openapi/token/latest-price",
        "orderbook": "/openapi/token/orderbook",
        "user_positions": "/openapi/positions/user/{wallet_address}",
        "user_trades": "/openapi/trade/user/{wallet_address}",
    }


# HTTP Constants
class HTTPConstants:
    """HTTP-related constants."""

    STATUS_OK = 200
    STATUS_NOT_FOUND = 404
    STATUS_RATE_LIMITED = 429
    STATUS_BAD_REQUEST = 400
    STATUS_UNAUTHORIZED = 401
    STATUS_FORBIDDEN = 403
    STATUS_INTERNAL_ERROR = 500

    CONTENT_TYPE_JSON = "application/json"

    # Headers
    HEADERS = {
        "content_type": "Content-Type",
        "user_agent": "User-Agent",
        "api_key": "apikey",
        "retry_after": "Retry-After",
    }


# Validation Constants
class ValidationConstants:
    """Validation-related constants."""

    MIN_RATE_LIMIT = 0.1
    MAX_RATE_LIMIT = 100.0
    MIN_TIMEOUT = 1.0
    MAX_TIMEOUT = 300.0
    MIN_LIMIT = 1
    MAX_LIMIT = 1000
    MIN_PAGE = 1
    MAX_PAGE = 1000

    # String length limits
    MIN_API_KEY_LENGTH = 10
    MAX_API_KEY_LENGTH = 200
    MIN_MARKET_ID_LENGTH = 1
    MAX_MARKET_ID_LENGTH = 20


# Error Messages
class ErrorMessages:
    """Common error messages."""

    API_KEY_REQUIRED = "API_KEY is required"
    API_KEY_TOO_SHORT = "API key must be at least {min_length} characters"
    API_KEY_TOO_LONG = "API key must be no more than {max_length} characters"

    RATE_LIMIT_INVALID = "Rate limit must be between {min_limit} and {max_limit}"
    TIMEOUT_INVALID = "Timeout must be between {min_timeout} and {max_timeout} seconds"

    MARKET_NOT_FOUND = "Market {market_id} not found"
    API_HEALTH_FAILED = "API health check failed"
    REQUEST_TIMEOUT = "Request timeout"
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Retry after {retry_after} seconds"
    WALLET_ADDRESS_REQUIRED = "Wallet address is required. Provide it as argument or set WALLET_ADDRESS environment variable."


# Success Messages
class SuccessMessages:
    """Common success messages."""

    CLIENT_INITIALIZED = "OpinionOpenAPIClient initialized with base_url={base_url}, rate_limit={rate_limit}/sec"
    CLIENT_CLOSED = "OpinionOpenAPIClient closed"


# Response Format Constants
class ResponseFormats:
    """API response format constants."""

    # Standard response keys
    ERRNO_KEY = "errno"
    CODE_KEY = "code"
    RESULT_KEY = "result"
    DATA_KEY = "data"
    LIST_KEY = "list"
    TOTAL_KEY = "total"
    MESSAGE_KEY = "message"
    ERROR_KEY = "error"

    # Success indicators
    SUCCESS_ERRNO = 0
    SUCCESS_CODE = 0


# Default Values
class DefaultValues:
    """Default values for various data types."""

    PRICE_FALLBACK = 0.0
    VOLUME_FALLBACK = 0.0
    PERCENTAGE_FALLBACK = 0.0
    DATE_FALLBACK = "N/A"
    STATUS_FALLBACK = "Unknown"
    TYPE_FALLBACK = "Unknown"

    # Empty data structures
    EMPTY_ORDERBOOK = {"bids": [], "asks": []}
    EMPTY_MARKET_LIST = []
    EMPTY_CHILD_MARKETS = []


# Display Constants
class DisplayConstants:
    """Display-related constants."""

    # Table display settings
    MAX_TITLE_WIDTH = 50
    MAX_ID_LENGTH = 12
    TABLE_WIDTH = 120
    ORDERBOOK_LEVELS = 5

    # Formatting precision
    VOLUME_PRECISION = 2
    PERCENTAGE_PRECISION = 1

    # Orderbook column widths
    ORDERBOOK_COLUMNS = {
        "total": 12,
        "size": 8,
        "price": 8,
        "separator": 2,
    }

    # Color scheme
    COLORS = {
        "success": "green",
        "error": "red",
        "warning": "yellow",
        "info": "cyan",
    }


# Logging Constants
class LoggingConstants:
    """Logging-related constants."""

    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    DEFAULT_LOG_LEVEL = None  # Disabled by default

    # Log formats
    DETAILED_FORMAT = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>"
    SIMPLE_FORMAT = "<level>{level: <8}</level> | <level>{message}</level>"
    MINIMAL_FORMAT = "<level>{message}</level>"
