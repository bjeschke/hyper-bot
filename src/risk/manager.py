"""Risk management for the trading bot."""

from typing import Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from src.config import TradingConfig, RiskConfig
from src.utils.models import (
    TradingDecision,
    Portfolio,
    Position,
    Decision,
    MarketRegime,
)


class RiskManager:
    """
    Risk management module for the trading bot.

    Implements:
    - Position sizing
    - Exposure limits
    - Drawdown management
    - Leverage control
    - Correlation checks
    """

    def __init__(self, trading_config: TradingConfig, risk_config: RiskConfig):
        self.trading_config = trading_config
        self.risk_config = risk_config
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.peak_equity = 0.0
        self._last_trade_ts: dict[str, datetime] = {}

    def calculate_position_size(
        self,
        decision: TradingDecision,
        portfolio: Portfolio,
        volatility: float
    ) -> Tuple[float, str]:
        """
        Calculate position size based on risk parameters and confidence.

        Args:
            decision: Trading decision from AI
            portfolio: Current portfolio status
            volatility: Current market volatility (ATR %)

        Returns:
            Tuple of (position_size, reasoning)
        """
        capital = portfolio.total_value
        base_risk = self.trading_config.risk_per_trade

        # Adjust risk based on confidence
        if decision.confidence > 0.75:
            risk_pct = base_risk * 1.0  # Full risk for high confidence
        elif decision.confidence > 0.65:
            risk_pct = base_risk * 0.75  # 75% risk for medium confidence
        else:
            risk_pct = base_risk * 0.5  # 50% risk for lower confidence

        # Adjust for volatility regime
        if volatility > 3.0:  # High volatility
            risk_pct *= 0.5
            vol_note = "High volatility: reduced size by 50%"
        elif volatility < 1.0:  # Low volatility
            risk_pct *= 1.0
            vol_note = "Normal volatility"
        else:
            vol_note = "Normal volatility"

        # Adjust for market regime
        regime_modifier = 1.0
        if decision.market_regime.primary == MarketRegime.RANGING:
            regime_modifier = 0.5
            regime_note = "Ranging market: reduced size"
        elif decision.market_regime.primary in [MarketRegime.HIGH_VOLATILITY]:
            regime_modifier = 0.6
            regime_note = "High volatility regime: reduced size"
        else:
            regime_note = "Trending market"

        risk_pct *= regime_modifier

        # Adjust for current drawdown
        if portfolio.total_value < self.peak_equity * 0.9:  # >10% drawdown
            risk_pct *= 0.5
            dd_note = "In drawdown: reduced size by 50%"
        elif portfolio.total_value < self.peak_equity * 0.85:  # >15% drawdown
            risk_pct *= 0.3
            dd_note = "Significant drawdown: reduced size by 70%"
        else:
            dd_note = "No significant drawdown"

        # Apply AI's position size modifier
        risk_pct *= decision.risk_assessment.position_size_modifier

        # Calculate dollar risk
        dollar_risk = capital * risk_pct

        # Calculate position size based on stop loss distance
        if decision.suggested_action and decision.suggested_action.stop_loss:
            stop_distance_pct = decision.suggested_action.stop_loss.distance_pct / 100
            if stop_distance_pct > 0:
                position_size_usd = dollar_risk / stop_distance_pct
            else:
                position_size_usd = dollar_risk / 0.02  # Default 2% stop

            # Apply max position size limit
            max_position = min(
                self.trading_config.max_position_size,
                capital * self.trading_config.max_exposure
            )

            position_size_usd = min(position_size_usd, max_position)

            reasoning = f"Risk: {risk_pct*100:.2f}% (${dollar_risk:.0f}). {vol_note}. {regime_note}. {dd_note}. Max position: ${max_position:.0f}"

            return position_size_usd, reasoning
        else:
            # No stop loss defined, use conservative sizing
            position_size_usd = dollar_risk / 0.03  # Assume 3% risk
            return position_size_usd, "No stop loss defined, using conservative sizing"

    def validate_trade(
        self,
        decision: TradingDecision,
        portfolio: Portfolio,
        asset: str
    ) -> Tuple[bool, str]:
        """
        Validate if a trade should be executed based on risk rules.

        Args:
            decision: Trading decision
            portfolio: Current portfolio
            asset: Asset symbol

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check decision is not HOLD
        if decision.decision == Decision.HOLD:
            return False, "Decision is HOLD"

        # Per-asset cooldown (entries only, but allow adding to existing position)
        if decision.decision in [Decision.BUY, Decision.SELL]:
            # Check if we already have a position - if yes, allow adding to it (bypass cooldown)
            has_position = any(pos.symbol == asset for pos in portfolio.positions)

            if not has_position:  # Only apply cooldown for NEW positions
                last_ts = self._last_trade_ts.get(asset)
                if last_ts:
                    elapsed = datetime.utcnow() - last_ts
                    if elapsed < timedelta(minutes=self.trading_config.trade_cooldown_minutes):
                        wait_min = int((timedelta(minutes=self.trading_config.trade_cooldown_minutes) - elapsed).total_seconds() // 60) + 1
                        return False, f"Cooldown active for {asset}: wait ~{wait_min} min"

        # Check daily trade limit - DISABLED
        # if self.daily_trades >= self.risk_config.max_daily_trades:
        #     return False, f"Daily trade limit reached ({self.risk_config.max_daily_trades})"

        # Check daily loss limit
        daily_loss_limit = portfolio.total_value * self.trading_config.daily_loss_limit
        if self.daily_pnl < -daily_loss_limit:
            return False, f"Daily loss limit reached (${-daily_loss_limit:.0f})"

        # Check maximum drawdown
        if self.peak_equity > 0:
            current_dd = (self.peak_equity - portfolio.total_value) / self.peak_equity
            if current_dd > self.trading_config.max_drawdown_threshold:
                return False, f"Maximum drawdown exceeded ({current_dd*100:.1f}%)"

        # Check available balance
        if portfolio.available_balance < 100:  # Minimum $100
            return False, "Insufficient balance"

        # Check max concurrent positions
        if len(portfolio.positions) >= self.risk_config.max_concurrent_positions:
            # Check if we're closing a position
            if decision.decision not in [Decision.CLOSE_LONG, Decision.CLOSE_SHORT]:
                return False, f"Max concurrent positions reached ({self.risk_config.max_concurrent_positions})"

        # Check exposure limit
        if decision.suggested_action:
            new_exposure = self.calculate_new_exposure(portfolio, decision.suggested_action.quantity, asset)

            # Adjust max exposure based on regime
            max_exposure = self.trading_config.max_exposure

            if decision.market_regime.primary == MarketRegime.HIGH_VOLATILITY:
                max_exposure *= 0.6  # Reduce to 40% in high vol
            elif decision.market_regime.primary == MarketRegime.RANGING:
                max_exposure *= 0.7  # Reduce to ~50% in ranging

            if new_exposure > max_exposure:
                return False, f"Would exceed max exposure ({max_exposure*100:.0f}%)"

        # Check liquidity
        if decision.risk_assessment.liquidity_check == "FAIL":
            return False, "Liquidity check failed"

        # Check margin safety
        if decision.risk_assessment.margin_safety < 40:
            return False, f"Margin safety too low ({decision.risk_assessment.margin_safety:.1f}%)"

        # Check risk/reward ratio
        if decision.risk_assessment.risk_reward_ratio < self.trading_config.min_risk_reward:
            return False, f"R:R ratio too low ({decision.risk_assessment.risk_reward_ratio:.2f})"

        # Check correlation (if multiple positions)
        if len(portfolio.positions) > 0:
            correlated_positions = sum(1 for pos in portfolio.positions if self._is_correlated(pos.asset, asset))
            if correlated_positions >= self.risk_config.max_correlated_positions:
                return False, f"Too many correlated positions ({correlated_positions})"

        return True, "All risk checks passed"

    def mark_asset_trade(self, asset: str) -> None:
        """Record a trade timestamp for cooldown enforcement."""
        self._last_trade_ts[asset] = datetime.utcnow()

    def calculate_new_exposure(self, portfolio: Portfolio, position_size: float, asset: str) -> float:
        """Calculate what the exposure would be after adding a position."""
        current_exposure_usd = sum(abs(p.size * p.current_price) for p in portfolio.positions)
        new_exposure_usd = current_exposure_usd + position_size

        if portfolio.total_value > 0:
            return new_exposure_usd / portfolio.total_value
        return 0.0

    def update_daily_stats(self, pnl: float):
        """Update daily trading statistics."""
        self.daily_trades += 1
        self.daily_pnl += pnl

    def reset_daily_stats(self):
        """Reset daily statistics (call at end of day)."""
        self.daily_trades = 0
        self.daily_pnl = 0.0

    def update_peak_equity(self, current_equity: float):
        """Update peak equity for drawdown calculation."""
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

    def get_current_drawdown(self, current_equity: float) -> float:
        """Calculate current drawdown percentage."""
        if self.peak_equity == 0:
            return 0.0
        return max(0, (self.peak_equity - current_equity) / self.peak_equity)

    def _is_correlated(self, asset1: str, asset2: str) -> bool:
        """Check if two assets are correlated."""
        # Simplified correlation check
        # In production, you'd calculate actual correlation from price data
        major_cryptos = ["BTC", "ETH"]

        if asset1 in major_cryptos and asset2 in major_cryptos:
            return True

        if asset1 == asset2:
            return True

        # All altcoins are considered correlated with BTC
        return True

    def calculate_leverage(
        self,
        asset: str,
        volatility: float,
        confidence: float
    ) -> int:
        """
        Calculate appropriate leverage for a trade.

        Args:
            asset: Asset symbol
            volatility: Current volatility
            confidence: AI confidence

        Returns:
            Leverage multiplier
        """
        # Base leverage limits
        if asset in ["BTC", "ETH"]:
            max_leverage = self.trading_config.btc_eth_max_leverage
        else:
            max_leverage = self.trading_config.large_cap_max_leverage

        # Reduce leverage in high volatility
        if volatility > 3.0:
            max_leverage = max(1, max_leverage // 2)

        # Reduce leverage for lower confidence
        if confidence < 0.7:
            max_leverage = max(1, max_leverage // 2)

        return max_leverage

    def should_reduce_position(self, position: Position, current_price: float) -> Tuple[bool, str]:
        """
        Check if a position should be reduced based on adverse conditions.

        Args:
            position: Current position
            current_price: Current market price

        Returns:
            Tuple of (should_reduce, reason)
        """
        # Check if position is underwater significantly
        if position.unrealized_pnl_percent < -3:
            return True, "Position down >3% without hitting stop"

        # Check if stop loss is close
        if position.stop_loss:
            distance_to_stop = abs(current_price - position.stop_loss) / current_price
            if distance_to_stop < 0.005:  # Within 0.5%
                return True, "Very close to stop loss"

        # Check if liquidation is approaching
        if position.liquidation_price:
            distance_to_liq = abs(current_price - position.liquidation_price) / current_price
            if distance_to_liq < 0.10:  # Within 10%
                return True, "Approaching liquidation"

        return False, ""

    def emergency_stop(self) -> bool:
        """Check if emergency stop should be triggered."""
        if self.peak_equity > 0:
            current_dd = self.get_current_drawdown(self.peak_equity)
            if current_dd > 0.20:  # 20% drawdown
                logger.critical(f"EMERGENCY STOP: Drawdown {current_dd*100:.1f}% exceeds 20%")
                return True

        return False
