"""Data models for Opinion Trade API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class ChildMarket(BaseModel):
    """Child market data model."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    market_id: str | int = Field(alias="marketId")
    market_title: str = Field(alias="marketTitle")
    status: int | None = None
    status_enum: str | None = Field(None, alias="statusEnum")
    yes_label: str | None = Field(None, alias="yesLabel")
    no_label: str | None = Field(None, alias="noLabel")
    rules: str | None = None
    yes_token_id: str | None = Field(None, alias="yesTokenId")
    no_token_id: str | None = Field(None, alias="noTokenId")
    condition_id: str | None = Field(None, alias="conditionId")
    result_token_id: str | None = Field(None, alias="resultTokenId")
    volume: str | None = None
    quote_token: str | None = Field(None, alias="quoteToken")
    chain_id: str | None = Field(None, alias="chainId")
    question_id: str | None = Field(None, alias="questionId")
    created_at: datetime | str | int | None = Field(None, alias="createdAt")
    cutoff_at: datetime | str | int | None = Field(None, alias="cutoffAt")
    resolved_at: datetime | str | int | None = Field(None, alias="resolvedAt")


class Market(BaseModel):
    """Market data model."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    market_id: str | int = Field(alias="marketId")
    market_title: str = Field(alias="marketTitle")
    status: int | None = None
    status_enum: str | None = Field(None, alias="statusEnum")
    market_type: int | None = Field(None, alias="marketType")
    child_markets: list[ChildMarket] | None = Field(None, alias="childMarkets")
    yes_label: str | None = Field(None, alias="yesLabel")
    no_label: str | None = Field(None, alias="noLabel")
    rules: str | None = None
    yes_token_id: str | None = Field(None, alias="yesTokenId")
    no_token_id: str | None = Field(None, alias="noTokenId")
    condition_id: str | None = Field(None, alias="conditionId")
    result_token_id: str | None = Field(None, alias="resultTokenId")
    volume: str | None = None
    volume_24h: str | None = Field(None, alias="volume24h")
    volume_7d: str | None = Field(None, alias="volume7d")
    quote_token: str | None = Field(None, alias="quoteToken")
    chain_id: str | None = Field(None, alias="chainId")
    question_id: str | None = Field(None, alias="questionId")
    incentive_factor: dict[str, Any] | None = Field(None, alias="incentiveFactor")
    created_at: datetime | str | int | None = Field(None, alias="createdAt")
    cutoff_at: datetime | str | int | None = Field(None, alias="cutoffAt")
    resolved_at: datetime | str | int | None = Field(None, alias="resolvedAt")

    @field_validator("market_id", mode="before")
    @classmethod
    def convert_id_to_string(cls, v):
        """Convert ID to string."""
        return str(v) if v is not None else None

    @field_validator("created_at", "cutoff_at", "resolved_at", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime from various formats."""
        if v is None or v == 0:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, (int, float)):
            # Assume timestamp
            return datetime.fromtimestamp(v)
        if isinstance(v, str):
            # Try to parse ISO format
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return v
        return v

    def get_volume_float(self, volume_str: str | None) -> float:
        """Parse volume from string to float."""
        if volume_str is None:
            return 0.0
        if isinstance(volume_str, (int, float)):
            return float(volume_str)
        if isinstance(volume_str, str):
            try:
                return float(volume_str)
            except ValueError:
                return 0.0
        return 0.0

    @property
    def id(self) -> str:
        """Alias for market_id for backward compatibility."""
        return str(self.market_id)

    @property
    def title(self) -> str:
        """Alias for market_title for backward compatibility."""
        return self.market_title

    @property
    def description(self) -> str | None:
        """Alias for rules for backward compatibility."""
        return self.rules

    @property
    def total_volume(self) -> float:
        """Get total volume as float."""
        return self.get_volume_float(self.volume)

    @property
    def volume_24h_float(self) -> float:
        """Get 24h volume as float."""
        return self.get_volume_float(self.volume_24h)

    @property
    def volume_7d_float(self) -> float:
        """Get 7d volume as float."""
        return self.get_volume_float(self.volume_7d)


class APIResponse(BaseModel):
    """Base API response model."""

    code: int
    msg: str
    result: dict[str, Any] | None = None


class MarketListResponse(BaseModel):
    """Response model for market list API."""

    code: int
    msg: str
    result: dict[str, Any]

    @property
    def markets(self) -> list[Market]:
        """Extract markets from result."""
        if not self.result or "list" not in self.result:
            return []

        markets = []
        for market_data in self.result["list"]:
            try:
                market = Market(**market_data)
                markets.append(market)
            except Exception as e:
                # Log the exception for debugging
                from loguru import logger

                logger.warning(f"Failed to parse market data: {e}")
                continue
        return markets

    @property
    def total(self) -> int:
        """Get total count."""
        return self.result.get("total", 0) if self.result else 0


class ClaimStatus(int, Enum):
    """Claim status enumeration."""

    CAN_NOT_CLAIM = 0
    CAN_CLAIM = 1
    CLAIMED = 2


class OutcomeSide(int, Enum):
    """Outcome side enumeration."""

    YES = 1
    NO = 0


class TradeStatus(int, Enum):
    """Trade status enumeration."""

    PENDING = 1
    FILLED = 2
    CANCELLED = 3


