"""Output formatting utilities for Opinion CLI."""

from typing import Dict, Any, List
import json


def format_config_info(config_info: Dict[str, Any]) -> str:
    """Format configuration information for display."""
    output = ["📋 Opinion CLI Configuration:"]
    output.append("=" * 40)

    # Connection settings
    output.append(f"🌐 Host: {config_info['host']}")
    output.append(f"⛓️  Chain ID: {config_info['chain_id']}")
    output.append(f"📦 Multi-sig Address: {config_info['multi_sig_address']}")

    output.append("")

    # Mode indicator
    if config_info["read_only_mode"]:
        output.append("📖 Mode: READ-ONLY")
        output.append("   └─ Can view markets, orders, and positions")
    else:
        output.append("💰 Mode: FULL ACCESS")
        output.append("   └─ Can view and place orders/trades")

    output.append("")
    output.append("⚙️  Real-time Monitoring Settings:")

    # Real-time mode is always enabled (no caching by default)
    if config_info["realtime_mode"]:
        output.append("🔴 Real-time Mode: ENABLED (No caching)")
        output.append("   ├─ Market Cache TTL: 0s (disabled)")
        output.append("   ├─ Quote Tokens Cache TTL: 0s (disabled)")
        output.append("   └─ Trading Check Interval: 0s (disabled)")
    else:
        output.append("🟢 Cached Mode: ENABLED")
        output.append(f"   ├─ Market Cache TTL: {config_info['market_cache_ttl']}s")
        output.append(
            f"   ├─ Quote Tokens Cache TTL: {config_info['quote_tokens_cache_ttl']}s"
        )
        output.append(
            f"   └─ Trading Check Interval: {config_info['enable_trading_check_interval']}s"
        )

    output.append("")
    output.append("🔐 Credentials Status:")

    # Credentials status
    status_icon = "✅" if config_info["api_key_set"] else "❌"
    output.append(
        f"  {status_icon} API Key: {'Set' if config_info['api_key_set'] else 'Not set'}"
    )

    status_icon = "✅" if config_info["rpc_url_set"] else "⚠️"
    status_text = "Set" if config_info["rpc_url_set"] else "Not set (read-only mode)"
    output.append(f"  {status_icon} RPC URL: {status_text}")

    status_icon = "✅" if config_info["private_key_set"] else "⚠️"
    status_text = (
        "Set" if config_info["private_key_set"] else "Not set (read-only mode)"
    )
    output.append(f"  {status_icon} Private Key: {status_text}")

    return "\n".join(output)


def format_connection_test(result: Dict[str, Any]) -> str:
    """Format connection test result for display."""
    if result["status"] == "success":
        output = ["✅ Connection Test: SUCCESS"]
        output.append(f"📊 Markets available: {result.get('markets_count', 'Unknown')}")
        output.append(f"💬 {result['message']}")
    else:
        output = ["❌ Connection Test: FAILED"]
        output.append(f"💬 {result['message']}")

    return "\n".join(output)


def format_json(data: Any, indent: int = 2) -> str:
    """Format data as pretty JSON."""
    return json.dumps(data, indent=indent, ensure_ascii=False)


def format_table(headers: List[str], rows: List[List[str]]) -> str:
    """Format data as a simple table."""
    if not rows:
        return "No data to display"

    # Calculate column widths
    col_widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Create format string
    format_str = " | ".join(f"{{:<{width}}}" for width in col_widths)

    # Build table
    output = []
    output.append(format_str.format(*headers))
    output.append("-" * (sum(col_widths) + 3 * (len(headers) - 1)))

    for row in rows:
        formatted_row = [str(cell) for cell in row]
        output.append(format_str.format(*formatted_row))

    return "\n".join(output)
