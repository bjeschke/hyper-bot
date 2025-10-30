"""Configuration management for the trading bot."""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class HyperliquidConfig:
    """Hyperliquid API configuration (Wallet-based)."""

    wallet_address: str
    private_key: str
    testnet: bool = True
    base_url: str = "https://api.hyperliquid.xyz"
    testnet_url: str = "https://api.hyperliquid-testnet.xyz"

    @property
    def url(self) -> str:
        """Get the appropriate URL based on testnet flag."""
        return self.testnet_url if self.testnet else self.base_url


@dataclass
class DeepSeekConfig:
    """DeepSeek API configuration."""

    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 0.1  # Low temperature for consistent trading decisions
    max_tokens: int = 1500  # Reduced for token efficiency


@dataclass
class CopyTradingConfig:
    """Copy trading configuration."""

    enabled: bool = False
    copy_wallets: list = None  # List of wallet addresses to copy
    position_multiplier: float = 1.0  # Scale factor for copied positions
    copy_only_assets: list = None  # Only copy trades for these assets


@dataclass
class TradingConfig:
    """Trading strategy configuration."""

    # Multi-asset support
    trading_assets: list = None  # List of assets to trade
    default_asset: str = "BTC"

    max_position_size: float = 10000.0  # Per asset
    risk_per_trade: float = 0.02  # 2%
    max_exposure: float = 0.7  # 70% across all assets
    trading_interval: int = 300  # 5 minutes
    min_confidence: float = 0.6
    min_confluence_score: int = 4

    # Leverage limits
    btc_eth_max_leverage: int = 10
    large_cap_max_leverage: int = 5
    small_cap_max_leverage: int = 3

    # Stop loss / take profit
    stop_loss_percent: float = 0.05  # Base 5%, will be dynamic
    take_profit_percent: float = 0.08
    min_risk_reward: float = 2.0

    # Liquidity requirements
    min_volume_24h: float = 1_000_000.0
    min_orderbook_depth: float = 50_000.0
    max_spread_bps: float = 10.0
    max_slippage: float = 0.005  # 0.5%

    # Drawdown limits
    daily_loss_limit: float = 0.05
    weekly_loss_limit: float = 0.10
    max_drawdown_threshold: float = 0.20

    # Timeframes for analysis
    timeframes: list = None

    def __post_init__(self):
        if self.timeframes is None:
            self.timeframes = ["1m", "5m", "15m", "1h", "4h", "24h"]


@dataclass
class RiskConfig:
    """Risk management configuration."""

    max_daily_trades: int = 10
    max_concurrent_positions: int = 3
    min_margin_ratio: float = 0.30
    liquidation_buffer: float = 0.15  # 15% from liquidation

    # Correlation limits
    max_correlated_positions: int = 2
    correlation_threshold: float = 0.7


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = "sqlite:///./trading_bot.db"
    echo: bool = False


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    log_file: str = "logs/trading_bot.log"
    log_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    rotation: str = "100 MB"
    retention: str = "30 days"


@dataclass
class VisionConfig:
    """Vision AI configuration (for YouTube livestream analysis)."""

    provider: str = "openai"  # openai, anthropic, gemini
    api_key: str = ""
    model: str = "gpt-4-vision-preview"


@dataclass
class YouTubeLivestreamConfig:
    """YouTube livestream monitoring configuration."""

    enabled: bool = False
    url: str = ""
    capture_interval: int = 60  # Seconds
    signal_weight: float = 0.3  # How much to weight livestream signals (0-1)


class Config:
    """Main configuration class."""

    def __init__(self):
        self.hyperliquid = HyperliquidConfig(
            wallet_address=os.getenv("HYPERLIQUID_WALLET_ADDRESS", ""),
            private_key=os.getenv("HYPERLIQUID_PRIVATE_KEY", ""),
            testnet=os.getenv("HYPERLIQUID_TESTNET", "true").lower() == "true"
        )

        self.deepseek = DeepSeekConfig(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        )

        # Parse trading assets (comma-separated list)
        trading_assets_str = os.getenv("TRADING_ASSETS", "")
        trading_assets = None
        if trading_assets_str:
            trading_assets = [asset.strip() for asset in trading_assets_str.split(",") if asset.strip()]

        self.trading = TradingConfig(
            trading_assets=trading_assets,
            default_asset=os.getenv("DEFAULT_ASSET", "BTC"),
            max_position_size=float(os.getenv("MAX_POSITION_SIZE", "10000")),
            risk_per_trade=float(os.getenv("RISK_PER_TRADE", "0.02")),
            max_exposure=float(os.getenv("MAX_EXPOSURE", "0.7")),
            trading_interval=int(os.getenv("TRADING_INTERVAL", "300")),
            min_confidence=float(os.getenv("MIN_CONFIDENCE", "0.6")),
            stop_loss_percent=float(os.getenv("STOP_LOSS_PERCENT", "0.05")),
            take_profit_percent=float(os.getenv("TAKE_PROFIT_PERCENT", "0.08")),
            min_volume_24h=float(os.getenv("MIN_LIQUIDITY", "1000000"))
        )

        # Parse copy trading wallets (comma-separated list)
        copy_wallets_str = os.getenv("COPY_WALLETS", "")
        copy_wallets = None
        if copy_wallets_str:
            copy_wallets = [wallet.strip() for wallet in copy_wallets_str.split(",") if wallet.strip()]

        copy_only_assets_str = os.getenv("COPY_ONLY_ASSETS", "")
        copy_only_assets = None
        if copy_only_assets_str:
            copy_only_assets = [asset.strip() for asset in copy_only_assets_str.split(",") if asset.strip()]

        self.copy_trading = CopyTradingConfig(
            enabled=os.getenv("COPY_TRADING_ENABLED", "false").lower() == "true",
            copy_wallets=copy_wallets,
            position_multiplier=float(os.getenv("COPY_POSITION_MULTIPLIER", "1.0")),
            copy_only_assets=copy_only_assets
        )

        self.risk = RiskConfig(
            max_daily_trades=int(os.getenv("MAX_DAILY_TRADES", "10")),
            max_concurrent_positions=int(os.getenv("MAX_CONCURRENT_POSITIONS", "3"))
        )

        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///./trading_bot.db"),
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"
        )

        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "logs/trading_bot.log")
        )

        self.vision = VisionConfig(
            provider=os.getenv("VISION_PROVIDER", "openai"),
            api_key=os.getenv("OPENAI_API_KEY", "")
        )

        self.youtube_livestream = YouTubeLivestreamConfig(
            enabled=os.getenv("YOUTUBE_LIVESTREAM_ENABLED", "false").lower() == "true",
            url=os.getenv("YOUTUBE_LIVESTREAM_URL", ""),
            capture_interval=int(os.getenv("YOUTUBE_CAPTURE_INTERVAL", "60"))
        )

    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration and return errors if any."""
        errors = []

        if not self.hyperliquid.wallet_address:
            errors.append("HYPERLIQUID_WALLET_ADDRESS is required")

        if not self.hyperliquid.private_key:
            errors.append("HYPERLIQUID_PRIVATE_KEY is required")

        if not self.deepseek.api_key:
            errors.append("DEEPSEEK_API_KEY is required")

        if self.trading.risk_per_trade <= 0 or self.trading.risk_per_trade > 0.05:
            errors.append("RISK_PER_TRADE must be between 0 and 0.05 (5%)")

        if self.trading.min_confidence < 0 or self.trading.min_confidence > 1:
            errors.append("MIN_CONFIDENCE must be between 0 and 1")

        return len(errors) == 0, errors


# Global config instance
config = Config()
