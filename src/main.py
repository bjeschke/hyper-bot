"""Main trading bot loop."""

import asyncio
from datetime import datetime
from typing import Dict
from loguru import logger
import sys

from src.config import config
from src.hyperliquid.client import HyperliquidClient
from src.analysis.indicators import TechnicalAnalysis
from src.ai.deepseek_engine import DeepSeekEngine
from src.risk.manager import RiskManager
from src.risk.performance_tracker import PerformanceTracker
from src.trading.position_manager import PositionManager
from src.utils.models import TechnicalIndicators, Decision


class TradingBot:
    """
    Main trading bot orchestrator.

    Coordinates:
    - Market data fetching
    - Technical analysis
    - AI decision making
    - Risk management
    - Order execution
    - Position monitoring
    """

    def __init__(self):
        # Validate config
        is_valid, errors = config.validate()
        if not is_valid:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            sys.exit(1)

        # Initialize components
        self.hl_client = HyperliquidClient(config.hyperliquid)

        # Initialize AI: Multi-Agent System OR Single Agent
        if config.deepseek.multi_agent_enabled:
            from src.agents.orchestrator import TradingDeskOrchestrator
            self.trading_desk = TradingDeskOrchestrator(config.deepseek.api_key)
            self.ai_engine = None
            logger.info("🏢 Using Multi-Agent Trading Desk (5 agents)")
        else:
            self.ai_engine = DeepSeekEngine(config.deepseek)
            self.trading_desk = None
            logger.info("🤖 Using Single-Agent DeepSeek Engine")

        self.risk_manager = RiskManager(config.trading, config.risk)
        self.performance_tracker = PerformanceTracker()
        self.position_manager = PositionManager()

        # Multi-asset support
        if config.trading.trading_assets:
            self.assets = config.trading.trading_assets
            logger.info(f"Multi-asset mode: Trading {len(self.assets)} assets: {', '.join(self.assets)}")
        else:
            self.assets = [config.trading.default_asset]
            logger.info(f"Single-asset mode: Trading {self.assets[0]}")

        self.trading_interval = config.trading.trading_interval
        self.running = False

        # Setup logging
        self._setup_logging()

        logger.info("Trading Bot initialized")
        logger.info(f"Trading {', '.join(self.assets)} on {'TESTNET' if config.hyperliquid.testnet else 'MAINNET'}")

    def _setup_logging(self):
        """Setup logging configuration."""
        logger.remove()  # Remove default handler

        # Console logging
        logger.add(
            sys.stdout,
            format=config.logging.log_format,
            level=config.logging.level,
            colorize=True
        )

        # File logging
        logger.add(
            config.logging.log_file,
            format=config.logging.log_format,
            level=config.logging.level,
            rotation=config.logging.rotation,
            retention=config.logging.retention,
            compression="zip"
        )

    async def start(self):
        """Start the trading bot."""
        self.running = True

        logger.info("=" * 80)
        logger.info("HYPERLIQUID TRADING BOT STARTING")
        logger.info("=" * 80)

        # Health check
        async with self.hl_client:
            healthy = await self.hl_client.health_check()
            if not healthy:
                logger.error("Hyperliquid API health check failed. Exiting.")
                return

            # Get initial portfolio state
            portfolio = await self.hl_client.get_account_state()
            self.risk_manager.update_peak_equity(portfolio.total_value)

            logger.info(f"Initial Portfolio: ${portfolio.total_value:,.2f}")
            logger.info(f"Available Balance: ${portfolio.available_balance:,.2f}")
            logger.info(f"Trading Assets: {', '.join(self.assets)}")

            if portfolio.positions:
                logger.info(f"Existing Positions: {len(portfolio.positions)}")
                for pos in portfolio.positions:
                    logger.info(f"  - {pos.side} {pos.size} {pos.asset} @ ${pos.entry_price} (P&L: ${pos.unrealized_pnl:,.2f})")

            logger.info(f"Trading loop interval: {self.trading_interval}s")
            logger.info("Bot is running. Press Ctrl+C to stop.")
            logger.info("=" * 80)

            # Main loop
            try:
                while self.running:
                    await self.trading_loop()
                    await asyncio.sleep(self.trading_interval)
            except KeyboardInterrupt:
                logger.info("Shutdown signal received")
                await self.stop()
            except Exception as e:
                logger.exception(f"Fatal error in main loop: {e}")
                await self.stop()

    async def trading_loop(self):
        """Main trading loop - executes every interval."""
        try:
            logger.info(f"--- Trading Loop: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")

            # Get portfolio first (needed for all assets)
            portfolio = await self.hl_client.get_account_state()
            self.risk_manager.update_peak_equity(portfolio.total_value)

            # Update balance and check daily limits
            can_continue = self.performance_tracker.update_balance(portfolio.total_value)
            if not can_continue:
                logger.critical("Daily loss limit hit - stopping for today")
                await self.close_all_positions()
                await self.stop()
                return

            # Check if we can trade today
            can_trade, reason = self.performance_tracker.can_trade()
            if not can_trade:
                logger.warning(f"Trading not allowed: {reason}")
                daily_stats = self.performance_tracker.get_daily_stats()
                logger.info(f"Daily Stats: {daily_stats['trades_today']} trades, {daily_stats['daily_pnl_pct']:+.2f}% P&L")
                return

            # Monitor existing positions
            await self.monitor_positions()

            # Check emergency stop
            if self.risk_manager.emergency_stop():
                logger.critical("EMERGENCY STOP TRIGGERED - Closing all positions")
                await self.close_all_positions()
                await self.stop()
                return

            # Iterate through all assets
            for asset in self.assets:
                await self.analyze_and_trade_asset(asset, portfolio)

            # Log daily performance
            daily_stats = self.performance_tracker.get_daily_stats()
            logger.info(f"Daily Summary: {daily_stats['trades_today']}/8 trades, {daily_stats['wins']}W-{daily_stats['losses']}L, {daily_stats['daily_pnl_pct']:+.2f}% P&L")

            logger.info("--- Trading Loop Complete ---\n")

        except Exception as e:
            logger.exception(f"Error in trading loop: {e}")

    async def analyze_and_trade_asset(self, asset: str, portfolio):
        """Analyze and potentially trade a single asset."""
        try:
            logger.info(f"\n>>> Analyzing {asset} <<<")

            # 1. Fetch market data
            logger.info(f"Fetching market data for {asset}...")
            market_data = await self.hl_client.get_multi_timeframe_data(asset)

            # 2. Get orderbook
            orderbook = await self.hl_client.get_orderbook(asset, depth=20)

            # Guard: skip if spread too wide
            if orderbook and orderbook.spread_bps and orderbook.spread_bps > config.trading.max_spread_bps:
                logger.warning(f"{asset}: Spread {orderbook.spread_bps:.1f} bps > max {config.trading.max_spread_bps:.1f} bps. Skipping.")
                return

            # 3. Get derivatives data
            derivatives = await self.hl_client.get_funding_rate(asset)

            # 4. Calculate technical indicators for all timeframes
            logger.info(f"Calculating technical indicators for {asset}...")
            indicators: Dict[str, TechnicalIndicators] = {}

            for timeframe in ["1h", "4h"]:  # Reduced timeframes for token efficiency (removed 5m)
                candles = await self.hl_client.get_candles(asset, timeframe, limit=100)  # Reduced for token efficiency
                if candles:
                    indicators[timeframe] = await TechnicalAnalysis.calculate_all_indicators(candles, timeframe)

            # 5. Get AI decision (Single-Agent OR Multi-Agent)
            logger.info(f"Requesting AI trading decision for {asset}...")
            start_ai = datetime.now()

            if self.trading_desk:
                # Multi-Agent System: Trading Desk Discussion
                # Use current_price from MultiTimeframeData
                price = market_data.current_price

                # Build indicators summary (fix attribute names)
                indicators_summary = {}
                if '1h' in indicators and indicators['1h']:
                    ind_1h = indicators['1h']
                    indicators_summary['rsi'] = ind_1h.rsi_1h if hasattr(ind_1h, 'rsi_1h') else None
                    indicators_summary['adx'] = ind_1h.adx if hasattr(ind_1h, 'adx') else None
                    if hasattr(ind_1h, 'macd_1h') and ind_1h.macd_1h:
                        indicators_summary['macd'] = ind_1h.macd_1h.histogram
                    else:
                        indicators_summary['macd'] = None

                context = {
                    'asset': asset,
                    'price': price,
                    'indicators': indicators_summary,
                    'market_data': market_data,
                    'full_indicators': indicators,
                    'orderbook': orderbook,
                    'derivatives': derivatives,
                    'portfolio': portfolio
                }
                decision = await self.trading_desk.run_trading_discussion(context)
            else:
                # Single-Agent System: DeepSeek Engine
                decision = await self.ai_engine.get_trading_decision(
                    asset=asset,
                    market_data=market_data,
                    indicators=indicators,
                    orderbook=orderbook,
                    derivatives=derivatives,
                    portfolio=portfolio
                )

            ai_ms = (datetime.now() - start_ai).total_seconds() * 1000
            if ai_ms > config.trading.ai_latency_guard_ms:
                logger.warning(f"{asset}: AI latency {ai_ms:.0f}ms > guard {config.trading.ai_latency_guard_ms}ms. Holding.")
                return

            if not decision:
                logger.error(f"Failed to get AI decision for {asset}, skipping")
                return

            # Log decision
            logger.info(f"AI Decision for {asset}: {decision.decision.value}")
            logger.info(f"Setup Quality: {decision.setup_quality.value} | Confidence: {decision.confidence:.2f}")
            logger.info(f"Confluence Score: {decision.confluence_score}/10")
            logger.info(f"Market Regime: {decision.market_regime.primary.value}")
            logger.info(f"Reasoning: {decision.reasoning[:200]}...")

            # 6. Validate decision (skip for multi-agent system as it has its own validation)
            if self.ai_engine:
                is_valid, validation_msg = self.ai_engine.validate_decision(
                    decision,
                    min_confidence=config.trading.min_confidence,
                    min_confluence=config.trading.min_confluence_score,
                    min_rr=config.trading.min_risk_reward,
                )

                if not is_valid:
                    logger.warning(f"{asset}: Decision validation failed: {validation_msg}")
                    return

            # 7. Performance-based quality filtering
            if self.performance_tracker.should_only_trade_aplus_setups():
                if decision.confidence < 0.75 or decision.confluence_score < 7:
                    logger.warning(f"{asset}: Skipping - not A+ setup (6+ trades today, need conf>0.75 & confluence>7)")
                    return

            # 8. Risk management check
            can_trade, risk_msg = self.risk_manager.validate_trade(decision, portfolio, asset)

            if not can_trade:
                logger.warning(f"{asset}: Risk check failed: {risk_msg}")
                return

            # 9. Execute trade based on decision
            if decision.decision in [Decision.BUY, Decision.SELL]:
                await self.execute_entry(asset, decision, portfolio, indicators.get("1h"))

            elif decision.decision in [Decision.CLOSE_LONG, Decision.CLOSE_SHORT]:
                await self.execute_close(asset, decision)

            elif decision.decision == Decision.HOLD:
                logger.info(f"{asset}: Holding - no trade signal")

        except Exception as e:
            logger.exception(f"Error in trading loop: {e}")

    async def execute_entry(self, asset: str, decision, portfolio, indicators: TechnicalIndicators):
        """Execute entry order."""
        try:
            if not decision.suggested_action:
                logger.warning(f"{asset}: No suggested action in decision")
                return

            suggested_action = decision.suggested_action

            # Calculate position size
            volatility = indicators.atr_percent if indicators and indicators.atr_percent else 2.0
            position_size_usd, size_reasoning = self.risk_manager.calculate_position_size(
                decision, portfolio, volatility
            )

            # ADX low-volatility guard: cap size
            if indicators and getattr(indicators, 'adx', None) is not None:
                adx_val = indicators.adx
                if adx_val is not None and adx_val < config.trading.adx_low_threshold:
                    capped = position_size_usd * config.trading.adx_low_size_cap
                    logger.warning(f"{asset}: ADX {adx_val:.1f} < {config.trading.adx_low_threshold:.1f} → size cap {config.trading.adx_low_size_cap*100:.0f}% (${position_size_usd:,.0f} → ${capped:,.0f})")
                    position_size_usd = capped

            # Apply performance-based modifier
            size_modifier = self.performance_tracker.get_position_size_modifier()
            if size_modifier < 1.0:
                position_size_usd *= size_modifier
                logger.warning(f"{asset}: Position size reduced by {(1-size_modifier)*100:.0f}% due to performance/losses")

            # Calculate quantity in asset terms
            quantity = position_size_usd / suggested_action.entry_price

            logger.info(f"{asset}: Position sizing: ${position_size_usd:,.0f} (~{quantity:.4f} {asset})")
            logger.info(f"{asset}: Sizing reasoning: {size_reasoning}")

            # Calculate leverage
            leverage = self.risk_manager.calculate_leverage(
                asset,
                volatility,
                decision.confidence
            )

            logger.info(f"{asset}: Using {leverage}x leverage")

            # Place order
            logger.info(f"{asset}: Placing {suggested_action.type.value} {suggested_action.side.value} order:")
            logger.info(f"  Entry: ${suggested_action.entry_price:.2f}")
            logger.info(f"  Quantity: {quantity:.4f} {asset}")
            logger.info(f"  Stop Loss: ${suggested_action.stop_loss.price:.2f} ({suggested_action.stop_loss.distance_pct:.2f}%)")
            logger.info(f"  TP Targets: {len(suggested_action.take_profit_targets)}")

            # Execute order
            order_result = await self.hl_client.place_order(
                asset=asset,
                side=suggested_action.side.value,
                size=quantity,
                order_type=suggested_action.type.value,
                price=suggested_action.entry_price if suggested_action.type.value == "LIMIT" else None
            )

            logger.success(f"{asset}: Order placed successfully: {order_result}")

            # Mark cooldown for this asset
            self.risk_manager.mark_asset_trade(asset)

            # Log trade to performance tracker
            tp_prices = [tp.price for tp in suggested_action.take_profit_targets]
            self.performance_tracker.log_trade(
                asset=asset,
                side=suggested_action.side.value,
                entry_price=suggested_action.entry_price,
                size=quantity,
                stop_loss=suggested_action.stop_loss.price,
                take_profit=tp_prices,
                confidence=decision.confidence,
                confluence=decision.confluence_score,
                reason=decision.reasoning[:200]
            )

            # Create position object
            from src.utils.models import Position

            position = Position(
                asset=asset,
                side="LONG" if suggested_action.side.value == "BUY" else "SHORT",
                size=quantity,
                entry_price=suggested_action.entry_price,
                current_price=suggested_action.entry_price,
                leverage=leverage,
                margin_used=position_size_usd / leverage,
                unrealized_pnl=0.0,
                unrealized_pnl_percent=0.0,
                liquidation_price=0.0  # Would be calculated by exchange
            )

            # Add to position manager
            self.position_manager.add_position(position, decision, suggested_action)

            # Update risk manager
            self.risk_manager.update_daily_stats(0)  # Entry doesn't have P&L yet

        except Exception as e:
            logger.exception(f"{asset}: Failed to execute entry: {e}")

    async def execute_close(self, asset: str, decision):
        """Execute position close."""
        try:
            logger.info(f"Closing position for {asset}")

            # Get position info before closing
            position = self.position_manager.get_position(asset)

            result = await self.hl_client.close_position(asset)

            logger.success(f"Position closed: {result}")

            # Log trade close to performance tracker
            if position:
                # Update stats with final P&L
                self.risk_manager.update_daily_stats(position.unrealized_pnl)

                # Log to performance tracker
                self.performance_tracker.log_trade_close(
                    asset=asset,
                    exit_price=position.current_price,
                    pnl=position.unrealized_pnl,
                    pnl_pct=position.unrealized_pnl_percent
                )

            self.position_manager.remove_position(asset)

        except Exception as e:
            logger.exception(f"Failed to close position: {e}")

    async def monitor_positions(self):
        """Monitor open positions for TP/SL hits and trailing stops."""
        positions = self.position_manager.get_all_positions()

        if not positions:
            return

        logger.info(f"Monitoring {len(positions)} open position(s)...")

        for position in positions:
            try:
                # Get current price
                ticker = await self.hl_client.get_ticker(position.asset)
                current_price = float(ticker.get('lastPx', position.current_price))

                # Update position
                self.position_manager.update_position(position.asset, current_price)

                # Check stop loss
                if self.position_manager.check_stop_loss(position.asset):
                    logger.warning(f"Stop loss hit for {position.asset} - closing position")
                    await self.hl_client.close_position(position.asset)

                    # Log trade close
                    self.performance_tracker.log_trade_close(
                        asset=position.asset,
                        exit_price=current_price,
                        pnl=position.unrealized_pnl,
                        pnl_pct=position.unrealized_pnl_percent
                    )

                    self.position_manager.remove_position(position.asset)
                    continue

                # Check take profit levels
                tp_hit = self.position_manager.check_take_profit_levels(position.asset)
                if tp_hit:
                    percentage_to_close = tp_hit["percentage_to_close"]
                    close_size = position.size * (percentage_to_close / 100)

                    logger.info(f"TP{tp_hit['tp_level']} hit - closing {percentage_to_close}% ({close_size:.4f} {position.asset})")

                    # Close partial position
                    side = "SELL" if position.side == "LONG" else "BUY"
                    await self.hl_client.place_order(
                        asset=position.asset,
                        side=side,
                        size=close_size,
                        order_type="MARKET",
                        reduce_only=True
                    )

                # Update trailing stop
                self.position_manager.update_trailing_stop(position.asset)

                # Check time-based exit
                if self.position_manager.should_close_by_time(position.asset, max_duration_hours=24):
                    logger.info(f"Time-based exit for {position.asset}")
                    await self.hl_client.close_position(position.asset)

                    # Log trade close
                    self.performance_tracker.log_trade_close(
                        asset=position.asset,
                        exit_price=current_price,
                        pnl=position.unrealized_pnl,
                        pnl_pct=position.unrealized_pnl_percent
                    )

                    self.position_manager.remove_position(position.asset)
                    continue

                # Log position status
                stats = self.position_manager.get_position_stats(position.asset)
                logger.info(f"Position {position.asset}: ${stats['unrealized_pnl']:,.2f} ({stats['unrealized_pnl_percent']:+.2f}%) | Duration: {stats['duration_hours']:.1f}h")

            except Exception as e:
                logger.error(f"Error monitoring position {position.asset}: {e}")

    async def close_all_positions(self):
        """Close all open positions (emergency)."""
        positions = self.position_manager.get_all_positions()

        logger.warning(f"Closing all {len(positions)} position(s)...")

        for position in positions:
            try:
                await self.hl_client.close_position(position.asset)

                # Log trade close
                self.performance_tracker.log_trade_close(
                    asset=position.asset,
                    exit_price=position.current_price,
                    pnl=position.unrealized_pnl,
                    pnl_pct=position.unrealized_pnl_percent
                )

                self.position_manager.remove_position(position.asset)
                logger.info(f"Closed position: {position.asset}")
            except Exception as e:
                logger.error(f"Failed to close {position.asset}: {e}")

    async def stop(self):
        """Stop the trading bot."""
        logger.info("Stopping trading bot...")
        self.running = False

        # Close session
        if self.hl_client.session:
            await self.hl_client.session.close()

        logger.info("Trading bot stopped")


async def main():
    """Main entry point."""
    bot = TradingBot()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
