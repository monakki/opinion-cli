"""Custom exceptions for Opinion CLI."""


class OpinionCliError(Exception):
    """Base exception for Opinion CLI."""

    pass


class ConfigurationError(OpinionCliError):
    """Raised when configuration is invalid."""

    pass


class ConnectionError(OpinionCliError):
    """Raised when connection to Opinion API fails."""

    pass


class AuthenticationError(OpinionCliError):
    """Raised when authentication fails."""

    pass
