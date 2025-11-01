"""Performance Tracker - Tracks daily P&L, trade count, and enforces limits."""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger


class PerformanceTracker:
    """
    Tracks trading performance and enforces risk limits.

    Features:
    - Daily P&L tracking
    - Trade count limits
    - Loss streak detection
    - Auto-stop on daily loss limit
    """

    def __init__(self, data_dir: str = "data/performance"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.perf_file = self.data_dir / "daily_performance.json"
        self.trades_file = self.data_dir / "trades_log.json"

        # Load or initialize data
        self.daily_data = self._load_daily_data()
        self.trades_log = self._load_trades_log()

    def _load_daily_data(self) -> Dict:
        """Load daily performance data."""
        if self.perf_file.exists():
            with open(self.perf_file, 'r') as f:
                return json.load(f)
        return self._init_daily_data()

    def _init_daily_data(self) -> Dict:
        """Initialize daily data structure."""
        return {
            "date": str(date.today()),
            "starting_balance": 0.0,
            "current_balance": 0.0,
            "daily_pnl": 0.0,
            "daily_pnl_pct": 0.0,
            "trades_today": 0,
            "wins_today": 0,
            "losses_today": 0,
            "consecutive_losses": 0,
            "is_trading_stopped": False,
            "stop_reason": None,
            "last_trade_time": None
        }

    def _load_trades_log(self) -> List[Dict]:
        """Load trades log."""
        if self.trades_file.exists():
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        return []

    def _save_data(self):
        """Save all data to disk."""
        with open(self.perf_file, 'w') as f:
            json.dump(self.daily_data, f, indent=2)
        with open(self.trades_file, 'w') as f:
            json.dump(self.trades_log, f, indent=2)

    def reset_if_new_day(self):
        """Reset daily counters if it's a new day."""
        today = str(date.today())
        if self.daily_data["date"] != today:
            logger.info(f"📅 New trading day: {today}")

            # Archive yesterday's data
            if self.daily_data["date"]:
                archive_file = self.data_dir / f"daily_{self.daily_data['date']}.json"
                with open(archive_file, 'w') as f:
                    json.dump(self.daily_data, f, indent=2)

            # Reset daily data but keep current balance as starting balance
            old_balance = self.daily_data["current_balance"]
            self.daily_data = self._init_daily_data()
            self.daily_data["starting_balance"] = old_balance
            self.daily_data["current_balance"] = old_balance
            self._save_data()

    def update_balance(self, new_balance: float):
        """Update current balance and calculate daily P&L."""
        self.reset_if_new_day()

        old_balance = self.daily_data["current_balance"]
        self.daily_data["current_balance"] = new_balance

        if self.daily_data["starting_balance"] == 0:
            self.daily_data["starting_balance"] = new_balance

        # Calculate daily P&L
        starting = self.daily_data["starting_balance"]
        self.daily_data["daily_pnl"] = new_balance - starting
        self.daily_data["daily_pnl_pct"] = (
            ((new_balance - starting) / starting * 100) if starting > 0 else 0
        )

        self._save_data()

        # Check daily loss limit
        if self.daily_data["daily_pnl_pct"] <= -3.0:
            self.stop_trading("Daily loss limit reached: -3%")
            return False
        elif self.daily_data["daily_pnl_pct"] <= -2.0:
            logger.warning(f"⚠️  DAILY LOSS AT -2%! Next trade will be 50% smaller.")

        return True

    def can_trade(self) -> tuple[bool, Optional[str]]:
        """
        Check if trading is allowed.

        Returns:
            (can_trade, reason_if_not)
        """
        self.reset_if_new_day()

        # Check if trading is stopped
        if self.daily_data["is_trading_stopped"]:
            return False, self.daily_data["stop_reason"]

        # Check max trades per day - DISABLED
        # if self.daily_data["trades_today"] >= 8:
        #     self.stop_trading("Max trades per day reached (8)")
        #     return False, "Max 8 trades per day"

        # Check if too many consecutive losses (4)
        if self.daily_data["consecutive_losses"] >= 4:
            self.stop_trading("Too many consecutive losses (4)")
            return False, "4 consecutive losses"

        # Check for cooldown after losses
        if self.daily_data["consecutive_losses"] >= 2:
            last_trade = self.daily_data.get("last_trade_time")
            if last_trade:
                hours_since = (datetime.now() - datetime.fromisoformat(last_trade)).total_seconds() / 3600
                required_cooldown = 2 if self.daily_data["consecutive_losses"] == 2 else 4

                if hours_since < required_cooldown:
                    return False, f"Cooldown: {required_cooldown}h after {self.daily_data['consecutive_losses']} losses"

        return True, None

    def get_position_size_modifier(self) -> float:
        """
        Get position size modifier based on performance.

        Returns:
            multiplier (0.5 - 1.0)
        """
        self.reset_if_new_day()

        modifier = 1.0

        # Reduce size after losses
        if self.daily_data["consecutive_losses"] >= 3:
            modifier *= 0.5

        # Reduce size near daily loss warning (-2%)
        if -2.5 < self.daily_data["daily_pnl_pct"] <= -2.0:
            modifier *= 0.5

        # Reduce size on 7th or 8th trade
        if self.daily_data["trades_today"] >= 6:
            modifier *= 0.75

        return modifier

    def should_only_trade_aplus_setups(self) -> bool:
        """Check if we should only trade A+ setups (Confidence >0.75, Confluence >7)."""
        self.reset_if_new_day()
        return self.daily_data["trades_today"] >= 6

    def log_trade(self, asset: str, side: str, entry_price: float, size: float,
                   stop_loss: float, take_profit: List[float], confidence: float,
                   confluence: int, reason: str):
        """Log a new trade."""
        self.reset_if_new_day()

        trade = {
            "timestamp": datetime.now().isoformat(),
            "date": str(date.today()),
            "asset": asset,
            "side": side,
            "entry_price": entry_price,
            "size": size,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "confidence": confidence,
            "confluence": confluence,
            "reason": reason,
            "status": "OPEN"
        }

        self.trades_log.append(trade)
        self.daily_data["trades_today"] += 1
        self.daily_data["last_trade_time"] = datetime.now().isoformat()

        self._save_data()

        logger.info(f"📝 Trade #{self.daily_data['trades_today']} logged: {side} {asset} @ ${entry_price:,.2f}")

    def log_trade_close(self, asset: str, exit_price: float, pnl: float, pnl_pct: float):
        """Log trade close and update stats."""
        self.reset_if_new_day()

        # Find and update the open trade
        for trade in reversed(self.trades_log):
            if trade["asset"] == asset and trade["status"] == "OPEN":
                trade["exit_price"] = exit_price
                trade["pnl"] = pnl
                trade["pnl_pct"] = pnl_pct
                trade["close_timestamp"] = datetime.now().isoformat()
                trade["status"] = "WIN" if pnl > 0 else "LOSS"

                # Update stats
                if pnl > 0:
                    self.daily_data["wins_today"] += 1
                    self.daily_data["consecutive_losses"] = 0
                    logger.success(f"✅ TRADE WIN: {asset} +{pnl_pct:.2f}% (${pnl:,.2f})")
                else:
                    self.daily_data["losses_today"] += 1
                    self.daily_data["consecutive_losses"] += 1
                    logger.error(f"❌ TRADE LOSS: {asset} {pnl_pct:.2f}% (${pnl:,.2f})")

                self._save_data()
                break

    def stop_trading(self, reason: str):
        """Stop trading for the day."""
        self.daily_data["is_trading_stopped"] = True
        self.daily_data["stop_reason"] = reason
        self._save_data()
        logger.critical(f"🛑 TRADING STOPPED: {reason}")

    def get_daily_stats(self) -> Dict:
        """Get current daily statistics."""
        self.reset_if_new_day()
        return {
            "date": self.daily_data["date"],
            "daily_pnl": self.daily_data["daily_pnl"],
            "daily_pnl_pct": self.daily_data["daily_pnl_pct"],
            "trades_today": self.daily_data["trades_today"],
            "wins": self.daily_data["wins_today"],
            "losses": self.daily_data["losses_today"],
            "win_rate": (self.daily_data["wins_today"] / self.daily_data["trades_today"] * 100)
                        if self.daily_data["trades_today"] > 0 else 0,
            "consecutive_losses": self.daily_data["consecutive_losses"],
            "is_stopped": self.daily_data["is_trading_stopped"]
        }
