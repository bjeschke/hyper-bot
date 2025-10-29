"""YouTube Livestream Signal Monitor - Visual Signal Extraction."""

import asyncio
import subprocess
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger
import aiohttp
from PIL import Image
import io


class YouTubeLiveMonitor:
    """
    Monitor YouTube livestream for visual trading signals.

    Uses:
    1. streamlink/yt-dlp to capture livestream frames
    2. Vision AI (GPT-4V, Claude Vision, or Gemini) to analyze charts/signals
    3. DeepSeek for final trading decision integration
    """

    def __init__(
        self,
        livestream_url: str,
        vision_provider: str = "openai",  # "openai", "anthropic", "gemini"
        api_key: str = None,
        capture_interval: int = 30,  # seconds between captures
    ):
        self.livestream_url = livestream_url
        self.vision_provider = vision_provider
        self.api_key = api_key
        self.capture_interval = capture_interval
        self.screenshot_dir = Path("data/livestream_captures")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.running = False

        logger.info(f"Initialized YouTube Live Monitor for: {livestream_url}")
        logger.info(f"Using {vision_provider} for visual analysis")
        logger.info(f"Capture interval: {capture_interval}s")

    async def capture_frame(self) -> Optional[Path]:
        """
        Capture a single frame from the YouTube livestream using yt-dlp.

        Simplified method - uses yt-dlp to get thumbnail from live stream.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.screenshot_dir / f"frame_{timestamp}.jpg"

        try:
            # Use yt-dlp to capture frame
            yt_dlp_cmd = [
                "yt-dlp",
                "--no-download",
                "--write-thumbnail",
                "--skip-download",
                "--convert-thumbnails", "jpg",
                "-o", str(output_path.with_suffix("")),
                self.livestream_url
            ]

            result = subprocess.run(
                yt_dlp_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Check for created files
            for ext in ['.jpg', '.png', '.webp']:
                possible_path = output_path.with_suffix(ext)
                if possible_path.exists():
                    # Convert to jpg if needed
                    if ext != '.jpg':
                        try:
                            from PIL import Image
                            img = Image.open(possible_path)
                            img.convert('RGB').save(output_path, 'JPEG')
                            possible_path.unlink()  # Remove original
                            logger.debug(f"Converted {ext} to JPG: {output_path}")
                            return output_path
                        except Exception as e:
                            logger.error(f"Failed to convert image: {e}")
                            return possible_path
                    else:
                        logger.debug(f"Captured frame: {output_path}")
                        return possible_path

            logger.warning(f"No thumbnail found. yt-dlp output: {result.stderr[:200]}")

        except subprocess.TimeoutExpired:
            logger.error("Frame capture timed out (30s)")
        except Exception as e:
            logger.error(f"Failed to capture frame: {e}")

        return None

    async def analyze_frame_with_vision(self, image_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze frame using vision AI to extract trading signals.

        Returns structured data about detected signals.
        """
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()

            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Choose provider
            if self.vision_provider == "openai":
                return await self._analyze_with_openai(image_base64)
            elif self.vision_provider == "anthropic":
                return await self._analyze_with_claude(image_base64)
            elif self.vision_provider == "gemini":
                return await self._analyze_with_gemini(image_base64)
            else:
                logger.error(f"Unknown vision provider: {self.vision_provider}")
                return None

        except Exception as e:
            logger.exception(f"Vision analysis failed: {e}")
            return None

    async def _analyze_with_openai(self, image_base64: str) -> Optional[Dict[str, Any]]:
        """Analyze image with GPT-4 Vision."""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            prompt = """Analyze this XRPGEN trading livestream screenshot and extract signals.

**IMPORTANT**: This bot trades on Hyperliquid which does NOT support XRP.
Only extract signals for: BTC, ETH, DOGE, SOL, BNB (ignore XRP signals!)

Extract:

1. **Trading Signals** for BTC, ETH, DOGE, SOL, or BNB:
   - Asset/Symbol (MUST be one of: BTC, ETH, DOGE, SOL, BNB)
   - Signal Type (BUY/SELL/CLOSE/LONG/SHORT)
   - Entry Price (look for "Entry:", "Buy at:", price levels)
   - Stop Loss (look for "SL:", "Stop Loss:", red zones)
   - Take Profit targets (look for "TP:", "Target:", green zones)
   - Confidence (if mentioned: High/Medium/Low → 0.8/0.6/0.4)

2. **Visual Chart Elements**:
   - Current Price visible on chart
   - Trend arrows or lines (Bullish/Bearish)
   - Support/Resistance levels drawn
   - Buy/Sell zones marked

3. **Text Overlays** (screen text, captions, annotations):
   - Trading recommendations
   - Price targets
   - Alerts or signals

**Return Format** (JSON):
{
  "signals": [
    {
      "asset": "BTC",
      "action": "BUY",
      "entry_price": 71500,
      "stop_loss": 70800,
      "take_profit": [72500, 73200, 74000],
      "confidence": 0.7,
      "reasoning": "Bullish breakout with strong support"
    }
  ],
  "analysis": "Overall market sentiment and visible trends"
}

If no signals for tradeable assets (BTC/ETH/DOGE/SOL/BNB), return: {"signals": [], "analysis": "No tradeable signals detected"}"""

            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }

            try:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']

                        # Try to parse as JSON
                        import json
                        try:
                            return json.loads(content)
                        except:
                            # If not JSON, return as text analysis
                            return {"raw_analysis": content}
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI Vision API error {response.status}: {error_text}")
                        return None

            except Exception as e:
                logger.error(f"OpenAI API request failed: {e}")
                return None

    async def _analyze_with_claude(self, image_base64: str) -> Optional[Dict[str, Any]]:
        """Analyze image with Claude Vision (Anthropic)."""
        # Similar implementation to OpenAI but for Claude API
        # https://docs.anthropic.com/claude/docs/vision
        logger.warning("Claude Vision analysis not yet implemented")
        return None

    async def _analyze_with_gemini(self, image_base64: str) -> Optional[Dict[str, Any]]:
        """Analyze image with Gemini Vision (Google)."""
        # Similar implementation for Google Gemini
        logger.warning("Gemini Vision analysis not yet implemented")
        return None

    async def extract_signals(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract actionable trading signals from vision analysis.

        Returns list of signals in standardized format for DeepSeek.
        """
        signals = []

        if not analysis:
            return signals

        # Parse signals from vision analysis
        if "signals" in analysis:
            for signal in analysis.get("signals", []):
                signals.append({
                    "source": "youtube_livestream",
                    "timestamp": datetime.now().isoformat(),
                    "asset": signal.get("asset"),
                    "action": signal.get("action"),  # BUY/SELL/CLOSE
                    "entry_price": signal.get("entry_price"),
                    "stop_loss": signal.get("stop_loss"),
                    "take_profit": signal.get("take_profit"),
                    "confidence": signal.get("confidence", 0.5),
                    "reasoning": signal.get("reasoning", ""),
                    "chart_analysis": analysis.get("analysis", "")
                })

        return signals

    async def monitor_loop(self):
        """Main monitoring loop - continuously captures and analyzes."""
        self.running = True

        logger.info("Starting YouTube livestream monitoring...")

        while self.running:
            try:
                # Capture frame
                logger.info("Capturing livestream frame...")
                frame_path = await self.capture_frame()

                if frame_path:
                    # Analyze with vision AI
                    logger.info("Analyzing frame with vision AI...")
                    analysis = await self.analyze_frame_with_vision(frame_path)

                    if analysis:
                        # Extract signals
                        signals = await self.extract_signals(analysis)

                        if signals:
                            logger.success(f"Extracted {len(signals)} signal(s) from livestream")

                            # Save to signals file for bot to pick up
                            await self._save_signals(signals)
                        else:
                            logger.info("No trading signals detected in current frame")

                    # Optional: Clean up old screenshots (keep last 100)
                    await self._cleanup_old_captures(keep_last=100)

                # Wait for next capture
                await asyncio.sleep(self.capture_interval)

            except Exception as e:
                logger.exception(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry

    async def _save_signals(self, signals: List[Dict[str, Any]]):
        """Save extracted signals to file for main bot to consume."""
        signals_file = Path("data/livestream_signals.json")

        import json

        # Load existing
        existing = []
        if signals_file.exists():
            with open(signals_file, 'r') as f:
                existing = json.load(f)

        # Add new signals
        existing.extend(signals)

        # Keep only last 50 signals
        existing = existing[-50:]

        # Save
        with open(signals_file, 'w') as f:
            json.dump(existing, indent=2, fp=f)

        logger.info(f"Saved signals to {signals_file}")

    async def _cleanup_old_captures(self, keep_last: int = 100):
        """Remove old screenshot files to save disk space."""
        files = sorted(self.screenshot_dir.glob("frame_*.jpg"))

        if len(files) > keep_last:
            for old_file in files[:-keep_last]:
                old_file.unlink()

    def stop(self):
        """Stop monitoring."""
        logger.info("Stopping livestream monitor...")
        self.running = False


async def main():
    """Test the livestream monitor."""
    # Example usage
    monitor = YouTubeLiveMonitor(
        livestream_url="https://www.youtube.com/watch?v=LIVESTREAM_ID",
        vision_provider="openai",
        api_key="YOUR_OPENAI_API_KEY",
        capture_interval=30  # Every 30 seconds
    )

    await monitor.monitor_loop()


if __name__ == "__main__":
    asyncio.run(main())
