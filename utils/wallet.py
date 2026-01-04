"""Wallet utilities for Opinion CLI."""

from typing import Optional


def get_wallet_address_from_private_key(private_key: str) -> Optional[str]:
    """
    Get wallet address from private key.

    This is a placeholder implementation. In a real implementation,
    you would use a library like web3.py or eth_account to derive
    the address from the private key.

    Args:
        private_key: The private key string

    Returns:
        The wallet address or None if derivation fails
    """
    try:
        # For now, we'll try to use web3 if available
        try:
            from eth_account import Account

            # Remove '0x' prefix if present
            if private_key.startswith("0x"):
                private_key = private_key[2:]

            # Create account from private key
            account = Account.from_key(private_key)
            return account.address

        except ImportError:
            # If web3/eth_account not available, return None
            # The caller should handle this case
            return None

    except Exception:
        return None


def get_wallet_address(
    wallet_address_arg: Optional[str] = None,
    private_key_env: Optional[str] = None,
    wallet_address_env: Optional[str] = None,
) -> Optional[str]:
    """
    Get wallet address from multiple sources in priority order:
    1. Direct argument
    2. Derived from private key
    3. Environment variable

    Args:
        wallet_address_arg: Wallet address from command argument
        private_key_env: Private key from environment
        wallet_address_env: Wallet address from environment

    Returns:
        The wallet address or None if not found
    """
    # Priority 1: Direct argument
    if wallet_address_arg:
        return wallet_address_arg.strip()

    # Priority 2: Derive from private key
    if (
        private_key_env
        and private_key_env
        != "0x0000000000000000000000000000000000000000000000000000000000000000"
    ):
        derived_address = get_wallet_address_from_private_key(private_key_env)
        if derived_address:
            return derived_address

    # Priority 3: Environment variable
    if wallet_address_env:
        return wallet_address_env.strip()

    return None
