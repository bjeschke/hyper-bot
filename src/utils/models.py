"""Data models for the trading bot."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal
from enum import Enum


class MarketRegime(str, Enum):
    """Market regime types."""

    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    BREAKOUT = "BREAKOUT"
    BREAKDOWN = "BREAKDOWN"


class OrderType(str, Enum):
    """Order types."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    TWAP = "TWAP"
    SCALE_IN = "SCALE_IN"


class OrderSide(str, Enum):
    """Order side."""

    BUY = "BUY"
    SELL = "SELL"
    CLOSE = "CLOSE"


class Decision(str, Enum):
    """Trading decision."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"
    REDUCE_LONG = "REDUCE_LONG"
    REDUCE_SHORT = "REDUCE_SHORT"


class SetupQuality(str, Enum):
    """Setup quality rating."""

    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    NO_SETUP = "NO_SETUP"


@dataclass
class MarketData:
    """Market data for a specific timeframe."""

    asset: str
    timestamp: datetime
    price: float
    mark_price: float
    index_price: float
    volume: float
    high: float
    low: float
    price_change: float
    volatility: Optional[float] = None


@dataclass
class MultiTimeframeData:
    """Market data across multiple timeframes."""

    asset: str
    timestamp: datetime
    current_price: float
    mark_price: float
    index_price: float
    data_1m: Optional[MarketData] = None
    data_5m: Optional[MarketData] = None
    data_15m: Optional[MarketData] = None
    data_1h: Optional[MarketData] = None
    data_4h: Optional[MarketData] = None
    data_24h: Optional[MarketData] = None


@dataclass
class OrderbookData:
    """Orderbook snapshot."""

    bids: list[tuple[float, float]]  # (price, size)
    asks: list[tuple[float, float]]
    bid_liquidity: float
    ask_liquidity: float
    spread_bps: float
    spread_usd: float
    imbalance: float  # Positive = bid pressure
    timestamp: datetime


@dataclass
class MACD:
    """MACD indicator values."""

    value: float
    signal: float
    histogram: float


@dataclass
class BollingerBands:
    """Bollinger Bands values."""

    upper: float
    middle: float
    lower: float
    percent_b: float
    width: float


@dataclass
class TechnicalIndicators:
    """Technical indicators for analysis."""

    # RSI across timeframes
    rsi_5m: Optional[float] = None
    rsi_15m: Optional[float] = None
    rsi_1h: Optional[float] = None
    rsi_4h: Optional[float] = None

    # MACD
    macd: Optional[MACD] = None
    macd_5m: Optional[MACD] = None
    macd_1h: Optional[MACD] = None
    macd_4h: Optional[MACD] = None

    # EMAs
    ema_9: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None

    # Trend indicators
    adx: Optional[float] = None
    plus_di: Optional[float] = None
    minus_di: Optional[float] = None
    supertrend: Optional[float] = None
    supertrend_signal: Optional[str] = None

    # Volatility
    bollinger_bands: Optional[BollingerBands] = None
    atr: Optional[float] = None
    atr_percent: Optional[float] = None
    realized_volatility: Optional[float] = None

    # Volume
    vwap_daily: Optional[float] = None
    vwap_weekly: Optional[float] = None
    cvd: Optional[float] = None
    cvd_trend: Optional[str] = None
    obv: Optional[float] = None
    obv_trend: Optional[str] = None
    volume_ratio: Optional[float] = None


@dataclass
class DerivativesData:
    """Derivatives market data."""

    funding_rate: float
    funding_rate_annual: float
    funding_trend: str
    time_to_funding: int  # minutes
    open_interest: float
    oi_change_24h: float
    oi_trend: str
    long_short_ratio: float
    ratio_interpretation: str
    long_liquidation_cluster: Optional[float] = None
    short_liquidation_cluster: Optional[float] = None


@dataclass
class Position:
    """Trading position."""

    asset: str
    side: Literal["LONG", "SHORT"]
    size: float
    entry_price: float
    current_price: float
    leverage: float
    margin_used: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    liquidation_price: float
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    entry_time: Optional[datetime] = None
    position_id: Optional[str] = None


@dataclass
class Portfolio:
    """Portfolio status."""

    total_value: float
    available_balance: float
    used_margin: float
    margin_usage_percent: float
    exposure_percent: float
    positions: list[Position] = field(default_factory=list)
    realized_pnl_24h: float = 0.0
    unrealized_pnl: float = 0.0


@dataclass
class PerformanceMetrics:
    """Performance metrics."""

    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    current_drawdown: float
    recovery_factor: float
    total_trades: int
    wins: int
    losses: int


@dataclass
class StopLoss:
    """Stop loss details."""

    price: float
    reasoning: str
    distance_pct: float
    dollar_risk: float


@dataclass
class TakeProfitTarget:
    """Take profit target."""

    target: int
    price: float
    percentage_to_close: int
    reasoning: str
    rr_ratio: float


@dataclass
class TrailingStop:
    """Trailing stop configuration."""

    activate_at_rr: float
    trail_at_rr: float
    method: Literal["EMA_20", "SUPERTREND", "ATR_BASED"]


@dataclass
class SuggestedAction:
    """Suggested trading action."""

    type: OrderType
    side: OrderSide
    size_percentage: int
    quantity: float
    entry_price: float
    entry_price_rationale: str
    stop_loss: StopLoss
    take_profit_targets: list[TakeProfitTarget]
    trailing_stop: TrailingStop
    execution_notes: str


@dataclass
class RiskAssessment:
    """Risk assessment details."""

    overall_risk: Literal["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
    risk_factors: list[str]
    edge_quality: float
    risk_reward_ratio: float
    expected_value: float
    position_size_modifier: float
    slippage_estimate: float
    liquidity_check: Literal["PASS", "MARGINAL", "FAIL"]
    funding_impact: float
    margin_safety: float
    liquidation_distance_pct: float


@dataclass
class MarketRegimeData:
    """Market regime information."""

    primary: MarketRegime
    strength: float
    regime_aligned: bool


@dataclass
class ConfluenceAnalysis:
    """Confluence analysis details."""

    trend_score: int
    trend_details: str
    momentum_score: int
    momentum_details: str
    volume_score: int
    volume_details: str
    microstructure_score: int
    microstructure_details: str
    total_confluence: int


@dataclass
class IndicatorsSummary:
    """Summary of indicators."""

    trend: dict
    momentum: dict
    volume: dict
    volatility: dict


@dataclass
class TradingDecision:
    """AI trading decision."""

    decision: Decision
    setup_quality: SetupQuality
    confidence: float
    confluence_score: int
    market_regime: MarketRegimeData
    confluence_analysis: ConfluenceAnalysis
    reasoning: str
    key_factors: dict
    indicators_summary: IndicatorsSummary
    suggested_action: Optional[SuggestedAction]
    risk_assessment: RiskAssessment
    alternative_scenarios: dict
    monitoring_points: list[str]
    meta: dict
    timestamp: datetime = field(default_factory=datetime.now)
