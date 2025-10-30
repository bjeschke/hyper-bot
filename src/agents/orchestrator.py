"""Orchestrator for multi-agent trading system."""

import asyncio
from typing import Dict, Any, List
from loguru import logger

from src.agents.base_agent import AgentOpinion
from src.agents.chart_analyst import ChartAnalystAgent
from src.agents.liquidity_hunter import LiquidityHunterAgent
from src.agents.risk_manager import RiskManagerAgent
from src.agents.regime_expert import RegimeExpertAgent
from src.agents.supervisor import TradeSupervisorAgent
from src.utils.models import TradingDecision, Decision, SetupQuality


class TradingDeskOrchestrator:
    """
    Orchestrates multi-agent trading discussion.

    Coordinates 5 specialized agents:
    1. Chart Analyst - Technical indicators
    2. Liquidity Hunter - Liquidity grabs
    3. Risk Manager - Risk assessment
    4. Market Regime Expert - Market conditions
    5. Trade Supervisor - Final decision
    """

    def __init__(self, api_key: str):
        """Initialize all trading agents."""
        logger.info("🏢 Initializing Trading Desk (Multi-Agent System)")

        # Initialize agents
        self.chart_analyst = ChartAnalystAgent(api_key)
        self.liquidity_hunter = LiquidityHunterAgent(api_key)
        self.risk_manager = RiskManagerAgent(api_key)
        self.regime_expert = RegimeExpertAgent(api_key)
        self.supervisor = TradeSupervisorAgent(api_key)

        logger.info("✅ Trading Desk ready: 5 agents initialized")

    async def run_trading_discussion(self, context: Dict[str, Any]) -> TradingDecision:
        """
        Run a complete trading desk discussion.

        Args:
            context: Market data, indicators, etc.

        Returns:
            Final trading decision from supervisor
        """
        asset = context.get('asset', 'Unknown')
        logger.info(f"\n{'='*80}")
        logger.info(f"💼 TRADING DESK DISCUSSION - {asset}")
        logger.info(f"{'='*80}\n")

        discussion_history: List[AgentOpinion] = []

        # Phase 1: Initial Analysis (parallel)
        logger.info("📊 Phase 1: Initial Market Analysis")
        logger.info("-" * 80)

        # Chart Analyst speaks first
        logger.info(f"🔍 {self.chart_analyst.name} analyzing...")
        chart_opinion = await self.chart_analyst.analyze(context, discussion_history)
        discussion_history.append(chart_opinion)
        self._log_opinion(chart_opinion)
        await asyncio.sleep(2)  # Rate limit protection

        # Liquidity Hunter
        logger.info(f"\n🎯 {self.liquidity_hunter.name} analyzing...")
        liq_opinion = await self.liquidity_hunter.analyze(context, discussion_history)
        discussion_history.append(liq_opinion)
        self._log_opinion(liq_opinion)
        await asyncio.sleep(2)  # Rate limit protection

        # Market Regime Expert
        logger.info(f"\n🌊 {self.regime_expert.name} analyzing...")
        regime_opinion = await self.regime_expert.analyze(context, discussion_history)
        discussion_history.append(regime_opinion)
        self._log_opinion(regime_opinion)
        await asyncio.sleep(2)  # Rate limit protection

        # Phase 2: Risk Assessment
        logger.info(f"\n{'='*80}")
        logger.info("🛡️ Phase 2: Risk Management Review")
        logger.info("-" * 80)

        logger.info(f"⚖️ {self.risk_manager.name} assessing...")
        risk_opinion = await self.risk_manager.analyze(context, discussion_history)
        discussion_history.append(risk_opinion)
        self._log_opinion(risk_opinion)
        await asyncio.sleep(2)  # Rate limit protection

        # Phase 3: Supervisor Decision
        logger.info(f"\n{'='*80}")
        logger.info("👔 Phase 3: Supervisor Final Decision")
        logger.info("-" * 80)

        logger.info(f"⚡ {self.supervisor.name} deciding...")
        final_opinion = await self.supervisor.analyze(context, discussion_history)
        self._log_opinion(final_opinion)

        # Build TradingDecision from consensus
        decision = self._build_trading_decision(final_opinion, discussion_history, context)

        logger.info(f"\n{'='*80}")
        logger.info(f"🏁 FINAL DECISION: {decision.decision}")
        logger.info(f"   Confidence: {decision.confidence:.0%}")
        logger.info(f"   Setup Quality: {decision.setup_quality}")
        logger.info(f"{'='*80}\n")

        return decision

    def _log_opinion(self, opinion: AgentOpinion):
        """Log agent opinion in a nice format."""
        stance_emoji = {
            "BULLISH": "🟢",
            "BEARISH": "🔴",
            "NEUTRAL": "⚪",
            "ACCEPTABLE": "✅",
            "RISKY": "⚠️",
            "TOO_RISKY": "❌"
        }
        emoji = stance_emoji.get(opinion.stance, "❓")

        logger.info(f"{emoji} {opinion.stance} (Confidence: {opinion.confidence:.0%})")
        logger.info(f"   {opinion.reasoning[:150]}...")

        if opinion.key_points:
            for point in opinion.key_points[:2]:
                logger.info(f"   • {point}")

    def _build_trading_decision(self,
                                final_opinion: AgentOpinion,
                                discussion: List[AgentOpinion],
                                context: Dict[str, Any]) -> TradingDecision:
        """Build TradingDecision from agent consensus."""

        # Map supervisor decision to Decision enum
        decision_map = {
            "BUY": Decision.BUY,
            "SELL": Decision.SELL,
            "HOLD": Decision.HOLD
        }
        final_decision = decision_map.get(final_opinion.suggested_action, Decision.HOLD)

        # Determine setup quality from confidence
        if final_opinion.confidence >= 0.75:
            setup_quality = SetupQuality.A_PLUS
        elif final_opinion.confidence >= 0.60:
            setup_quality = SetupQuality.A
        elif final_opinion.confidence >= 0.45:
            setup_quality = SetupQuality.B
        else:
            setup_quality = SetupQuality.NO_SETUP

        # Count bullish/bearish agents
        bullish_count = sum(1 for op in discussion if op.stance == "BULLISH")
        bearish_count = sum(1 for op in discussion if op.stance == "BEARISH")

        # Build consensus summary
        key_factors = {
            "bullish": [],
            "bearish": [],
            "neutral": []
        }

        for opinion in discussion:
            if opinion.stance == "BULLISH":
                key_factors["bullish"].extend(opinion.key_points[:1])
            elif opinion.stance == "BEARISH":
                key_factors["bearish"].extend(opinion.key_points[:1])

        # Calculate confluence score based on agent agreement
        if bullish_count >= 3 or bearish_count >= 3:
            confluence_score = 8  # Strong agreement
        elif bullish_count >= 2 or bearish_count >= 2:
            confluence_score = 6  # Moderate agreement
        else:
            confluence_score = 3  # Mixed signals

        # Build reasoning summary
        reasoning = f"**Multi-Agent Consensus:** {final_opinion.reasoning}\n\n"
        reasoning += f"**Agent Votes:** {bullish_count} Bullish, {bearish_count} Bearish\n"
        for opinion in discussion:
            reasoning += f"- {opinion.agent_name}: {opinion.stance} ({opinion.confidence:.0%})\n"

        # Create TradingDecision
        from src.utils.models import (
            MarketRegime, MarketRegimeData, ConfluenceAnalysis, IndicatorsSummary,
            SuggestedAction, RiskAssessment,
            OrderType, OrderSide, StopLoss, TakeProfitTarget, TrailingStop
        )

        # Extract current price from context
        price = context.get('price', 0.0)

        # Build suggested action if not HOLD
        suggested_action = None
        if final_decision != Decision.HOLD:
            side = OrderSide.BUY if final_decision == Decision.BUY else OrderSide.SELL
            entry_price = price
            stop_distance = price * 0.01  # 1% stop
            stop_loss_price = entry_price - stop_distance if side == OrderSide.BUY else entry_price + stop_distance

            suggested_action = SuggestedAction(
                type=OrderType.LIMIT,
                side=side,
                size_percentage=100,
                quantity=0.0,
                entry_price=entry_price,
                entry_price_rationale=final_opinion.reasoning[:100],
                stop_loss=StopLoss(
                    price=stop_loss_price,
                    reasoning="Multi-agent consensus stop level",
                    distance_pct=1.0,
                    dollar_risk=0.0
                ),
                take_profit_targets=[
                    TakeProfitTarget(target=1, price=entry_price * 1.02, percentage_to_close=50, reasoning="TP1", rr_ratio=2.0),
                    TakeProfitTarget(target=2, price=entry_price * 1.04, percentage_to_close=30, reasoning="TP2", rr_ratio=4.0),
                    TakeProfitTarget(target=3, price=entry_price * 1.06, percentage_to_close=20, reasoning="TP3", rr_ratio=6.0),
                ],
                trailing_stop=TrailingStop(activate_at_rr=2.0, trail_at_rr=1.0, method="EMA_20"),
                execution_notes="Multi-agent consensus trade"
            )

        return TradingDecision(
            decision=final_decision,
            setup_quality=setup_quality,
            confidence=final_opinion.confidence,
            confluence_score=confluence_score,
            market_regime=MarketRegimeData(primary=MarketRegime.RANGING, strength=0.5, regime_aligned=True),
            confluence_analysis=ConfluenceAnalysis(
                trend_score=1 if bullish_count > bearish_count else -1,
                trend_details="Multi-agent analysis",
                momentum_score=bullish_count - bearish_count,
                momentum_details=f"{bullish_count} bullish, {bearish_count} bearish",
                volume_score=1,
                volume_details="Analyzed by agents",
                microstructure_score=1,
                microstructure_details="Multi-agent consensus",
                total_confluence=bullish_count - bearish_count
            ),
            reasoning=reasoning,
            key_factors=key_factors,
            indicators_summary=IndicatorsSummary(
                trend=context.get('indicators', {}).get('trend', {}),
                momentum=context.get('indicators', {}).get('momentum', {}),
                volume=context.get('indicators', {}).get('volume', {}),
                volatility=context.get('indicators', {}).get('volatility', {})
            ),
            suggested_action=suggested_action,
            risk_assessment=RiskAssessment(
                overall_risk="MEDIUM",
                risk_factors=["Multi-agent system"],
                edge_quality=final_opinion.confidence,
                risk_reward_ratio=2.5,
                expected_value=0.0,
                position_size_modifier=1.0,
                slippage_estimate=0.0,
                liquidity_check="PASS",
                funding_impact=0.0,
                margin_safety=50.0,
                liquidation_distance_pct=20.0
            ),
            alternative_scenarios={},
            monitoring_points=[],
            meta={
                "multi_agent": True,
                "agent_opinions": [str(op) for op in discussion],
                "consensus_level": confluence_score
            }
        )
