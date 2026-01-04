# Opinion CLI

Command line interface for Opinion prediction market.

[![GitHub Repository](https://img.shields.io/badge/GitHub-monakki%2Fopinion--cli-blue?logo=github)](https://github.com/monakki/opinion-cli)
[![Python](https://img.shields.io/badge/Python-3.14+-blue?logo=python)](https://python.org)
[![uv](https://img.shields.io/badge/uv-package%20manager-orange?logo=python)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Support](https://img.shields.io/badge/Support-BSC%2FEVM-yellow?logo=binance)](https://github.com/monakki/opinion-cli#support-the-project)

## Prerequisites

This project uses [uv](https://docs.astral.sh/uv/) - a fast Python package manager and project manager written in Rust.

### Install uv

**macOS and Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

For more installation options, see the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

## Installation

### Option 1: Clone via HTTPS
```bash
# Clone the repository
git clone https://github.com/monakki/opinion-cli.git
cd opinion-cli

# Install dependencies and create virtual environment
uv sync
```

### Option 2: Clone via SSH
```bash
# Clone the repository
git clone git@github.com:monakki/opinion-cli.git
cd opinion-cli

# Install dependencies and create virtual environment
uv sync
```

> **Note**: `uv sync` will automatically:
> - Create a virtual environment if it doesn't exist
> - Install all project dependencies
> - Install the project in editable mode
> - Make CLI commands available via `uv run`

## Configuration

The CLI supports two modes of operation:

### 1. Read-Only Mode (Minimal Configuration)
For viewing markets, orders, and positions only:

```bash
# Create .env file with minimal configuration
echo "API_KEY=your_actual_api_key" > .env
```

### 2. Full Access Mode (Complete Configuration)
For viewing and placing orders/trades:

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` file with your actual credentials:
```bash
# Required: Opinion API key
API_KEY=your_actual_api_key

# Required for trading: Blockchain RPC URL
RPC_URL=https://bsc-dataseed.binance.org/

# Required for trading: Your private key for transactions
PRIVATE_KEY=your_actual_private_key

# Required for trading: Multi-signature wallet address
MULTI_SIG_ADDRESS=your_actual_multisig_address
```

**Where to get credentials:**
- **API_KEY**: Follow the [Opinion Developer Guide](https://docs.opinion.trade/developer-guide/opinion-clob-sdk/getting-started/quick-start#prerequisites)
- **MULTI_SIG_ADDRESS**: Check your Opinion platform "My Profile" section
- **PRIVATE_KEY**: Your wallet's private key (keep this secure!)
- **RPC_URL**: BSC RPC endpoint (example: `https://bsc-dataseed.binance.org/`)

## Usage

### Help Commands

Show available commands and general help:
```bash
uv run help
```

Get detailed help for specific commands:
```bash
uv run config --help
uv run balance --help
uv run markets --help
```

### Configuration Commands

Show current configuration and test connection:
```bash
uv run config
```

### Balance Commands

Show user's token balances:
```bash
# Table format (default) - beautiful Rich tables
uv run balance

# JSON format
uv run balance --json
uv run balance -j
```

### Markets Commands

Fetch and display markets from Opinion Open API. Supports both numeric market IDs and Opinion Trade URLs from https://app.opinion.trade.

#### Basic Usage

```bash
# Show top 20 markets (default, sorted by 24h volume desc)
uv run markets

# Show specific market by ID
uv run markets 217

# Show market from Opinion Trade URL
uv run markets https://app.opinion.trade/detail?topicId=217
uv run markets "https://app.opinion.trade/detail?topicId=61&type=multi"
```

#### Filtering and Sorting

```bash
# Show different number of markets
uv run markets -l 10                         # or --limit 10
uv run markets --limit 50

# Filter by market status
uv run markets -s activated                  # or --status activated
uv run markets --status resolved

# Filter by market type
uv run markets -t 0                          # or --market-type 0 (Binary)
uv run markets --market-type 1               # Categorical markets
uv run markets -t 2                          # All market types (default)

# Sort markets (--sort-by options)
uv run markets --sort-by 1                   # Sort by newest first
uv run markets --sort-by 2                   # Sort by ending soon
uv run markets --sort-by 3                   # Sort by total volume (desc)
uv run markets --sort-by 5                   # Sort by 24h volume (desc) - default
uv run markets --sort-by 7                   # Sort by 7d volume (desc)
```

#### Combined Filters

```bash
# Top 5 binary markets by total volume
uv run markets -t 0 --sort-by 3 -l 5
uv run markets --market-type 0 --sort-by 3 --limit 5

# Resolved categorical markets, newest first
uv run markets -s resolved -t 1 --sort-by 1

# Active markets ending soon, show 15
uv run markets --status activated --sort-by 2 --limit 15
```

#### Pagination and Output

```bash
# Navigate through pages
uv run markets -p 1 -l 20                    # or --page 1 --limit 20
uv run markets --page 2 --limit 20

# JSON output for programmatic use
uv run markets -j                            # or --json
uv run markets 217 --json                    # Specific market as JSON
uv run markets -l 5 -j                       # Top 5 markets as JSON
```

#### Sort Options Reference

| Option | Description |
|--------|-------------|
| `1` | **new** - Newest markets first |
| `2` | **ending_soon** - Markets ending soonest first |
| `3` | **volume_desc** - Highest total volume first |
| `4` | **volume_asc** - Lowest total volume first |
| `5` | **volume_24h_desc** - Highest 24h volume first (default) |
| `6` | **volume_24h_asc** - Lowest 24h volume first |
| `7` | **volume_7d_desc** - Highest 7d volume first |
| `8` | **volume_7d_asc** - Lowest 7d volume first |

#### Market Type Options

| Option | Description |
|--------|-------------|
| `0` | **Binary** - Yes/No prediction markets |
| `1` | **Categorical** - Multiple choice markets |
| `2` | **All** - All market types (default) |

## Project Structure

```
opinion-cli/
├── clients/                   # Opinion API clients
│   ├── __init__.py
│   ├── models.py             # Pydantic data models
│   ├── opinion_api_client.py # Open API client (async)
│   └── opinion_clob_client.py # CLOB SDK client wrapper
├── commands/                  # CLI commands
│   ├── __init__.py
│   ├── base.py               # Base command functionality
│   ├── config.py             # Configuration commands
│   ├── balance.py            # Balance commands
│   └── help.py               # Help commands
├── config/                   # Configuration management
│   ├── __init__.py
│   ├── constants.py          # All constants and enums
│   ├── settings.py           # Unified OpinionConfig class
│   └── validators.py         # Input validation utilities
├── display/                  # Display and formatting
│   ├── __init__.py
│   ├── formatters.py         # Pure formatting functions
│   ├── json_display.py       # JSON output formatting
│   ├── table_display.py      # Table display functionality
│   ├── market_display.py     # Market-specific display
│   ├── config_display.py     # Configuration display
│   └── balance_display.py    # Balance display
├── utils/                    # Utilities
│   ├── __init__.py
│   ├── exceptions.py         # Custom exceptions
│   └── logging.py            # Logging configuration
├── cli.py                    # CLI entry point
├── .env.example              # Environment variables template
└── pyproject.toml            # Project configuration
```

## Environment Variables

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | Yes | - | Opinion API key (required for all operations) |
| `RPC_URL` | Trading only | - | Blockchain RPC URL |
| `PRIVATE_KEY` | Trading only | - | Private key for transactions |
| `MULTI_SIG_ADDRESS` | Trading only | - | Multi-signature wallet address |
| `CHAIN_ID` | No | 56 | Blockchain chain ID |
| `OPINION_HOST` | No | https://proxy.opinion.trade:8443 | Opinion API host |
| `MARKET_CACHE_TTL` | No | 0 | Market cache TTL in seconds (0 = no caching) |
| `QUOTE_TOKENS_CACHE_TTL` | No | 0 | Quote tokens cache TTL in seconds (0 = no caching) |
| `ENABLE_TRADING_CHECK_INTERVAL` | No | 0 | Trading check interval in seconds (0 = disabled) |
| `RATE_LIMIT` | No | 12 | API requests per second limit |
| `TIMEOUT` | No | 30.0 | Request timeout in seconds |
| `LOG_LEVEL` | No | - | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) - disabled if not set |

## Operating Modes

### Read-Only Mode
- **Requirements**: Only `API_KEY`
- **Capabilities**: View markets, orders, and positions
- **Use case**: Monitoring and analysis without trading

### Full Access Mode  
- **Requirements**: `API_KEY`, `RPC_URL`, `PRIVATE_KEY`, `MULTI_SIG_ADDRESS`
- **Capabilities**: All read-only features plus placing orders and trades
- **Use case**: Complete trading functionality

## Real-time Monitoring

By default, the CLI is configured for real-time monitoring with no caching and rate limiting:
- `MARKET_CACHE_TTL=0` - Markets are fetched fresh every time
- `QUOTE_TOKENS_CACHE_TTL=0` - Quote tokens are fetched fresh every time  
- `ENABLE_TRADING_CHECK_INTERVAL=0` - No trading check delays
- `RATE_LIMIT=12` - Maximum 12 API requests per second
- `TIMEOUT=30.0` - Request timeout of 30 seconds

By default, logging is disabled for clean output. Enable logging by setting `LOG_LEVEL`:
- `LOG_LEVEL=INFO` - Show informational messages
- `LOG_LEVEL=DEBUG` - Show detailed debug information

This ensures you always get the most up-to-date data from the Opinion prediction market while respecting API limits and timeouts.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support the Project

If you find this project helpful, you can support the development:

**Crypto donations (BSC/EVM):**
```
0xdf8f5610481065c071154b17460d459455325fd1
```

*Donations help maintain and improve the project. Thank you for your support!*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Repository

- **GitHub**: [https://github.com/monakki/opinion-cli](https://github.com/monakki/opinion-cli)
- **Issues**: [https://github.com/monakki/opinion-cli/issues](https://github.com/monakki/opinion-cli/issues)
- **Pull Requests**: [https://github.com/monakki/opinion-cli/pulls](https://github.com/monakki/opinion-cli/pulls)