"""Technical indicators calculation."""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
from loguru import logger

from src.utils.models import MACD, BollingerBands, TechnicalIndicators


class TechnicalAnalysis:
    """
    Technical analysis engine for calculating indicators.

    Implements all indicators used in the trading strategy:
    - RSI, MACD, EMAs
    - ADX, Supertrend
    - Bollinger Bands, ATR
    - Volume indicators (VWAP, CVD, OBV)
    """

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """
        Calculate RSI (Relative Strength Index).

        Args:
            prices: List of closing prices
            period: RSI period (default 14)

        Returns:
            RSI value (0-100)
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral if not enough data

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        # Calculate remaining periods using Wilder's smoothing
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def calculate_macd(
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> MACD:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            prices: List of closing prices
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period

        Returns:
            MACD object with value, signal, and histogram
        """
        if len(prices) < slow_period + signal_period:
            return MACD(value=0.0, signal=0.0, histogram=0.0)

        df = pd.DataFrame(prices, columns=['price'])

        # Calculate EMAs
        ema_fast = df['price'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df['price'].ewm(span=slow_period, adjust=False).mean()

        # MACD line
        macd_line = ema_fast - ema_slow

        # Signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Histogram
        histogram = macd_line - signal_line

        return MACD(
            value=float(macd_line.iloc[-1]),
            signal=float(signal_line.iloc[-1]),
            histogram=float(histogram.iloc[-1])
        )

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """
        Calculate EMA (Exponential Moving Average).

        Args:
            prices: List of closing prices
            period: EMA period

        Returns:
            EMA value
        """
        if len(prices) < period:
            return float(np.mean(prices)) if prices else 0.0

        df = pd.DataFrame(prices, columns=['price'])
        ema = df['price'].ewm(span=period, adjust=False).mean()
        return float(ema.iloc[-1])

    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> float:
        """Calculate SMA (Simple Moving Average)."""
        if len(prices) < period:
            return float(np.mean(prices)) if prices else 0.0

        return float(np.mean(prices[-period:]))

    @staticmethod
    def calculate_bollinger_bands(
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0
    ) -> BollingerBands:
        """
        Calculate Bollinger Bands.

        Args:
            prices: List of closing prices
            period: Moving average period
            std_dev: Number of standard deviations

        Returns:
            BollingerBands object
        """
        if len(prices) < period:
            current_price = prices[-1] if prices else 0
            return BollingerBands(
                upper=current_price,
                middle=current_price,
                lower=current_price,
                percent_b=0.5,
                width=0.0
            )

        df = pd.DataFrame(prices, columns=['price'])

        # Middle band (SMA)
        middle = df['price'].rolling(window=period).mean()

        # Standard deviation
        std = df['price'].rolling(window=period).std()

        # Upper and lower bands
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        # %B (position within bands)
        current_price = prices[-1]
        upper_val = float(upper.iloc[-1])
        lower_val = float(lower.iloc[-1])
        middle_val = float(middle.iloc[-1])

        if upper_val != lower_val:
            percent_b = (current_price - lower_val) / (upper_val - lower_val)
        else:
            percent_b = 0.5

        # Bandwidth
        if middle_val != 0:
            width = ((upper_val - lower_val) / middle_val) * 100
        else:
            width = 0.0

        return BollingerBands(
            upper=upper_val,
            middle=middle_val,
            lower=lower_val,
            percent_b=percent_b,
            width=width
        )

    @staticmethod
    def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """
        Calculate ATR (Average True Range).

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices
            period: ATR period

        Returns:
            ATR value
        """
        if len(closes) < period + 1:
            return 0.0

        true_ranges = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            true_range = max(high_low, high_close, low_close)
            true_ranges.append(true_range)

        # Wilder's smoothing
        atr = np.mean(true_ranges[:period])
        for i in range(period, len(true_ranges)):
            atr = (atr * (period - 1) + true_ranges[i]) / period

        return atr

    @staticmethod
    def calculate_adx(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14
    ) -> Tuple[float, float, float]:
        """
        Calculate ADX (Average Directional Index).

        Returns:
            Tuple of (ADX, +DI, -DI)
        """
        if len(closes) < period + 1:
            return 0.0, 0.0, 0.0

        # Calculate +DM and -DM
        plus_dm = []
        minus_dm = []

        for i in range(1, len(highs)):
            high_diff = highs[i] - highs[i-1]
            low_diff = lows[i-1] - lows[i]

            if high_diff > low_diff and high_diff > 0:
                plus_dm.append(high_diff)
            else:
                plus_dm.append(0)

            if low_diff > high_diff and low_diff > 0:
                minus_dm.append(low_diff)
            else:
                minus_dm.append(0)

        # Calculate ATR
        atr = TechnicalAnalysis.calculate_atr(highs, lows, closes, period)

        if atr == 0:
            return 0.0, 0.0, 0.0

        # Smooth +DM and -DM
        plus_dm_smooth = np.mean(plus_dm[:period])
        minus_dm_smooth = np.mean(minus_dm[:period])

        for i in range(period, len(plus_dm)):
            plus_dm_smooth = (plus_dm_smooth * (period - 1) + plus_dm[i]) / period
            minus_dm_smooth = (minus_dm_smooth * (period - 1) + minus_dm[i]) / period

        # Calculate +DI and -DI
        plus_di = (plus_dm_smooth / atr) * 100
        minus_di = (minus_dm_smooth / atr) * 100

        # Calculate DX
        if plus_di + minus_di != 0:
            dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
        else:
            dx = 0

        # ADX is smoothed DX
        adx = dx  # Simplified; full implementation would smooth DX values

        return adx, plus_di, minus_di

    @staticmethod
    def calculate_vwap(prices: List[float], volumes: List[float]) -> float:
        """
        Calculate VWAP (Volume Weighted Average Price).

        Args:
            prices: List of typical prices (H+L+C)/3
            volumes: List of volumes

        Returns:
            VWAP value
        """
        if len(prices) != len(volumes) or len(prices) == 0:
            return 0.0

        cumulative_pv = sum(p * v for p, v in zip(prices, volumes))
        cumulative_volume = sum(volumes)

        if cumulative_volume == 0:
            return 0.0

        return cumulative_pv / cumulative_volume

    @staticmethod
    def calculate_obv(closes: List[float], volumes: List[float]) -> float:
        """
        Calculate OBV (On Balance Volume).

        Args:
            closes: List of closing prices
            volumes: List of volumes

        Returns:
            OBV value
        """
        if len(closes) < 2 or len(volumes) < 2:
            return 0.0

        obv = 0.0
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv += volumes[i]
            elif closes[i] < closes[i-1]:
                obv -= volumes[i]

        return obv

    @staticmethod
    def calculate_supertrend(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 10,
        multiplier: float = 3.0
    ) -> Tuple[float, str]:
        """
        Calculate Supertrend indicator.

        Returns:
            Tuple of (supertrend_value, signal)
            Signal is "bullish" or "bearish"
        """
        if len(closes) < period + 1:
            return 0.0, "neutral"

        atr = TechnicalAnalysis.calculate_atr(highs, lows, closes, period)

        # Calculate basic upper and lower bands
        hl_avg = [(h + l) / 2 for h, l in zip(highs, lows)]

        basic_upper = [avg + multiplier * atr for avg in hl_avg]
        basic_lower = [avg - multiplier * atr for avg in hl_avg]

        # Determine trend
        current_close = closes[-1]
        upper_band = basic_upper[-1]
        lower_band = basic_lower[-1]

        if current_close > upper_band:
            signal = "bullish"
            supertrend = lower_band
        else:
            signal = "bearish"
            supertrend = upper_band

        return supertrend, signal

    @staticmethod
    def detect_divergence(prices: List[float], indicator: List[float]) -> str:
        """
        Detect bullish or bearish divergence.

        Returns:
            "bullish", "bearish", or "none"
        """
        if len(prices) < 10 or len(indicator) < 10:
            return "none"

        # Find recent peaks and troughs
        price_peaks = []
        price_troughs = []
        indicator_peaks = []
        indicator_troughs = []

        for i in range(1, len(prices) - 1):
            if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                price_peaks.append((i, prices[i]))
                indicator_peaks.append((i, indicator[i]))
            elif prices[i] < prices[i-1] and prices[i] < prices[i+1]:
                price_troughs.append((i, prices[i]))
                indicator_troughs.append((i, indicator[i]))

        # Bullish divergence: price making lower lows, indicator making higher lows
        if len(price_troughs) >= 2 and len(indicator_troughs) >= 2:
            if price_troughs[-1][1] < price_troughs[-2][1] and indicator_troughs[-1][1] > indicator_troughs[-2][1]:
                return "bullish"

        # Bearish divergence: price making higher highs, indicator making lower highs
        if len(price_peaks) >= 2 and len(indicator_peaks) >= 2:
            if price_peaks[-1][1] > price_peaks[-2][1] and indicator_peaks[-1][1] < indicator_peaks[-2][1]:
                return "bearish"

        return "none"

    @staticmethod
    async def calculate_all_indicators(
        candles: List[dict],
        timeframe: str = "1h"
    ) -> TechnicalIndicators:
        """
        Calculate all technical indicators from candle data.

        Args:
            candles: List of candle dictionaries with OHLCV data
            timeframe: Timeframe of the candles

        Returns:
            TechnicalIndicators object with all calculated indicators
        """
        if not candles or len(candles) < 50:
            logger.debug(f"Not enough candle data for {timeframe}: {len(candles)}")
            return TechnicalIndicators()

        # Extract OHLCV data
        opens = [float(c['open']) for c in candles]
        highs = [float(c['high']) for c in candles]
        lows = [float(c['low']) for c in candles]
        closes = [float(c['close']) for c in candles]
        volumes = [float(c['volume']) for c in candles]

        indicators = TechnicalIndicators()

        # RSI
        try:
            if timeframe == "5m":
                indicators.rsi_5m = TechnicalAnalysis.calculate_rsi(closes)
            elif timeframe == "15m":
                indicators.rsi_15m = TechnicalAnalysis.calculate_rsi(closes)
            elif timeframe == "1h":
                indicators.rsi_1h = TechnicalAnalysis.calculate_rsi(closes)
            elif timeframe == "4h":
                indicators.rsi_4h = TechnicalAnalysis.calculate_rsi(closes)
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")

        # MACD
        try:
            macd = TechnicalAnalysis.calculate_macd(closes)
            if timeframe == "5m":
                indicators.macd_5m = macd
            elif timeframe == "1h":
                indicators.macd_1h = macd
            elif timeframe == "4h":
                indicators.macd_4h = macd
            else:
                indicators.macd = macd
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")

        # EMAs
        try:
            indicators.ema_9 = TechnicalAnalysis.calculate_ema(closes, 9)
            indicators.ema_20 = TechnicalAnalysis.calculate_ema(closes, 20)
            indicators.ema_50 = TechnicalAnalysis.calculate_ema(closes, 50)
            indicators.ema_200 = TechnicalAnalysis.calculate_ema(closes, 200)
        except Exception as e:
            logger.error(f"Error calculating EMAs: {e}")

        # ADX
        try:
            adx, plus_di, minus_di = TechnicalAnalysis.calculate_adx(highs, lows, closes)
            indicators.adx = adx
            indicators.plus_di = plus_di
            indicators.minus_di = minus_di
        except Exception as e:
            logger.error(f"Error calculating ADX: {e}")

        # Bollinger Bands
        try:
            indicators.bollinger_bands = TechnicalAnalysis.calculate_bollinger_bands(closes)
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")

        # ATR
        try:
            atr = TechnicalAnalysis.calculate_atr(highs, lows, closes)
            indicators.atr = atr
            if closes[-1] > 0:
                indicators.atr_percent = (atr / closes[-1]) * 100
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")

        # Supertrend
        try:
            supertrend, signal = TechnicalAnalysis.calculate_supertrend(highs, lows, closes)
            indicators.supertrend = supertrend
            indicators.supertrend_signal = signal
        except Exception as e:
            logger.error(f"Error calculating Supertrend: {e}")

        # VWAP
        try:
            typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
            indicators.vwap_daily = TechnicalAnalysis.calculate_vwap(typical_prices, volumes)
        except Exception as e:
            logger.error(f"Error calculating VWAP: {e}")

        # OBV
        try:
            obv = TechnicalAnalysis.calculate_obv(closes, volumes)
            indicators.obv = obv

            # Determine OBV trend
            if len(candles) >= 20:
                obv_20_ago = TechnicalAnalysis.calculate_obv(closes[:-20], volumes[:-20])
                if obv > obv_20_ago * 1.05:
                    indicators.obv_trend = "uptrend"
                elif obv < obv_20_ago * 0.95:
                    indicators.obv_trend = "downtrend"
                else:
                    indicators.obv_trend = "neutral"
        except Exception as e:
            logger.error(f"Error calculating OBV: {e}")

        # Volume ratio
        try:
            if len(volumes) >= 20:
                avg_volume = np.mean(volumes[-20:])
                current_volume = volumes[-1]
                if avg_volume > 0:
                    indicators.volume_ratio = current_volume / avg_volume
        except Exception as e:
            logger.error(f"Error calculating volume ratio: {e}")

        logger.debug(f"Calculated indicators for {timeframe}")
        return indicators
