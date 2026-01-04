"""Input validation utilities."""

import re
from typing import Any

from .constants import (
    DefaultValues,
    ErrorMessages,
    ValidationConstants,
)


class InputValidator:
    """Centralized input validation."""

    @staticmethod
    def validate_market_id(market_id: str) -> bool:
        """Validate market ID format and length."""
        if not market_id:
            return False

        # Check if it's a valid number
        if not market_id.isdigit():
            return False

        # Check length constraints
        if len(market_id) < ValidationConstants.MIN_MARKET_ID_LENGTH:
            return False
        if len(market_id) > ValidationConstants.MAX_MARKET_ID_LENGTH:
            return False

        # Check if it's a positive number
        try:
            return int(market_id) > 0
        except ValueError:
            return False

    @staticmethod
    def validate_api_key(api_key: str) -> tuple[bool, str | None]:
        """Validate API key format and length."""
        if not api_key or not api_key.strip():
            return False, ErrorMessages.API_KEY_REQUIRED

        api_key = api_key.strip()

        if len(api_key) < ValidationConstants.MIN_API_KEY_LENGTH:
            return False, ErrorMessages.API_KEY_TOO_SHORT.format(
                min_length=ValidationConstants.MIN_API_KEY_LENGTH
            )

        if len(api_key) > ValidationConstants.MAX_API_KEY_LENGTH:
            return False, ErrorMessages.API_KEY_TOO_LONG.format(
                max_length=ValidationConstants.MAX_API_KEY_LENGTH
            )

        return True, None

    @staticmethod
    def validate_rate_limit(rate_limit: float) -> tuple[bool, str | None]:
        """Validate rate limit value."""
        if (
            rate_limit < ValidationConstants.MIN_RATE_LIMIT
            or rate_limit > ValidationConstants.MAX_RATE_LIMIT
        ):
            return False, ErrorMessages.RATE_LIMIT_INVALID.format(
                min_limit=ValidationConstants.MIN_RATE_LIMIT,
                max_limit=ValidationConstants.MAX_RATE_LIMIT,
            )
        return True, None

    @staticmethod
    def validate_timeout(timeout: float) -> tuple[bool, str | None]:
        """Validate timeout value."""
        if (
            timeout < ValidationConstants.MIN_TIMEOUT
            or timeout > ValidationConstants.MAX_TIMEOUT
        ):
            return False, ErrorMessages.TIMEOUT_INVALID.format(
                min_timeout=ValidationConstants.MIN_TIMEOUT,
                max_timeout=ValidationConstants.MAX_TIMEOUT,
            )
        return True, None

    @staticmethod
    def validate_limit(limit: int) -> tuple[bool, str | None]:
        """Validate limit parameter."""
        if (
            limit < ValidationConstants.MIN_LIMIT
            or limit > ValidationConstants.MAX_LIMIT
        ):
            return (
                False,
                f"Limit must be between {ValidationConstants.MIN_LIMIT} and {ValidationConstants.MAX_LIMIT}",
            )
        return True, None

    @staticmethod
    def validate_page(page: int) -> tuple[bool, str | None]:
        """Validate page parameter."""
        if page < ValidationConstants.MIN_PAGE or page > ValidationConstants.MAX_PAGE:
            return (
                False,
                f"Page must be between {ValidationConstants.MIN_PAGE} and {ValidationConstants.MAX_PAGE}",
            )
        return True, None


class DataSanitizer:
    """Data sanitization utilities."""

    @staticmethod
    def safe_float(value: Any, fallback: float = DefaultValues.PRICE_FALLBACK) -> float:
        """Safely convert value to float with fallback."""
        if value is None:
            return fallback

        try:
            return float(value)
        except (ValueError, TypeError):
            return fallback

    @staticmethod
    def safe_int(value: Any, fallback: int = 0) -> int:
        """Safely convert value to int with fallback."""
        if value is None:
            return fallback

        try:
            return int(value)
        except (ValueError, TypeError):
            return fallback

    @staticmethod
    def safe_string(value: Any, fallback: str = "") -> str:
        """Safely convert value to string with fallback."""
        if value is None:
            return fallback

        try:
            return str(value).strip()
        except (ValueError, TypeError):
            return fallback

    @staticmethod
    def safe_percentage(
        value: Any, fallback: float = DefaultValues.PERCENTAGE_FALLBACK
    ) -> float:
        """Safely convert price to percentage (0.5 -> 50.0)."""
        price = DataSanitizer.safe_float(value, fallback)
        return price * 100.0

    @staticmethod
    def clean_market_id(market_id: Any) -> str:
        """Clean and validate market ID."""
        if market_id is None:
            return ""

        # Convert to string and remove whitespace
        clean_id = str(market_id).strip()

        # Remove any non-digit characters
        clean_id = re.sub(r"[^\d]", "", clean_id)

        return clean_id


class ResponseValidator:
    """API response validation utilities."""

    @staticmethod
    def is_success_response(data: dict) -> bool:
        """Check if API response indicates success."""
        if not isinstance(data, dict):
            return False

        # Check errno format
        if "errno" in data:
            return data.get("errno") == 0

        # Check code format
        if "code" in data:
            return data.get("code") == 0

        # If no error indicators, assume success
        return True

    @staticmethod
    def extract_error_message(data: dict) -> str:
        """Extract error message from API response."""
        if not isinstance(data, dict):
            return "Invalid response format"

        # Try different error message fields
        for field in ["message", "error", "errmsg", "msg"]:
            if field in data and data[field]:
                return str(data[field])

        return "Unknown error"

    @staticmethod
    def has_required_fields(data: dict, required_fields: list[str]) -> bool:
        """Check if response has all required fields."""
        if not isinstance(data, dict):
            return False

        return all(field in data for field in required_fields)
