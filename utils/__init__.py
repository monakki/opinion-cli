"""Utilities module for Opinion CLI."""

from .exceptions import (
    OpinionCliError,
    ConfigurationError,
    ConnectionError,
    AuthenticationError,
)

__all__ = [
    "OpinionCliError",
    "ConfigurationError",
    "ConnectionError",
    "AuthenticationError",
]
