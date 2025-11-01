"""Hyperliquid API client."""

import asyncio
import hashlib
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import aiohttp
from loguru import logger
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

from src.config import HyperliquidConfig
from src.utils.models import (
    MarketData,
    MultiTimeframeData,
    OrderbookData,
    Position,
    Portfolio,
    DerivativesData,
)


class HyperliquidClient:
    """
    Hyperliquid DEX API client.

    Handles all API interactions with Hyperliquid including:
    - Market data retrieval
    - Order placement
    - Position management
    - Account information
    """

    def __init__(self, config: HyperliquidConfig):
        self.config = config
        self.base_url = config.url  # For trading
        self.data_url = config.data_url  # For market data
        self.session: Optional[aiohttp.ClientSession] = None

        # Setup wallet for signing
        self.account = Account.from_key(config.private_key)
        self.wallet_address = config.wallet_address

        # Initialize official Hyperliquid SDK
        # Trading SDK uses testnet/mainnet based on config
        sdk_trading_url = constants.TESTNET_API_URL if config.testnet else constants.MAINNET_API_URL
        # Data SDK uses mainnet if use_mainnet_data is true
        sdk_data_url = constants.MAINNET_API_URL if config.use_mainnet_data else sdk_trading_url

        self.info = Info(sdk_data_url, skip_ws=True)  # Market data (for analysis)
        self.info_trading = Info(sdk_trading_url, skip_ws=True)  # Market data (for order prices)
        self.exchange = Exchange(self.account, sdk_trading_url)  # Trading

        logger.info(f"Initialized Hyperliquid client for wallet: {self.wallet_address}")
        logger.info(f"Trading URL: {sdk_trading_url}")
        logger.info(f"Market Data URL: {sdk_data_url}")
        if config.use_mainnet_data and config.testnet:
            logger.info("⚠️  Using MAINNET data for analysis, TESTNET for trading")

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _sign_l1_action(self, action: Dict[str, Any], nonce: int) -> Dict[str, Any]:
        """
        Sign an L1 action using EIP-712 typed data signing.

        This is how Hyperliquid authenticates requests - not with API keys,
        but by signing messages with your wallet's private key.
        """
        # Hyperliquid uses a specific message format for signing
        # The message includes timestamp and action data
        timestamp = int(time.time() * 1000)

        # Create connection ID for the action
        connection_id = {
            "type": "l1Action",
            "data": action,
            "timestamp": timestamp,
            "nonce": nonce
        }

        # For Hyperliquid, we use personal_sign (not typed data)
        # This is simpler and what Hyperliquid expects
        message_str = json.dumps(connection_id, separators=(',', ':'), sort_keys=True)
        message = encode_defunct(text=message_str)

        # Sign with private key
        signed_message = self.account.sign_message(message)

        return {
            "action": action,
            "nonce": nonce,
            "signature": {
                "r": hex(signed_message.r),
                "s": hex(signed_message.s),
                "v": signed_message.v
            },
            "timestamp": timestamp
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        authenticated: bool = False
    ) -> Dict[str, Any]:
        """Make HTTP request to Hyperliquid API."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        # For authenticated requests, we need to sign the action
        if authenticated and data:
            nonce = int(time.time() * 1000)
            signed_data = self._sign_l1_action(data, nonce)
            data = signed_data

        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error(f"API request timeout for {endpoint}")
            raise

    async def get_ticker(self, asset: str) -> Dict[str, Any]:
        """Get current ticker data for an asset."""
        endpoint = "/info"
        data = {"type": "allMids"}
        response = await self._request("POST", endpoint, data)

        # Response is a dict of asset -> price
        # Return a ticker-like structure
        if asset in response:
            return {
                "coin": asset,
                "lastPx": response[asset],
                "markPx": response[asset],
                "indexPx": response[asset]
            }
        else:
            raise ValueError(f"Asset {asset} not found in market data")

    async def get_market_data(self, asset: str, timeframe: str = "1h") -> MarketData:
        """Get market data for a specific timeframe."""
        # Get current ticker
        ticker = await self.get_ticker(asset)

        # Get historical data for the timeframe
        candles = await self.get_candles(asset, timeframe, limit=2)

        if not candles or len(candles) < 1:
            raise ValueError(f"No candle data available for {asset} {timeframe}")

        latest = candles[-1]

        return MarketData(
            asset=asset,
            timestamp=datetime.fromtimestamp(latest['time'] / 1000),
            price=float(latest['close']),
            mark_price=float(ticker.get('markPx', latest['close'])),
            index_price=float(ticker.get('indexPx', latest['close'])),
            volume=float(latest['volume']),
            high=float(latest['high']),
            low=float(latest['low']),
            price_change=((float(latest['close']) - float(latest['open'])) / float(latest['open'])) * 100,
            volatility=self._calculate_volatility(candles)
        )

    async def get_multi_timeframe_data(self, asset: str) -> MultiTimeframeData:
        """Get market data across multiple timeframes."""
        timeframes = ["1m", "5m", "15m", "1h", "4h", "24h"]

        # Fetch all timeframes concurrently
        tasks = [self.get_market_data(asset, tf) for tf in timeframes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Get current ticker for prices
        ticker = await self.get_ticker(asset)

        data = MultiTimeframeData(
            asset=asset,
            timestamp=datetime.now(),
            current_price=float(ticker.get('lastPx', 0)),
            mark_price=float(ticker.get('markPx', 0)),
            index_price=float(ticker.get('indexPx', 0))
        )

        # Assign data to respective timeframes
        for i, tf in enumerate(timeframes):
            if not isinstance(results[i], Exception):
                setattr(data, f"data_{tf.replace('m', 'm').replace('h', 'h')}", results[i])

        return data

    async def get_candles(
        self,
        asset: str,
        timeframe: str = "1h",
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical candle data.

        Args:
            asset: Asset symbol (e.g., "BTC")
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to retrieve
            start_time: Start time for candles
            end_time: End time for candles
        """
        endpoint = "/info"

        # Calculate end time (now) and start time based on limit
        end_ts = int(time.time() * 1000) if not end_time else int(end_time.timestamp() * 1000)

        # Timeframe mapping - Hyperliquid uses specific intervals
        timeframe_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "1h": "1h",
            "4h": "4h",
            "24h": "1d"  # 24h maps to 1d
        }
        interval = timeframe_map.get(timeframe, timeframe)

        data = {
            "type": "candleSnapshot",
            "req": {
                "coin": asset,
                "interval": interval,
                "startTime": int(start_time.timestamp() * 1000) if start_time else end_ts - (limit * 3600000),
                "endTime": end_ts
            }
        }

        try:
            response = await self._request("POST", endpoint, data)

            # Parse response - Hyperliquid returns array of candles
            if isinstance(response, list):
                candles = []
                for candle in response:
                    candles.append({
                        'time': candle['t'],
                        'open': float(candle['o']),
                        'high': float(candle['h']),
                        'low': float(candle['l']),
                        'close': float(candle['c']),
                        'volume': float(candle['v'])
                    })
                return candles[-limit:] if len(candles) > limit else candles
        except Exception as e:
            logger.warning(f"Failed to get candles for {asset} {timeframe}: {e}")
            # Return empty list so bot can continue
            return []

        return []

    async def get_orderbook(self, asset: str, depth: int = 20) -> OrderbookData:
        """Get orderbook data with depth."""
        endpoint = "/info"
        data = {"type": "l2Book", "coin": asset}
        response = await self._request("POST", endpoint, data)

        bids = [(float(b['px']), float(b['sz'])) for b in response.get('bids', [])]
        asks = [(float(a['px']), float(a['sz'])) for a in response.get('asks', [])]

        bid_liquidity = sum(price * size for price, size in bids)
        ask_liquidity = sum(price * size for price, size in asks)

        # Calculate spread
        if bids and asks:
            best_bid = bids[0][0]
            best_ask = asks[0][0]
            spread_usd = best_ask - best_bid
            spread_bps = (spread_usd / best_bid) * 10000
        else:
            spread_usd = 0
            spread_bps = 0

        # Calculate orderbook imbalance
        total_liquidity = bid_liquidity + ask_liquidity
        imbalance = ((bid_liquidity - ask_liquidity) / total_liquidity * 100) if total_liquidity > 0 else 0

        return OrderbookData(
            bids=bids,
            asks=asks,
            bid_liquidity=bid_liquidity,
            ask_liquidity=ask_liquidity,
            spread_bps=spread_bps,
            spread_usd=spread_usd,
            imbalance=imbalance,
            timestamp=datetime.now()
        )

    async def get_funding_rate(self, asset: str) -> DerivativesData:
        """Get funding rate and derivatives data."""
        endpoint = "/info"
        data = {"type": "metaAndAssetCtxs"}
        response = await self._request("POST", endpoint, data)

        # Find the asset in the response
        funding_rate = 0.0
        open_interest = 0.0

        if isinstance(response, list) and len(response) >= 2:
            # response[0] is meta, response[1] is assetCtxs
            asset_ctxs = response[1]
            for ctx in asset_ctxs:
                if ctx.get('coin') == asset:
                    funding_rate = float(ctx.get('funding', 0))
                    open_interest = float(ctx.get('openInterest', 0))
                    break
        else:
            # Fallback to default response structure
            response = await self._request("POST", "/info", {"type": "userFunding", "user": self.wallet_address})
            for item in response:
                if item.get('coin') == asset:
                    funding_rate = float(item.get('fundingRate', 0))
                    break

        funding_rate_annual = funding_rate * 3 * 365  # 8h funding * 3 per day * 365 days

        # Get historical funding to determine trend
        funding_history = []
        funding_trend = "neutral"
        if len(funding_history) >= 3:
            recent_avg = sum(float(f['rate']) for f in funding_history[-3:]) / 3
            if recent_avg > funding_rate * 1.2:
                funding_trend = "decreasing"
            elif recent_avg < funding_rate * 0.8:
                funding_trend = "increasing"

        # Calculate time to next funding (every 8 hours)
        now = datetime.now()
        next_funding_hour = ((now.hour // 8) + 1) * 8
        next_funding = now.replace(hour=next_funding_hour % 24, minute=0, second=0)
        if next_funding_hour >= 24:
            next_funding += timedelta(days=1)
        time_to_funding = int((next_funding - now).total_seconds() / 60)

        # Interpret funding rate
        if funding_rate > 0.05:
            ratio_interpretation = "Extremely long-biased, shorts have edge"
        elif funding_rate > 0.02:
            ratio_interpretation = "Long-biased, slightly overcrowded"
        elif funding_rate < -0.02:
            ratio_interpretation = "Short-biased, potential short squeeze"
        else:
            ratio_interpretation = "Balanced, no clear bias"

        return DerivativesData(
            funding_rate=funding_rate,
            funding_rate_annual=funding_rate_annual,
            funding_trend=funding_trend,
            time_to_funding=time_to_funding,
            open_interest=open_interest,
            oi_change_24h=0.0,  # Would need historical OI data
            oi_trend="neutral",
            long_short_ratio=1.0,  # Would need specific API endpoint
            ratio_interpretation=ratio_interpretation
        )

    async def get_account_state(self) -> Portfolio:
        """Get account balance and positions."""
        endpoint = "/info"
        data = {"type": "clearinghouseState", "user": self.wallet_address}
        response = await self._request("POST", endpoint, data)

        margin_summary = response.get('marginSummary', {})
        positions_data = response.get('positions', [])

        total_value = float(margin_summary.get('accountValue', 0))
        used_margin = float(margin_summary.get('totalMarginUsed', 0))
        available_balance = total_value - used_margin

        positions = []
        total_unrealized_pnl = 0.0

        for pos_data in positions_data:
            if float(pos_data.get('szi', 0)) != 0:  # Only include non-zero positions
                position = self._parse_position(pos_data)
                positions.append(position)
                total_unrealized_pnl += position.unrealized_pnl

        # Calculate exposure
        exposure_value = sum(abs(p.size * p.current_price) for p in positions)
        exposure_percent = (exposure_value / total_value * 100) if total_value > 0 else 0

        return Portfolio(
            total_value=total_value,
            available_balance=available_balance,
            used_margin=used_margin,
            margin_usage_percent=(used_margin / total_value * 100) if total_value > 0 else 0,
            exposure_percent=exposure_percent,
            positions=positions,
            unrealized_pnl=total_unrealized_pnl
        )

    def _parse_position(self, pos_data: Dict[str, Any]) -> Position:
        """Parse position data from API response."""
        size = float(pos_data.get('szi', 0))
        side = "LONG" if size > 0 else "SHORT"

        entry_price = float(pos_data.get('entryPx', 0))
        current_price = float(pos_data.get('markPx', entry_price))
        leverage = float(pos_data.get('leverage', {}).get('value', 1))

        # Calculate unrealized PnL
        if side == "LONG":
            unrealized_pnl = (current_price - entry_price) * abs(size)
        else:
            unrealized_pnl = (entry_price - current_price) * abs(size)

        unrealized_pnl_percent = (unrealized_pnl / (entry_price * abs(size)) * 100) if entry_price > 0 else 0

        return Position(
            asset=pos_data.get('coin', ''),
            side=side,
            size=abs(size),
            entry_price=entry_price,
            current_price=current_price,
            leverage=leverage,
            margin_used=float(pos_data.get('marginUsed', 0)),
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
            liquidation_price=float(pos_data.get('liquidationPx', 0)),
            position_id=pos_data.get('positionId')
        )

    def _get_asset_index(self, asset: str) -> int:
        """Get asset index for perpetuals. BTC=0, ETH=1, etc."""
        # Common perpetuals indices
        asset_indices = {
            "BTC": 0, "ETH": 1, "SOL": 2, "ARB": 3, "AVAX": 4,
            "BNB": 5, "DOGE": 6, "MATIC": 7, "OP": 8, "SUI": 9
        }
        return asset_indices.get(asset, 0)

    async def place_order(
        self,
        asset: str,
        side: str,
        size: float,
        order_type: str = "LIMIT",
        price: Optional[float] = None,
        reduce_only: bool = False,
        post_only: bool = False
    ) -> Dict[str, Any]:
        """
        Place an order on Hyperliquid using official SDK.

        Args:
            asset: Asset symbol (e.g., "BTC", "ETH")
            side: "BUY" or "SELL"
            size: Order size
            order_type: "MARKET" or "LIMIT"
            price: Limit price (required for LIMIT orders)
            reduce_only: Only reduce existing position
            post_only: Only maker orders
        """
        # Get current market price if MARKET order
        if order_type == "MARKET":
            # Use trading SDK to get current price (NOT data SDK - need correct network price!)
            all_mids = await asyncio.to_thread(self.info_trading.all_mids)
            current_price = float(all_mids[asset])

            # Add moderate slippage for market orders (2% to find liquidity)
            if side.upper() == "BUY":
                price = round(current_price * 1.02)  # 2% above for buys
            else:
                price = round(current_price * 0.98)  # 2% below for sells
        else:
            if price is None:
                raise ValueError("Price is required for LIMIT orders")
            price = round(price)  # Round to integer for tick size

        # Get metadata for proper size rounding (use trading info for correct network metadata)
        meta = await asyncio.to_thread(self.info_trading.meta)
        asset_meta = None
        for universe_asset in meta["universe"]:
            if universe_asset["name"] == asset:
                asset_meta = universe_asset
                break

        if asset_meta:
            sz_decimals = asset_meta["szDecimals"]
            size = round(size, sz_decimals)

        # Determine order type for SDK
        if order_type == "MARKET":
            # Market orders use IOC (Immediate or Cancel)
            sdk_order_type = {"limit": {"tif": "Ioc"}}
        elif post_only:
            sdk_order_type = {"limit": {"tif": "Alo"}}  # Add Liquidity Only
        else:
            sdk_order_type = {"limit": {"tif": "Gtc"}}  # Good til Cancel

        is_buy = side.upper() == "BUY"

        logger.info(f"Placing {order_type} {side} order: {size} {asset} @ ${price:,.0f}")

        try:
            # Use official SDK to place order (wrapped in thread for async)
            order_result = await asyncio.to_thread(
                self.exchange.order,
                name=asset,
                is_buy=is_buy,
                sz=size,
                limit_px=price,
                order_type=sdk_order_type,
                reduce_only=reduce_only
            )

            logger.debug(f"Order response: {order_result}")

            # Check response status
            if order_result.get("status") == "ok":
                data = order_result.get("response", {}).get("data", {})
                statuses = data.get("statuses", [])

                if statuses and "filled" in statuses[0]:
                    filled_data = statuses[0]["filled"]
                    logger.success(f"✅ Order FILLED: {filled_data['totalSz']} @ ${filled_data['avgPx']}")
                    return {
                        "status": "filled",
                        "size": filled_data['totalSz'],
                        "price": filled_data['avgPx'],
                        "order_id": filled_data.get('oid')
                    }
                elif statuses and "resting" in statuses[0]:
                    oid = statuses[0]["resting"]["oid"]
                    logger.success(f"✅ Order placed (resting): Order ID {oid}")
                    return {"order_id": oid, "status": "resting"}
                elif statuses and "error" in statuses[0]:
                    error_msg = statuses[0]["error"]
                    logger.error(f"❌ Order rejected: {error_msg}")
                    raise Exception(f"Order rejected: {error_msg}")

            return order_result

        except Exception as e:
            logger.error(f"❌ Failed to place order: {e}")
            raise

    async def place_trigger_order(
        self,
        asset: str,
        side: str,
        size: float,
        trigger_price: float,
        trigger_type: str,  # "tp" or "sl"
        is_market: bool = True
    ) -> Dict[str, Any]:
        """
        Place a trigger order (Stop Loss or Take Profit) on Hyperliquid.

        Args:
            asset: Asset symbol (e.g., "BTC", "ETH")
            side: "BUY" or "SELL" (direction when triggered)
            size: Order size
            trigger_price: Price at which the order triggers
            trigger_type: "tp" (take profit) or "sl" (stop loss)
            is_market: Execute as market order when triggered (default True)
        """
        # Get metadata for proper size rounding (use trading info for correct network metadata)
        meta = await asyncio.to_thread(self.info_trading.meta)
        asset_meta = None
        for universe_asset in meta["universe"]:
            if universe_asset["name"] == asset:
                asset_meta = universe_asset
                break

        if asset_meta:
            sz_decimals = asset_meta["szDecimals"]
            size = round(size, sz_decimals)

        # Round trigger price to integer
        trigger_price = round(trigger_price)

        logger.info(f"Placing {trigger_type.upper()} trigger order: {size} {asset} @ ${trigger_price:,.0f}")

        # Build trigger order type
        order_type = {
            "trigger": {
                "isMarket": is_market,
                "triggerPx": str(trigger_price),
                "tpsl": trigger_type
            }
        }

        is_buy = side.upper() == "BUY"

        try:
            # Use official SDK to place trigger order
            order_result = await asyncio.to_thread(
                self.exchange.order,
                name=asset,
                is_buy=is_buy,
                sz=size,
                limit_px=trigger_price,
                order_type=order_type,
                reduce_only=True  # SL/TP should always reduce position
            )

            logger.debug(f"Trigger order response: {order_result}")

            # Check response status
            if order_result.get("status") == "ok":
                data = order_result.get("response", {}).get("data", {})
                statuses = data.get("statuses", [])

                if statuses and "resting" in statuses[0]:
                    oid = statuses[0]["resting"]["oid"]
                    logger.success(f"✅ {trigger_type.upper()} order placed: Order ID {oid}")
                    return {"order_id": oid, "status": "resting", "type": trigger_type}
                elif statuses and "error" in statuses[0]:
                    error_msg = statuses[0]["error"]
                    logger.error(f"❌ Trigger order rejected: {error_msg}")
                    raise Exception(f"Trigger order rejected: {error_msg}")
                else:
                    logger.warning(f"⚠️  Unexpected trigger order response: {statuses}")
                    return {"status": "unknown", "response": order_result}
            else:
                error_msg = order_result.get("error", "Unknown error")
                logger.error(f"❌ Trigger order failed: {error_msg}")
                raise Exception(f"Trigger order failed: {error_msg}")

        except Exception as e:
            logger.error(f"❌ Failed to place trigger order: {e}")
            raise

    async def cancel_order(self, order_id: str, asset: str) -> Dict[str, Any]:
        """Cancel an existing order."""
        endpoint = "/exchange/cancel"
        data = {"coin": asset, "oid": order_id}

        response = await self._request("POST", endpoint, data, authenticated=True)
        logger.info(f"Order cancelled: {order_id}")
        return response

    async def close_position(self, asset: str) -> Dict[str, Any]:
        """Close all positions for an asset."""
        portfolio = await self.get_account_state()

        for position in portfolio.positions:
            if position.asset == asset:
                # Place opposite order to close
                side = "SELL" if position.side == "LONG" else "BUY"
                await self.place_order(
                    asset=asset,
                    side=side,
                    size=position.size,
                    order_type="MARKET",
                    reduce_only=True
                )
                logger.info(f"Closed {position.side} position for {asset}")

        return {"status": "closed", "asset": asset}

    def _calculate_volatility(self, candles: List[Dict[str, Any]]) -> float:
        """Calculate realized volatility from candle data."""
        if len(candles) < 2:
            return 0.0

        returns = []
        for i in range(1, len(candles)):
            prev_close = float(candles[i-1]['close'])
            curr_close = float(candles[i]['close'])
            if prev_close > 0:
                ret = (curr_close - prev_close) / prev_close
                returns.append(ret)

        if not returns:
            return 0.0

        # Calculate standard deviation of returns
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = (variance ** 0.5) * 100  # Convert to percentage

        return volatility

    async def get_trade_history(self, asset: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trade history for an asset."""
        endpoint = "/info"
        data = {"type": "userFills", "user": self.wallet_address}
        response = await self._request("POST", endpoint, data)

        # Filter trades for the specific asset
        trades = []
        for trade in response:
            if trade.get('coin') == asset:
                trades.append(trade)
                if len(trades) >= limit:
                    break

        return trades

    async def health_check(self) -> bool:
        """Check if API is accessible."""
        try:
            await self.get_ticker("BTC")
            logger.info("Hyperliquid API health check passed")
            return True
        except Exception as e:
            logger.error(f"Hyperliquid API health check failed: {e}")
            return False
