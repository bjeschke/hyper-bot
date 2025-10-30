"""DeepSeek AI engine for trading decisions."""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from openai import AsyncOpenAI
from loguru import logger

from src.config import DeepSeekConfig
from src.utils.models import (
    TradingDecision,
    Decision,
    SetupQuality,
    MarketRegimeData,
    ConfluenceAnalysis,
    IndicatorsSummary,
    SuggestedAction,
    RiskAssessment,
    TechnicalIndicators,
    MultiTimeframeData,
    OrderbookData,
    DerivativesData,
    Portfolio,
    MarketRegime,
)


class DeepSeekEngine:
    """
    DeepSeek AI engine for trading analysis and decisions.

    Uses the production-grade prompt to analyze market data and generate
    trading decisions with institutional-level analysis.
    """

    def __init__(self, config: DeepSeekConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

    def _load_system_prompt(self) -> str:
        """Load the system prompt from prompt.md."""
        try:
            with open("prompt.md", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error("prompt.md not found, using fallback prompt")
            return self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """Fallback prompt if prompt.md is not found."""
        return """You are a professional trading algorithm for Hyperliquid DEX.
        Analyze market data and provide trading decisions in JSON format with confluence-based analysis."""

    def generate_prompt(
        self,
        asset: str,
        market_data: MultiTimeframeData,
        indicators: Dict[str, TechnicalIndicators],
        orderbook: OrderbookData,
        derivatives: DerivativesData,
        portfolio: Portfolio
    ) -> str:
        """
        Generate the complete prompt with market data.

        Args:
            asset: Asset symbol
            market_data: Multi-timeframe market data
            indicators: Technical indicators for each timeframe
            orderbook: Orderbook data
            derivatives: Derivatives market data
            portfolio: Current portfolio status

        Returns:
            Complete prompt string with all data
        """
        # Extract data for each timeframe
        data_1m = market_data.data_1m
        data_5m = market_data.data_5m
        data_15m = market_data.data_15m
        data_1h = market_data.data_1h
        data_4h = market_data.data_4h
        data_24h = market_data.data_24h

        # Get indicators for different timeframes
        ind_5m = indicators.get("5m", TechnicalIndicators())
        ind_1h = indicators.get("1h", TechnicalIndicators())
        ind_4h = indicators.get("4h", TechnicalIndicators())

        # Build the data prompt
        data_prompt = f"""
# Current Market Data for {asset}

## Multi-Timeframe Price Data
- Current Price: ${market_data.current_price:.2f}
- Mark Price: ${market_data.mark_price:.2f}
- Index Price: ${market_data.index_price:.2f}

**1m Timeframe:**
- Price Change: {data_1m.price_change if data_1m else 0:.2f}% | Volume: ${data_1m.volume if data_1m else 0:,.0f}

**5m Timeframe:**
- Price Change: {data_5m.price_change if data_5m else 0:.2f}% | Volume: ${data_5m.volume if data_5m else 0:,.0f} | Volatility: {data_5m.volatility if data_5m and data_5m.volatility else 0:.2f}%

**15m Timeframe:**
- Price Change: {data_15m.price_change if data_15m else 0:.2f}% | Volume: ${data_15m.volume if data_15m else 0:,.0f}

**1h Timeframe:**
- Price Change: {data_1h.price_change if data_1h else 0:.2f}% | Volume: ${data_1h.volume if data_1h else 0:,.0f}
- High: ${data_1h.high if data_1h else 0:.2f} | Low: ${data_1h.low if data_1h else 0:.2f}

**4h Timeframe:**
- Price Change: {data_4h.price_change if data_4h else 0:.2f}% | High: ${data_4h.high if data_4h else 0:.2f} | Low: ${data_4h.low if data_4h else 0:.2f}

**24h Timeframe:**
- Price Change: {data_24h.price_change if data_24h else 0:.2f}% | Volume: ${data_24h.volume if data_24h else 0:,.0f}
- High: ${data_24h.high if data_24h else 0:.2f} | Low: ${data_24h.low if data_24h else 0:.2f}

## Technical Indicators

**Momentum & Oscillators:**
- RSI(14): 5m: {ind_5m.rsi_5m or 50:.1f} | 1h: {ind_1h.rsi_1h or 50:.1f} | 4h: {ind_4h.rsi_4h or 50:.1f}
- MACD 1h: Value: {ind_1h.macd.value if ind_1h.macd else 0:.2f} | Signal: {ind_1h.macd.signal if ind_1h.macd else 0:.2f} | Histogram: {ind_1h.macd.histogram if ind_1h.macd else 0:.2f}

**Trend Indicators:**
- EMA 20/50/200: {ind_1h.ema_20 or 0:.2f} / {ind_1h.ema_50 or 0:.2f} / {ind_1h.ema_200 or 0:.2f}
- ADX(14): {ind_1h.adx or 0:.1f} | +DI/-DI: {ind_1h.plus_di or 0:.1f} / {ind_1h.minus_di or 0:.1f}
- Supertrend: {ind_1h.supertrend or 0:.2f} (Signal: {ind_1h.supertrend_signal or "neutral"})

**Volatility:**
- Bollinger Bands: Upper: {ind_1h.bollinger_bands.upper if ind_1h.bollinger_bands else 0:.2f} | Middle: {ind_1h.bollinger_bands.middle if ind_1h.bollinger_bands else 0:.2f} | Lower: {ind_1h.bollinger_bands.lower if ind_1h.bollinger_bands else 0:.2f}
- %B Position: {ind_1h.bollinger_bands.percent_b if ind_1h.bollinger_bands else 0:.2f}
- ATR(14): {ind_1h.atr or 0:.2f} ({ind_1h.atr_percent or 0:.2f}% of price)

**Volume Analysis:**
- VWAP Daily: {ind_1h.vwap_daily or 0:.2f}
- CVD: {ind_1h.cvd or 0:.0f} (Trend: {ind_1h.cvd_trend or "neutral"})
- OBV: {ind_1h.obv or 0:.0f} (Trend: {ind_1h.obv_trend or "neutral"})
- Volume Ratio: {ind_1h.volume_ratio or 1:.2f}x

## 📊 DETAILED CHART HISTORY (Recent Price Action)
**Analysiere diese Daten wie ein Chart - identifiziere Patterns, Support/Resistance, Trends!**

### Last 24 Hours Price Movement (1h Candles):
```
Time       | Open     | High     | Low      | Close    | Volume   | Change
-----------|----------|----------|----------|----------|----------|--------
```

_Identifiziere:_
- Higher Highs / Lower Lows? (Trend)
- Support und Resistance Zones
- Breakouts oder Rejections
- Volume Profile (wo war meiste Aktivität?)
- Swing Points für Stop-Loss Platzierung

### Key Price Levels (abgeleitet aus Historie):
- **Recent High**: ${data_24h.high if data_24h else 0:.2f}
- **Recent Low**: ${data_24h.low if data_24h else 0:.2f}
- **Current vs High**: {((market_data.current_price / (data_24h.high if data_24h and data_24h.high > 0 else market_data.current_price)) - 1) * 100:.1f}%
- **Current vs Low**: {((market_data.current_price / (data_24h.low if data_24h and data_24h.low > 0 else market_data.current_price)) - 1) * 100:.1f}%

### Pattern Recognition (denke laut):
- "Sehe ich Double Top/Bottom?"
- "Ist das ein Triangle/Wedge Pattern?"
- "Bull/Bear Flag im Gange?"
- "Wo sind die letzten Swing Highs/Lows für Stop-Loss?"

## Orderbook & Microstructure
- Top 10 Bids: {len(orderbook.bids)} levels (Total: ${orderbook.bid_liquidity:,.0f})
- Top 10 Asks: {len(orderbook.asks)} levels (Total: ${orderbook.ask_liquidity:,.0f})
- Bid-Ask Spread: {orderbook.spread_bps:.1f} bps (${orderbook.spread_usd:.2f})
- Orderbook Imbalance: {orderbook.imbalance:+.1f}% {"(bid pressure)" if orderbook.imbalance > 0 else "(ask pressure)" if orderbook.imbalance < 0 else "(balanced)"}

## Derivatives Data
- Funding Rate: {derivatives.funding_rate:.4f}% per 8h (Annual: {derivatives.funding_rate_annual:.2f}%)
- Funding Trend: {derivatives.funding_trend}
- Next Funding: in {derivatives.time_to_funding} minutes
- Open Interest: ${derivatives.open_interest:,.0f} ({derivatives.oi_change_24h:+.1f}% change 24h)
- OI Trend: {derivatives.oi_trend}
- Long/Short Ratio: {derivatives.long_short_ratio:.2f} ({derivatives.ratio_interpretation})

## Portfolio Status
- Total Account Value: ${portfolio.total_value:,.2f} USDC
- Available Balance: ${portfolio.available_balance:,.2f} USDC
- Used Margin: ${portfolio.used_margin:,.2f} USDC ({portfolio.margin_usage_percent:.1f}%)
- Current Exposure: {portfolio.exposure_percent:.1f}% of total capital
- Current Positions: {len(portfolio.positions)}
- Unrealized P&L: ${portfolio.unrealized_pnl:,.2f}
- Realized P&L (24h): ${portfolio.realized_pnl_24h:,.2f}

"""

        # Add position details if any
        if portfolio.positions:
            data_prompt += "\n## Current Positions:\n"
            for pos in portfolio.positions:
                data_prompt += f"- {pos.side} {pos.size} {pos.asset} @ ${pos.entry_price:.2f} (P&L: ${pos.unrealized_pnl:,.2f}, {pos.unrealized_pnl_percent:+.2f}%)\n"
        else:
            data_prompt += "\n## Current Positions: None\n"

        # Add analysis request (concise, no CoT)
        data_prompt += """
Follow the system prompt. Output JSON only, strictly matching the schema. No chain-of-thought.
"""

        return data_prompt

    async def get_trading_decision(
        self,
        asset: str,
        market_data: MultiTimeframeData,
        indicators: Dict[str, TechnicalIndicators],
        orderbook: OrderbookData,
        derivatives: DerivativesData,
        portfolio: Portfolio
    ) -> Optional[TradingDecision]:
        """
        Get trading decision from DeepSeek AI.

        Args:
            asset: Asset symbol
            market_data: Multi-timeframe market data
            indicators: Technical indicators
            orderbook: Orderbook data
            derivatives: Derivatives data
            portfolio: Portfolio status

        Returns:
            TradingDecision object or None if error
        """
        try:
            # Load system prompt
            system_prompt = self._load_system_prompt()

            # Generate data prompt
            user_prompt = self.generate_prompt(
                asset, market_data, indicators, orderbook, derivatives, portfolio
            )

            logger.info(f"Requesting trading decision from DeepSeek for {asset}")

            # Call DeepSeek API
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )

            # Parse response
            content = response.choices[0].message.content
            decision_data = json.loads(content)

            logger.info(f"Received decision from DeepSeek: {decision_data.get('decision')} (confidence: {decision_data.get('confidence')})")

            # Save detailed reasoning to separate log file
            self._save_reasoning_log(asset, decision_data, response)

            # Parse into TradingDecision object
            trading_decision = self._parse_decision(decision_data)

            return trading_decision

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DeepSeek response: {e}")
            logger.debug(f"Response content: {content}")
            return None
        except Exception as e:
            logger.error(f"Error getting trading decision: {e}")
            return None

    def _parse_decision(self, data: Dict[str, Any]) -> TradingDecision:
        """Parse JSON response into TradingDecision object."""
        # Parse market regime
        regime_data = data.get("market_regime", {})
        market_regime = MarketRegimeData(
            primary=MarketRegime(regime_data.get("primary", "RANGING")),
            strength=regime_data.get("strength", 0.5),
            regime_aligned=regime_data.get("regime_aligned", False)
        )

        # Parse confluence analysis
        confluence_data = data.get("confluence_analysis", {})
        confluence_analysis = ConfluenceAnalysis(
            trend_score=confluence_data.get("trend_score", 0),
            trend_details=confluence_data.get("trend_details", ""),
            momentum_score=confluence_data.get("momentum_score", 0),
            momentum_details=confluence_data.get("momentum_details", ""),
            volume_score=confluence_data.get("volume_score", 0),
            volume_details=confluence_data.get("volume_details", ""),
            microstructure_score=confluence_data.get("microstructure_score", 0),
            microstructure_details=confluence_data.get("microstructure_details", ""),
            total_confluence=confluence_data.get("total_confluence", 0)
        )

        # Parse indicators summary
        indicators_summary = IndicatorsSummary(
            trend=data.get("indicators_summary", {}).get("trend", {}),
            momentum=data.get("indicators_summary", {}).get("momentum", {}),
            volume=data.get("indicators_summary", {}).get("volume", {}),
            volatility=data.get("indicators_summary", {}).get("volatility", {})
        )

        # Parse suggested action (if present)
        # HOLD decisions should not have a suggested action
        suggested_action = None
        if "suggested_action" in data and data["suggested_action"]:
            # Only parse if this is not a HOLD decision
            decision_type = data.get("decision", "HOLD")
            if decision_type not in ["HOLD", "NO_ACTION"]:
                try:
                    suggested_action = self._parse_suggested_action(data["suggested_action"])
                except Exception as e:
                    logger.warning(f"Failed to parse suggested_action: {e}. Setting to None.")
                    suggested_action = None

        # Parse risk assessment
        risk_data = data.get("risk_assessment", {})
        risk_assessment = RiskAssessment(
            overall_risk=risk_data.get("overall_risk", "MEDIUM"),
            risk_factors=risk_data.get("risk_factors", []),
            edge_quality=risk_data.get("edge_quality", 0.5),
            risk_reward_ratio=risk_data.get("risk_reward_ratio", 0.0),
            expected_value=risk_data.get("expected_value", 0.0),
            position_size_modifier=risk_data.get("position_size_modifier", 1.0),
            slippage_estimate=risk_data.get("slippage_estimate", 0.0),
            liquidity_check=risk_data.get("liquidity_check", "PASS"),
            funding_impact=risk_data.get("funding_impact", 0.0),
            margin_safety=risk_data.get("margin_safety", 100.0),
            liquidation_distance_pct=risk_data.get("liquidation_distance_pct", 0.0)
        )

        # Normalize setup_quality to internal enum values
        setup_quality_raw = data.get("setup_quality", "NO_SETUP")
        if setup_quality_raw == "A_PLUS":
            setup_quality_raw = "A+"
        if setup_quality_raw == "NONE":
            setup_quality_raw = "NO_SETUP"

        # Build reasoning from rationale/evidence if explicit reasoning missing
        reasoning_text = data.get("reasoning")
        if not reasoning_text:
            rationale = data.get("rationale")
            evidence = data.get("evidence", [])
            bullets = "\n".join([f"- {e}" for e in evidence]) if evidence else ""
            reasoning_text = (rationale or "").strip()
            if bullets:
                reasoning_text = (reasoning_text + ("\n" if reasoning_text else "") + bullets).strip()

        # If key_factors missing but evidence provided, store as key_factors.evidence
        key_factors = data.get("key_factors")
        if not key_factors and data.get("evidence"):
            key_factors = {"evidence": data.get("evidence")}

        return TradingDecision(
            decision=Decision(data.get("decision", "HOLD")),
            setup_quality=SetupQuality(setup_quality_raw),
            confidence=data.get("confidence", 0.0),
            confluence_score=data.get("confluence_score", 0),
            market_regime=market_regime,
            confluence_analysis=confluence_analysis,
            reasoning=reasoning_text,
            key_factors=key_factors or {},
            indicators_summary=indicators_summary,
            suggested_action=suggested_action,
            risk_assessment=risk_assessment,
            alternative_scenarios=data.get("alternative_scenarios", {}),
            monitoring_points=data.get("monitoring_points", []),
            meta=data.get("meta", {}),
            timestamp=datetime.now()
        )

    def _parse_suggested_action(self, action_data: Dict[str, Any]) -> SuggestedAction:
        """Parse suggested action from JSON.

        Supports both legacy shape with explicit stop_loss/take_profit_targets and
        the v2 concise shape with entry_level/invalidation_level/tp_levels.
        """
        from src.utils.models import (
            OrderType,
            OrderSide,
            StopLoss,
            TakeProfitTarget,
            TrailingStop
        )

        # v2 shape detection
        if "entry_level" in action_data or "invalidation_level" in action_data:
            entry_price = action_data.get("entry_level", 0.0)
            invalidation = action_data.get("invalidation_level", 0.0)
            tp_levels = action_data.get("tp_levels", []) or []
            rr_snapshot = action_data.get("rr_snapshot", {})

            stop_loss = StopLoss(
                price=invalidation,
                reasoning="invalidation_level",
                distance_pct=(abs(entry_price - invalidation) / entry_price * 100.0) if entry_price else 0.0,
                dollar_risk=0.0,
            )

            tp_targets: list[TakeProfitTarget] = []
            for i, price in enumerate(tp_levels[:3], start=1):
                rr = rr_snapshot.get(f"tp{i}", 0.0)
                tp_targets.append(TakeProfitTarget(
                    target=i,
                    price=price,
                    percentage_to_close=33,
                    reasoning="level",
                    rr_ratio=rr,
                ))

            trailing_stop = TrailingStop(
                activate_at_rr=2.0,
                trail_at_rr=1.0,
                method="EMA_20",
            )

            return SuggestedAction(
                type=OrderType(action_data.get("type", "LIMIT")),
                side=OrderSide(action_data.get("side", "BUY")),
                size_percentage=action_data.get("size_percentage", 0),
                quantity=action_data.get("quantity", 0.0),
                entry_price=entry_price,
                entry_price_rationale=action_data.get("execution_notes", ""),
                stop_loss=stop_loss,
                take_profit_targets=tp_targets,
                trailing_stop=trailing_stop,
                execution_notes=action_data.get("execution_notes", ""),
            )

        # Legacy shape fallback
        sl_data = action_data.get("stop_loss", {})
        stop_loss = StopLoss(
            price=sl_data.get("price", 0.0),
            reasoning=sl_data.get("reasoning", ""),
            distance_pct=sl_data.get("distance_pct", 0.0),
            dollar_risk=sl_data.get("dollar_risk", 0.0),
        )

        tp_targets = []
        for tp_data in action_data.get("take_profit_targets", []):
            tp_targets.append(
                TakeProfitTarget(
                    target=tp_data.get("target", 1),
                    price=tp_data.get("price", 0.0),
                    percentage_to_close=tp_data.get("percentage_to_close", 100),
                    reasoning=tp_data.get("reasoning", ""),
                    rr_ratio=tp_data.get("rr_ratio", 1.0),
                )
            )

        ts_data = action_data.get("trailing_stop", {})
        trailing_stop = TrailingStop(
            activate_at_rr=ts_data.get("activate_at_rr", 2.0),
            trail_at_rr=ts_data.get("trail_at_rr", 1.0),
            method=ts_data.get("method", "EMA_20"),
        )

        return SuggestedAction(
            type=OrderType(action_data.get("type", "LIMIT")),
            side=OrderSide(action_data.get("side", "BUY")),
            size_percentage=action_data.get("size_percentage", 100),
            quantity=action_data.get("quantity", 0.0),
            entry_price=action_data.get("entry_price", 0.0),
            entry_price_rationale=action_data.get("entry_price_rationale", ""),
            stop_loss=stop_loss,
            take_profit_targets=tp_targets,
            trailing_stop=trailing_stop,
            execution_notes=action_data.get("execution_notes", ""),
        )

    def validate_decision(
        self,
        decision: TradingDecision,
        min_confidence: float = 0.6,
        min_confluence: int = 4,
        min_rr: float = 2.2,
    ) -> tuple[bool, str]:
        """
        Validate trading decision before execution.

        Args:
            decision: Trading decision to validate
            min_confidence: Minimum confidence threshold

        Returns:
            Tuple of (is_valid, reason)
        """
        if decision.decision == Decision.HOLD:
            return True, "HOLD decision"

        if decision.confidence < min_confidence:
            return False, f"Confidence too low: {decision.confidence:.2f} < {min_confidence}"

        if decision.confluence_score < min_confluence:
            return False, f"Insufficient confluence: {decision.confluence_score} < {min_confluence}"

        if decision.setup_quality in [SetupQuality.C, SetupQuality.NO_SETUP]:
            return False, f"Setup quality too low: {decision.setup_quality}"

        if decision.risk_assessment.liquidity_check == "FAIL":
            return False, "Liquidity check failed"

        if decision.risk_assessment.risk_reward_ratio < min_rr:
            return False, f"R:R ratio too low: {decision.risk_assessment.risk_reward_ratio:.2f} < {min_rr:.2f}"

        if not decision.suggested_action:
            return False, "No suggested action provided"

        return True, "Decision validated"

    def _save_reasoning_log(self, asset: str, decision_data: Dict[str, Any], response: Any) -> None:
        """
        Save detailed AI reasoning to a separate log file for review.

        Args:
            asset: Trading asset
            decision_data: Parsed decision JSON
            response: Full API response object
        """
        import os
        from pathlib import Path

        # Create logs/ai_thinking directory if it doesn't exist
        log_dir = Path("logs/ai_thinking")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create filename with timestamp and asset
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = log_dir / f"{timestamp}_{asset}.md"

        # Format the reasoning log
        log_content = f"""# DeepSeek AI Reasoning Log

## Metadata
- **Asset**: {asset}
- **Timestamp**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Model**: {self.config.model}
- **Decision**: {decision_data.get('decision', 'N/A')}
- **Confidence**: {decision_data.get('confidence', 0):.2%}
- **Confluence Score**: {decision_data.get('confluence_score', 0)}/10
- **Setup Quality**: {decision_data.get('setup_quality', 'N/A')}

---

## 🧠 AI Reasoning Process

### Market Regime Analysis
**Primary Regime**: {decision_data.get('market_regime', {}).get('primary', 'N/A')}
**Strength**: {decision_data.get('market_regime', {}).get('strength', 0):.2f}
**Regime Aligned**: {decision_data.get('market_regime', {}).get('regime_aligned', False)}

### Confluence Analysis
{self._format_confluence_analysis(decision_data.get('confluence_analysis', {}))}

### Key Factors
{self._format_key_factors(decision_data.get('key_factors', {}))}

---

## 💭 Detailed Reasoning

{decision_data.get('reasoning', 'No reasoning provided')}

---

## 📊 Indicators Summary

### Trend Indicators
{json.dumps(decision_data.get('indicators_summary', {}).get('trend', {}), indent=2)}

### Momentum Indicators
{json.dumps(decision_data.get('indicators_summary', {}).get('momentum', {}), indent=2)}

### Volume Analysis
{json.dumps(decision_data.get('indicators_summary', {}).get('volume', {}), indent=2)}

### Volatility Metrics
{json.dumps(decision_data.get('indicators_summary', {}).get('volatility', {}), indent=2)}

---

## 🎯 Suggested Action
{self._format_suggested_action(decision_data.get('suggested_action'))}

---

## ⚠️ Risk Assessment
{self._format_risk_assessment(decision_data.get('risk_assessment', {}))}

---

## 🔮 Alternative Scenarios
{json.dumps(decision_data.get('alternative_scenarios', {}), indent=2)}

---

## 📍 Monitoring Points
{self._format_monitoring_points(decision_data.get('monitoring_points', []))}

---

## 🔢 Raw API Response
```json
{json.dumps(decision_data, indent=2)}
```

---

**Generated by Hyperliquid Trading Bot powered by DeepSeek Reasoner**
"""

        # Write to file
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)

        logger.debug(f"Saved AI reasoning log to: {log_file}")

    def _format_confluence_analysis(self, confluence: Dict[str, Any]) -> str:
        """Format confluence analysis for log."""
        return f"""
- **Trend Factors**: {confluence.get('trend_factors', [])}
- **Momentum Factors**: {confluence.get('momentum_factors', [])}
- **Volume Factors**: {confluence.get('volume_factors', [])}
- **Microstructure Factors**: {confluence.get('microstructure_factors', [])}
- **Total Confluence**: {confluence.get('total_confluence', 0)}/10
"""

    def _format_key_factors(self, factors: Dict[str, Any]) -> str:
        """Format key factors for log."""
        if not factors:
            return "No key factors identified"

        result = []
        for category, items in factors.items():
            result.append(f"\n**{category.replace('_', ' ').title()}**:")
            if isinstance(items, list):
                for item in items:
                    result.append(f"  - {item}")
            else:
                result.append(f"  - {items}")

        return "\n".join(result)

    def _format_suggested_action(self, action: Optional[Dict[str, Any]]) -> str:
        """Format suggested action for log."""
        if not action:
            return "**No action suggested** (HOLD decision)"

        return f"""
**Type**: {action.get('type', 'N/A')}
**Side**: {action.get('side', 'N/A')}
**Size**: {action.get('size_percentage', 0)}% of position
**Entry Price**: ${action.get('entry_price', 0):.2f}
**Entry Rationale**: {action.get('entry_price_rationale', 'N/A')}

**Stop Loss**:
- Price: ${action.get('stop_loss', {}).get('price', 0):.2f}
- Risk: {action.get('stop_loss', {}).get('risk_percent', 0):.2%}
- Rationale: {action.get('stop_loss', {}).get('rationale', 'N/A')}

**Take Profit Targets**:
{self._format_tp_targets(action.get('take_profit_targets', []))}

**Execution Notes**: {action.get('execution_notes', 'N/A')}
"""

    def _format_tp_targets(self, targets: List[Dict[str, Any]]) -> str:
        """Format take profit targets."""
        if not targets:
            return "  - No targets specified"

        result = []
        for i, target in enumerate(targets, 1):
            result.append(f"  - TP{i}: ${target.get('price', 0):.2f} ({target.get('size_percent', 0)}%) - R:R {target.get('rr_ratio', 0):.2f}")

        return "\n".join(result)

    def _format_risk_assessment(self, risk: Dict[str, Any]) -> str:
        """Format risk assessment for log."""
        return f"""
**Overall Risk**: {risk.get('overall_risk', 'N/A')}
**Edge Quality**: {risk.get('edge_quality', 0):.2%}
**Risk/Reward Ratio**: {risk.get('risk_reward_ratio', 0):.2f}
**Expected Value**: {risk.get('expected_value', 0):.2%}
**Liquidity Check**: {risk.get('liquidity_check', 'N/A')}
**Slippage Estimate**: {risk.get('slippage_estimate', 0):.2%}

**Risk Factors**:
{self._format_list(risk.get('risk_factors', []))}
"""

    def _format_monitoring_points(self, points: List[str]) -> str:
        """Format monitoring points."""
        if not points:
            return "- No specific monitoring points"

        return "\n".join([f"- {point}" for point in points])

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items."""
        if not items:
            return "  - None"

        return "\n".join([f"  - {item}" for item in items])