class Position(BaseModel):
    """User position data model."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    market_id: int = Field(alias="marketId")
    market_title: str = Field(alias="marketTitle")
    market_status: int = Field(alias="marketStatus")
    market_status_enum: str = Field(alias="marketStatusEnum")
    market_cutoff_at: int = Field(alias="marketCutoffAt")
    root_market_id: int = Field(alias="rootMarketId")
    root_market_title: str = Field(alias="rootMarketTitle")
    outcome: str
    outcome_side: int = Field(alias="outcomeSide")
    outcome_side_enum: str = Field(alias="outcomeSideEnum")
    shares_owned: str = Field(alias="sharesOwned")
    shares_frozen: str = Field(alias="sharesFrozen")
    unrealized_pnl: str = Field(alias="unrealizedPnl")
    unrealized_pnl_percent: str = Field(alias="unrealizedPnlPercent")
    daily_pnl_change: str = Field(alias="dailyPnlChange")
    daily_pnl_change_percent: str = Field(alias="dailyPnlChangePercent")
    condition_id: str = Field(alias="conditionId")
    token_id: str = Field(alias="tokenId")
    current_value_in_quote_token: str = Field(alias="currentValueInQuoteToken")
    avg_entry_price: str = Field(alias="avgEntryPrice")
    claim_status: int = Field(alias="claimStatus")
    claim_status_enum: str = Field(alias="claimStatusEnum")
    quote_token: str = Field(alias="quoteToken")

    def get_shares_owned_float(self) -> float:
        """Parse shares owned from string to float."""
        try:
            return float(self.shares_owned)
        except (ValueError, TypeError):
            return 0.0

    def get_unrealized_pnl_float(self) -> float:
        """Parse unrealized PnL from string to float."""
        try:
            return float(self.unrealized_pnl)
        except (ValueError, TypeError):
            return 0.0

    def get_current_value_float(self) -> float:
        """Parse current value from string to float."""
        try:
            return float(self.current_value_in_quote_token)
        except (ValueError, TypeError):
            return 0.0


class PositionsResponse(BaseModel):
    """Response model for user positions API."""

    code: int
    msg: str
    result: dict[str, Any]

    @property
    def positions(self) -> list[Position]:
        """Extract positions from result."""
        if not self.result or "list" not in self.result:
            return []

        positions = []
        for position_data in self.result["list"]:
            try:
                position = Position(**position_data)
                positions.append(position)
            except Exception as e:
                # Log the exception for debugging
                from loguru import logger

                logger.warning(f"Failed to parse position data: {e}")
                continue
        return positions

    @property
    def total(self) -> int:
        """Get total count."""
        return self.result.get("total", 0) if self.result else 0


class Trade(BaseModel):
    """User trade data model."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    tx_hash: str = Field(alias="txHash")
    market_id: int = Field(alias="marketId")
    market_title: str = Field(alias="marketTitle")
    root_market_id: int = Field(alias="rootMarketId")
    root_market_title: str = Field(alias="rootMarketTitle")
    side: str
    outcome: str
    outcome_side: int = Field(alias="outcomeSide")
    outcome_side_enum: str = Field(alias="outcomeSideEnum")
    price: str
    shares: str
    amount: str
    fee: str
    profit: str
    quote_token: str = Field(alias="quoteToken")
    quote_token_usd_price: str = Field(alias="quoteTokenUsdPrice")
    usd_amount: str = Field(alias="usdAmount")
    status: int
    status_enum: str = Field(alias="statusEnum")
    chain_id: str = Field(alias="chainId")
    created_at: datetime | str | int = Field(alias="createdAt")

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime from various formats."""
        if v is None or v == 0:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, (int, float)):
            # Assume timestamp
            return datetime.fromtimestamp(v)
        if isinstance(v, str):
            # Try to parse ISO format
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return v
        return v

    def get_price_float(self) -> float:
        """Parse price from string to float."""
        try:
            return float(self.price)
        except (ValueError, TypeError):
            return 0.0

    def get_shares_float(self) -> float:
        """Parse shares from string to float."""
        try:
            return float(self.shares)
        except (ValueError, TypeError):
            return 0.0

    def get_amount_float(self) -> float:
        """Parse amount from string to float."""
        try:
            return float(self.amount)
        except (ValueError, TypeError):
            return 0.0

    def get_fee_float(self) -> float:
        """Parse fee from string to float."""
        try:
            return float(self.fee)
        except (ValueError, TypeError):
            return 0.0

    def get_profit_float(self) -> float:
        """Parse profit from string to float."""
        try:
            return float(self.profit)
        except (ValueError, TypeError):
            return 0.0

    def get_usd_amount_float(self) -> float:
        """Parse USD amount from string to float."""
        try:
            return float(self.usd_amount)
        except (ValueError, TypeError):
            return 0.0


class TradesResponse(BaseModel):
    """Response model for user trades API."""

    code: int
    msg: str
    result: dict[str, Any]

    @property
    def trades(self) -> list[Trade]:
        """Extract trades from result."""
        if not self.result or "list" not in self.result:
            return []

        trades = []
        for trade_data in self.result["list"]:
            try:
                trade = Trade(**trade_data)
                trades.append(trade)
            except Exception as e:
                # Log the exception for debugging
                from loguru import logger

                logger.warning(f"Failed to parse trade data: {e}")
                continue
        return trades

    @property
    def total(self) -> int:
        """Get total count."""
        return self.result.get("total", 0) if self.result else 0


class APIError(BaseModel):
    """API error response model."""

    error: str
    message: str
    code: int | None = None
