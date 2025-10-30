"""Copy Trading Service - Monitor and copy trades from specified wallets."""

import asyncio
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.hyperliquid.client import HyperliquidClient


class CopyTrader:
    """
    Monitors specified wallet addresses and copies their trades.

    Features:
    - Real-time wallet monitoring
    - Automatic trade copying with position scaling
    - Filter by assets
    - Duplicate trade prevention
    """

    def __init__(self,
                 hl_client: HyperliquidClient,
                 wallets_to_copy: List[str],
                 position_multiplier: float = 1.0,
                 allowed_assets: Optional[List[str]] = None):
        """
        Initialize copy trader.

        Args:
            hl_client: Hyperliquid API client
            wallets_to_copy: List of wallet addresses to monitor
            position_multiplier: Scale factor for position sizes (1.0 = same size)
            allowed_assets: List of assets to copy (None = all assets)
        """
        self.hl_client = hl_client
        self.wallets_to_copy = [w.lower() for w in wallets_to_copy]
        self.position_multiplier = position_multiplier
        self.allowed_assets = allowed_assets or []

        # Track processed trades to avoid duplicates
        self.processed_trades: Set[str] = set()

        # Last check timestamp for each wallet
        self.last_check: Dict[str, datetime] = {
            wallet: datetime.now() - timedelta(minutes=5)
            for wallet in self.wallets_to_copy
        }

        logger.info(f"Copy Trader initialized: Monitoring {len(self.wallets_to_copy)} wallet(s)")
        logger.info(f"Wallets: {', '.join(self.wallets_to_copy)}")
        logger.info(f"Position multiplier: {self.position_multiplier}x")
        logger.info(f"Allowed assets: {', '.join(self.allowed_assets) if self.allowed_assets else 'ALL'}")

    async def check_for_new_trades(self) -> List[Dict]:
        """
        Check all monitored wallets for new trades.

        Returns:
            List of new trades to copy
        """
        new_trades = []

        for wallet in self.wallets_to_copy:
            try:
                trades = await self._get_wallet_trades(wallet)

                for trade in trades:
                    # Generate unique trade ID
                    trade_id = self._generate_trade_id(trade)

                    # Skip if already processed
                    if trade_id in self.processed_trades:
                        continue

                    # Skip if asset not in allowed list
                    asset = trade.get('coin', '').upper()
                    if self.allowed_assets and asset not in self.allowed_assets:
                        logger.debug(f"Skipping {asset} - not in allowed assets")
                        continue

                    # Skip if trade is too old (>5 minutes)
                    trade_time = self._parse_trade_time(trade)
                    if (datetime.now() - trade_time).total_seconds() > 300:
                        continue

                    # Mark as processed
                    self.processed_trades.add(trade_id)

                    # Add to new trades
                    new_trades.append({
                        'wallet': wallet,
                        'asset': asset,
                        'side': trade.get('side'),
                        'size': float(trade.get('sz', 0)),
                        'price': float(trade.get('px', 0)),
                        'time': trade_time,
                        'original_trade': trade
                    })

                    logger.info(f"🔔 New trade detected from {wallet[:10]}...:")
                    logger.info(f"   {trade.get('side')} {asset} | Size: {trade.get('sz')} @ ${trade.get('px')}")

                # Update last check time
                self.last_check[wallet] = datetime.now()

            except Exception as e:
                logger.error(f"Error checking wallet {wallet}: {e}")

        return new_trades

    async def _get_wallet_trades(self, wallet: str) -> List[Dict]:
        """
        Get recent trades for a wallet address.

        Args:
            wallet: Wallet address to check

        Returns:
            List of recent trades
        """
        try:
            # Use Hyperliquid API to get user fills (trades)
            # This endpoint returns recent trade activity for a user
            url = f"{self.hl_client.base_url}/info"

            payload = {
                "type": "userFills",
                "user": wallet
            }

            async with self.hl_client.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data if isinstance(data, list) else []
                else:
                    logger.warning(f"Failed to fetch trades for {wallet}: Status {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching wallet trades: {e}")
            return []

    def _generate_trade_id(self, trade: Dict) -> str:
        """Generate unique ID for a trade to prevent duplicates."""
        return f"{trade.get('coin')}_{trade.get('side')}_{trade.get('px')}_{trade.get('time')}"

    def _parse_trade_time(self, trade: Dict) -> datetime:
        """Parse trade timestamp."""
        try:
            # Hyperliquid uses millisecond timestamps
            timestamp_ms = int(trade.get('time', 0))
            return datetime.fromtimestamp(timestamp_ms / 1000)
        except:
            return datetime.now()

    async def copy_trade(self, trade: Dict) -> bool:
        """
        Copy a detected trade.

        Args:
            trade: Trade information dict

        Returns:
            True if trade copied successfully, False otherwise
        """
        try:
            asset = trade['asset']
            side = trade['side'].upper()
            original_size = trade['size']
            price = trade['price']

            # Scale position size
            copy_size = original_size * self.position_multiplier

            logger.info(f"📋 Copying trade: {side} {copy_size:.4f} {asset} @ ${price:.2f}")

            # Place order via Hyperliquid client
            order_result = await self.hl_client.place_order(
                asset=asset,
                side=side,
                size=copy_size,
                order_type="MARKET",  # Use market order for fast execution
                price=None
            )

            logger.success(f"✅ Trade copied successfully: {order_result}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to copy trade: {e}")
            return False

    def cleanup_old_trades(self, max_age_hours: int = 24):
        """Remove old trade IDs from memory to prevent unbounded growth."""
        # In production, you'd want to implement this properly
        # For now, we just clear if too many
        if len(self.processed_trades) > 10000:
            self.processed_trades.clear()
            logger.info("Cleared processed trades cache")
