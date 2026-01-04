"""Pure formatting functions for data display."""

from datetime import datetime
from typing import Any

from config.constants import DefaultValues, DisplayConstants
from config.validators import DataSanitizer


def format_date(date_value: Any) -> str:
    """Format date value consistently."""
    if not date_value:
        return DefaultValues.DATE_FALLBACK
    if isinstance(date_value, datetime):
        return date_value.strftime("%Y-%m-%d")
    return str(date_value)[:10]


def format_market_type(market_type: int | None) -> str:
    """Format market type consistently."""
    if market_type == 0:
        return "Binary"
    elif market_type == 1:
        return "Categorical"
    else:
        return DefaultValues.TYPE_FALLBACK


def format_status(status_enum: str | None, status: int | None) -> str:
    """Format status consistently."""
    if status_enum:
        return status_enum
    elif status:
        return f"Status {status}"
    else:
        return DefaultValues.STATUS_FALLBACK


def format_id(market_id: Any, max_length: int = DisplayConstants.MAX_ID_LENGTH) -> str:
    """Format market ID consistently."""
    id_str = str(market_id)
    if len(id_str) > max_length:
        return id_str[:max_length] + "..."
    return id_str


def format_volume(volume: float) -> str:
    """Format volume as currency string."""
    safe_volume = DataSanitizer.safe_float(volume, DefaultValues.VOLUME_FALLBACK)
    return f"${safe_volume:,.{DisplayConstants.VOLUME_PRECISION}f}"


def format_percentage(price: float) -> str:
    """Format price as percentage."""
    safe_price = DataSanitizer.safe_float(price, DefaultValues.PERCENTAGE_FALLBACK)
    percentage = safe_price * 100
    return f"{percentage:.{DisplayConstants.PERCENTAGE_PRECISION}f}%"


def format_price_with_percentage(price: float | None) -> str:
    """Format price with percentage if available."""
    if price is None:
        return ""

    safe_percentage = DataSanitizer.safe_percentage(
        price, DefaultValues.PERCENTAGE_FALLBACK
    )
    return f"{safe_percentage:.{DisplayConstants.PERCENTAGE_PRECISION}f}%"


def format_currency(
    amount: float, precision: int = DisplayConstants.VOLUME_PRECISION
) -> str:
    """Format amount as currency with specified precision."""
    safe_amount = DataSanitizer.safe_float(amount, DefaultValues.VOLUME_FALLBACK)
    return f"${safe_amount:,.{precision}f}"


def format_number(number: float, precision: int = 2) -> str:
    """Format number with specified precision."""
    safe_number = DataSanitizer.safe_float(number, 0.0)
    return f"{safe_number:,.{precision}f}"


def format_color_text(text: str, color: str) -> str:
    """Format text with Rich color markup."""
    colors = DisplayConstants.COLORS
    color_name = colors.get(color, color)
    return f"[{color_name}]{text}[/{color_name}]"


def format_success_text(text: str) -> str:
    """Format text as success message."""
    return format_color_text(text, "success")


def format_error_text(text: str) -> str:
    """Format text as error message."""
    return format_color_text(text, "error")


def format_warning_text(text: str) -> str:
    """Format text as warning message."""
    return format_color_text(text, "warning")


def format_info_text(text: str) -> str:
    """Format text as info message."""
    return format_color_text(text, "info")
