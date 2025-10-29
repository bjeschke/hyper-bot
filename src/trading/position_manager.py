"""Position management for the trading bot."""

from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from src.utils.models import Position, TradingDecision, SuggestedAction


class PositionManager:
    """
    Manages open positions and their lifecycle.

    Tracks:
    - Position entries and exits
    - Take-profit levels
    - Trailing stops
    - Position duration
    """

    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.position_metadata: Dict[str, dict] = {}

    def add_position(
        self,
        position: Position,
        decision: TradingDecision,
        suggested_action: SuggestedAction
    ):
        """Add a new position to tracking."""
        position.entry_time = datetime.now()

        # Store suggested action details
        self.position_metadata[position.asset] = {
            "decision": decision,
            "suggested_action": suggested_action,
            "entry_time": position.entry_time,
            "tp_levels_hit": [],
            "trailing_stop_active": False,
            "trailing_stop_price": None
        }

        # Set take profit levels
        if suggested_action.take_profit_targets:
            if len(suggested_action.take_profit_targets) >= 1:
                position.take_profit_1 = suggested_action.take_profit_targets[0].price
            if len(suggested_action.take_profit_targets) >= 2:
                position.take_profit_2 = suggested_action.take_profit_targets[1].price
            if len(suggested_action.take_profit_targets) >= 3:
                position.take_profit_3 = suggested_action.take_profit_targets[2].price

        position.stop_loss = suggested_action.stop_loss.price

        self.positions[position.asset] = position

        logger.info(f"Added position: {position.side} {position.size} {position.asset} @ ${position.entry_price}")

    def update_position(self, asset: str, current_price: float):
        """Update position with current market price."""
        if asset not in self.positions:
            return

        position = self.positions[asset]
        position.current_price = current_price

        # Recalculate P&L
        if position.side == "LONG":
            position.unrealized_pnl = (current_price - position.entry_price) * position.size
        else:  # SHORT
            position.unrealized_pnl = (position.entry_price - current_price) * position.size

        if position.entry_price > 0:
            position.unrealized_pnl_percent = (position.unrealized_pnl / (position.entry_price * position.size)) * 100

    def check_take_profit_levels(self, asset: str) -> Optional[dict]:
        """
        Check if any take-profit levels have been hit.

        Returns:
            Dict with TP level info if hit, None otherwise
        """
        if asset not in self.positions or asset not in self.position_metadata:
            return None

        position = self.positions[asset]
        metadata = self.position_metadata[asset]
        current_price = position.current_price

        suggested_action = metadata["suggested_action"]
        tp_levels_hit = metadata["tp_levels_hit"]

        for i, tp_target in enumerate(suggested_action.take_profit_targets):
            tp_num = i + 1

            # Skip if already hit
            if tp_num in tp_levels_hit:
                continue

            # Check if TP hit
            if position.side == "LONG":
                tp_hit = current_price >= tp_target.price
            else:  # SHORT
                tp_hit = current_price <= tp_target.price

            if tp_hit:
                metadata["tp_levels_hit"].append(tp_num)

                logger.info(f"TP{tp_num} hit for {asset}: ${tp_target.price} (R:R {tp_target.rr_ratio:.2f})")

                return {
                    "tp_level": tp_num,
                    "tp_price": tp_target.price,
                    "percentage_to_close": tp_target.percentage_to_close,
                    "rr_ratio": tp_target.rr_ratio,
                    "reasoning": tp_target.reasoning
                }

        return None

    def check_stop_loss(self, asset: str) -> bool:
        """Check if stop loss has been hit."""
        if asset not in self.positions:
            return False

        position = self.positions[asset]

        if not position.stop_loss:
            return False

        if position.side == "LONG":
            stop_hit = position.current_price <= position.stop_loss
        else:  # SHORT
            stop_hit = position.current_price >= position.stop_loss

        if stop_hit:
            logger.warning(f"Stop loss hit for {asset}: ${position.stop_loss} (current: ${position.current_price})")

        return stop_hit

    def update_trailing_stop(self, asset: str):
        """Update trailing stop based on current price and rules."""
        if asset not in self.positions or asset not in self.position_metadata:
            return

        position = self.positions[asset]
        metadata = self.position_metadata[asset]
        suggested_action = metadata["suggested_action"]

        # Calculate current R (reward in multiples of initial risk)
        initial_risk = abs(position.entry_price - suggested_action.stop_loss.price)
        if initial_risk == 0:
            return

        if position.side == "LONG":
            current_r = (position.current_price - position.entry_price) / initial_risk
        else:
            current_r = (position.entry_price - position.current_price) / initial_risk

        # Check if we should activate trailing stop
        trailing_config = suggested_action.trailing_stop
        if current_r >= trailing_config.activate_at_rr and not metadata["trailing_stop_active"]:
            metadata["trailing_stop_active"] = True
            logger.info(f"Trailing stop activated for {asset} at {current_r:.2f}R")

        # Update trailing stop price if active
        if metadata["trailing_stop_active"]:
            trail_distance = initial_risk * trailing_config.trail_at_rr

            if position.side == "LONG":
                new_trail_stop = position.current_price - trail_distance
                if metadata["trailing_stop_price"] is None or new_trail_stop > metadata["trailing_stop_price"]:
                    metadata["trailing_stop_price"] = new_trail_stop
                    position.stop_loss = new_trail_stop
                    logger.debug(f"Updated trailing stop for {asset} to ${new_trail_stop:.2f}")
            else:  # SHORT
                new_trail_stop = position.current_price + trail_distance
                if metadata["trailing_stop_price"] is None or new_trail_stop < metadata["trailing_stop_price"]:
                    metadata["trailing_stop_price"] = new_trail_stop
                    position.stop_loss = new_trail_stop
                    logger.debug(f"Updated trailing stop for {asset} to ${new_trail_stop:.2f}")

    def get_position(self, asset: str) -> Optional[Position]:
        """Get position for an asset."""
        return self.positions.get(asset)

    def get_all_positions(self) -> List[Position]:
        """Get all open positions."""
        return list(self.positions.values())

    def remove_position(self, asset: str):
        """Remove a closed position from tracking."""
        if asset in self.positions:
            del self.positions[asset]
        if asset in self.position_metadata:
            del self.position_metadata[asset]
        logger.info(f"Removed position for {asset}")

    def get_position_duration(self, asset: str) -> Optional[float]:
        """Get position duration in hours."""
        if asset not in self.position_metadata:
            return None

        entry_time = self.position_metadata[asset]["entry_time"]
        duration = (datetime.now() - entry_time).total_seconds() / 3600

        return duration

    def should_close_by_time(self, asset: str, max_duration_hours: float = 24) -> bool:
        """Check if position should be closed based on time."""
        duration = self.get_position_duration(asset)

        if duration is None:
            return False

        position = self.positions.get(asset)
        if not position:
            return False

        # Close if position flat and held too long
        if duration > max_duration_hours and abs(position.unrealized_pnl_percent) < 0.5:
            logger.info(f"Position {asset} held for {duration:.1f}h with minimal P&L")
            return True

        return False

    def get_position_stats(self, asset: str) -> dict:
        """Get statistics for a position."""
        if asset not in self.positions or asset not in self.position_metadata:
            return {}

        position = self.positions[asset]
        metadata = self.position_metadata[asset]

        return {
            "asset": asset,
            "side": position.side,
            "size": position.size,
            "entry_price": position.entry_price,
            "current_price": position.current_price,
            "unrealized_pnl": position.unrealized_pnl,
            "unrealized_pnl_percent": position.unrealized_pnl_percent,
            "duration_hours": self.get_position_duration(asset),
            "tp_levels_hit": metadata.get("tp_levels_hit", []),
            "trailing_stop_active": metadata.get("trailing_stop_active", False),
            "stop_loss": position.stop_loss
        }
