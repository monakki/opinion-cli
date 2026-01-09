# Opinion CLI

[![GitHub Repository](https://img.shields.io/badge/GitHub-monakki%2Fopinion--cli-blue?logo=github)](https://github.com/monakki/opinion-cli)
[![Python](https://img.shields.io/badge/Python-3.14+-blue?logo=python)](https://python.org)
[![uv](https://img.shields.io/badge/uv-package%20manager-orange?logo=python)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Support](https://img.shields.io/badge/Support-BSC%2FEVM-yellow?logo=binance)](https://github.com/monakki/opinion-cli#support-the-project)

**Powerful command line interface for Opinion prediction market**

Monitor markets, analyze positions, track trades, and manage your portfolio with ease. Get real-time insights into any user's trading activity by wallet address, view your own balances and orders, with upcoming trading features to open/close positions and manage orders.

## Features

✅ **Market Analysis** - Browse and analyze prediction markets with advanced filtering and search  
✅ **Market Search** - Find markets by title with smart auto-detection
✅ **Portfolio Tracking** - View positions and trades for any wallet address  
✅ **Personal Dashboard** - Check your balances and manage your orders  
✅ **Real-time Data** - Live market data with automatic pagination  
🚧 **Trading Functions** - Open/close positions, cancel orders *(coming soon)*

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
uv run markets --help
uv run balance --help
uv run positions --help
uv run orders --help
uv run trades --help
```

### Configuration Commands

Show current configuration and test connection:
```bash
uv run config
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

#### Market Search

Search markets by title with automatic detection - simply provide search text as argument:

```bash
# Search for markets containing "bitcoin" (searches all available markets)
uv run markets bitcoin

# Search for markets with "AI prediction" 
uv run markets "AI prediction"

# Search with filters - search "crypto" in resolved markets only
uv run markets crypto -s resolved

# Search in binary markets only
uv run markets ethereum -t 0

# Limit search to first 100 markets (faster)
uv run markets bitcoin -l 100

# Explicit search option (same as above)
uv run markets --search bitcoin
uv run markets -q "AI prediction"
```

**Search Features:**
- **Unlimited by default**: Searches through all available markets
- **Case-insensitive**: "Bitcoin", "bitcoin", "BITCOIN" all work the same
- **Partial matching**: "bit" will find "Bitcoin" markets
- **Child market search**: Also searches titles of categorical market options

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

### Balance Commands

Show user's token balances:
```bash
# Table format (default) - beautiful Rich tables
uv run balance

# JSON format
uv run balance --json
uv run balance -j
```

### Positions Commands

Show user's positions (portfolio) for a specific wallet address:
```bash
# Show positions for specific wallet (default: 20 positions)
uv run positions 0x1234567890abcdef1234567890abcdef12345678

# Show positions using environment variable
WALLET_ADDRESS=0x1234...abcd uv run positions

# Show positions using private key (address will be derived automatically)
PRIVATE_KEY=0x1234...abcd uv run positions

# Show fewer positions per page
uv run positions 0x1234...abcd --limit 10

# Show many positions (up to 1000)
uv run positions 0x1234...abcd --limit 100

# Filter by specific market
uv run positions 0x1234...abcd --market-id 217

# Navigate through pages
uv run positions 0x1234...abcd --page 2 --limit 20

# JSON format
uv run positions 0x1234...abcd --json
uv run positions 0x1234...abcd -j
```

**Wallet Address Priority:**
1. Command argument (highest priority)
2. Derived from `PRIVATE_KEY` environment variable
3. `WALLET_ADDRESS` environment variable (lowest priority)

**Note**: Positions command requires only `API_KEY` environment variable.

### Orders Commands

Show user's orders with optional filters:
```bash
# Show ALL open orders (auto-paginated, up to 1000)
uv run orders

# Show all orders (auto-paginated, up to 20)
uv run orders --status all

# Show filled orders (auto-paginated, up to 20)
uv run orders --status filled

# Show cancelled orders (auto-paginated, up to 20)
uv run orders --status cancelled

# Show ALL open orders for specific market
uv run orders --market-id 217

# Limit maximum orders shown
uv run orders --limit 50

# Disable auto-pagination (use manual pagination)
uv run orders --no-auto-paginate

# Manual pagination (when auto-pagination is disabled)
uv run orders --no-auto-paginate --page 2 --limit 10

# JSON format
uv run orders --json
uv run orders -j
```

**Filter Options:**
- `--market-id` / `-m`: Filter by market ID (0 = all markets)
- `--status` / `-s`: Filter by status (open, pending, filled, completed, cancelled, canceled, all)
- `--limit` / `-l`: Maximum number of orders (default: 1000 for open orders, 20 for others)
- `--page` / `-p`: Page number (only used with --no-auto-paginate)
- `--no-auto-paginate`: Disable automatic pagination (use manual pagination)
- `--json` / `-j`: Output in JSON format

**Status Values:**
- `open` or `pending`: Active orders waiting to be filled (default, auto-paginated up to 1000)
- `filled` or `completed`: Successfully executed orders (auto-paginated up to 20)
- `cancelled` or `canceled`: Cancelled orders (auto-paginated up to 20)
- `all`: Show all orders regardless of status (auto-paginated up to 20)

**Auto-Pagination:**
- Automatically fetches multiple pages to show all orders up to the limit
- Open orders: default limit 1000 (to show all active orders)
- Other statuses: default limit 20 (for better performance)
- Use `--no-auto-paginate` to disable and use manual pagination instead

**Note**: Orders command requires both `API_KEY` and `PRIVATE_KEY` environment variables.

### Trades Commands

Show user's trade history for a specific wallet address:
```bash
# Show trades for specific wallet (default: 20 trades)
uv run trades 0x1234567890abcdef1234567890abcdef12345678

# Show trades using environment variable
WALLET_ADDRESS=0x1234...abcd uv run trades

# Show trades using private key (address will be derived automatically)
PRIVATE_KEY=0x1234...abcd uv run trades

# Show fewer trades per page
uv run trades 0x1234...abcd --limit 10

# Show many trades (up to 1000, with automatic pagination)
uv run trades 0x1234...abcd --limit 100

# Filter by specific market
uv run trades 0x1234...abcd --market-id 217

# Filter by chain ID
uv run trades 0x1234...abcd --chain-id 56

# Navigate through pages
uv run trades 0x1234...abcd --page 2 --limit 20

# JSON format
uv run trades 0x1234...abcd --json
uv run trades 0x1234...abcd -j
```

**Features:**
- **Automatic Pagination**: When requesting more than 20 trades, the command automatically fetches multiple pages
- **Trade History**: Shows only filled (successful) trades, sorted by creation time (descending)
- **Market Context**: Displays both market title and root market title for better context
- **Comprehensive Data**: Shows side (Buy/Sell), outcome, price, shares, amount, and status

**Wallet Address Priority:**
1. Command argument (highest priority)
2. Derived from `PRIVATE_KEY` environment variable
3. `WALLET_ADDRESS` environment variable (lowest priority)

**Note**: Trades command requires only `API_KEY` environment variable.

## Project Structure

```
opinion-cli/
├── clients/                   # Opinion API clients and data models
├── commands/                  # CLI commands (config, balance, positions, trades, markets, help)
├── config/                    # Configuration management and constants
├── display/                   # Display formatting and output (tables, JSON, etc.)
├── utils/                     # Utilities (logging, exceptions, wallet helpers)
├── cli.py                     # CLI entry point and command routing
├── .env.example               # Environment variables template
└── pyproject.toml             # Project configuration and dependencies
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | Yes | - | Opinion API key (required for all operations) |
| `RPC_URL` | Trading only | - | Blockchain RPC URL |
| `PRIVATE_KEY` | Trading only | - | Private key for transactions |
| `MULTI_SIG_ADDRESS` | Trading only | - | Multi-signature wallet address |
| `WALLET_ADDRESS` | No | - | Default wallet address for positions command |
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
- **Capabilities**: View markets, orders, positions, and user portfolios
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