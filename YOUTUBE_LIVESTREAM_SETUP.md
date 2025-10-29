# YouTube Livestream Signal Monitor - Setup Guide

## 📺 Übersicht

Dieses Modul überwacht YouTube-Livestreams mit **visuellen Trading-Signalen** und extrahiert diese automatisch für deinen Trading Bot.

### Funktionsweise:

1. **Frame Capture**: Screenshot vom Livestream alle X Sekunden
2. **Vision AI Analysis**: GPT-4 Vision / Claude / Gemini analysiert das Bild
3. **Signal Extraction**: Trading-Signale werden strukturiert extrahiert
4. **DeepSeek Integration**: Signale fließen in Bot-Entscheidungen ein

---

## 🛠️ Installation

### 1. Basis-Dependencies

```bash
# Aktiviere venv
source venv/bin/activate

# Installation der zusätzlichen Packages
pip install Pillow streamlink yt-dlp
```

### 2. FFmpeg installieren (für Frame Capture)

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
- Download von: https://ffmpeg.org/download.html
- Zu PATH hinzufügen

### 3. Vision AI Provider Setup

Du brauchst einen Vision AI Provider (mindestens einen):

#### Option A: OpenAI GPT-4 Vision (Empfohlen) 🌟

**Vorteile:**
- Beste Qualität für Chart-Analyse
- Schnelle Response-Zeit (~2-3s)
- Gute JSON-Strukturierung

**Setup:**
```bash
# OpenAI API Key erstellen: https://platform.openai.com/api-keys
# Zur .env hinzufügen:
echo "OPENAI_API_KEY=sk-..." >> .env
```

**Kosten:** ~$0.01-0.02 pro Screenshot (1280x720)

#### Option B: Claude Vision (Anthropic)

**Vorteile:**
- Sehr gute Reasoning
- Lange Context Window
- Detaillierte Analysen

**Setup:**
```bash
# Claude API Key: https://console.anthropic.com/
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

**Kosten:** ~$0.008 pro Screenshot

#### Option C: Gemini Vision (Google)

**Vorteile:**
- Günstigste Option
- Gute Performance
- Große Free Tier

**Setup:**
```bash
# Google AI Studio: https://makersuite.google.com/app/apikey
echo "GOOGLE_API_KEY=..." >> .env
```

**Kosten:** Free bis 60 requests/min

---

## ⚙️ Konfiguration

### .env Einstellungen:

```bash
# Vision AI Provider
VISION_PROVIDER=openai  # oder: anthropic, gemini
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...  # Falls Claude
# GOOGLE_API_KEY=...  # Falls Gemini

# Livestream Monitoring
YOUTUBE_LIVESTREAM_URL=https://www.youtube.com/watch?v=LIVESTREAM_ID
LIVESTREAM_CAPTURE_INTERVAL=30  # Sekunden zwischen Screenshots
LIVESTREAM_ENABLED=true
```

---

## 🚀 Verwendung

### Standalone Monitoring (Test):

```bash
# Test-Script erstellen
python -c "
from src.sources.youtube_live_monitor import YouTubeLiveMonitor
import asyncio
import os

async def test():
    monitor = YouTubeLiveMonitor(
        livestream_url='https://www.youtube.com/watch?v=YOUR_STREAM_ID',
        vision_provider='openai',
        api_key=os.getenv('OPENAI_API_KEY'),
        capture_interval=30
    )

    # Single capture test
    frame = await monitor.capture_frame()
    if frame:
        print(f'✅ Frame captured: {frame}')

        # Analyze
        analysis = await monitor.analyze_frame_with_vision(frame)
        print(f'📊 Analysis: {analysis}')
    else:
        print('❌ Frame capture failed')

asyncio.run(test())
"
```

### Integration in Trading Bot:

Der Monitor läuft parallel zum Bot und speichert Signale in `data/livestream_signals.json`.

**Modifiziere `src/main.py`:**

```python
# Am Anfang importieren
from src.sources.youtube_live_monitor import YouTubeLiveMonitor

class TradingBot:
    def __init__(self):
        # ... existing code ...

        # Livestream Monitor starten (falls aktiviert)
        if config.livestream.enabled:
            self.livestream_monitor = YouTubeLiveMonitor(
                livestream_url=config.livestream.url,
                vision_provider=config.vision.provider,
                api_key=config.vision.api_key,
                capture_interval=config.livestream.capture_interval
            )

    async def start(self):
        # ... existing code ...

        # Start livestream monitor in background
        if hasattr(self, 'livestream_monitor'):
            asyncio.create_task(self.livestream_monitor.monitor_loop())

    async def trading_loop(self):
        # ... existing code ...

        # Load livestream signals
        livestream_signals = await self._load_livestream_signals()

        # Merge with technical analysis
        for signal in livestream_signals:
            if signal['asset'] in self.assets:
                # Consider livestream signal in decision
                pass
```

---

## 📊 Signal Format

Extrahierte Signale werden in diesem Format gespeichert:

```json
{
  "source": "youtube_livestream",
  "timestamp": "2025-10-29T16:45:00",
  "asset": "BTC",
  "action": "BUY",
  "entry_price": 111500,
  "stop_loss": 110800,
  "take_profit": [112500, 113200, 114000],
  "confidence": 0.75,
  "reasoning": "Strong support at 111400, RSI oversold on 4h...",
  "chart_analysis": "Bullish divergence visible, MACD crossover..."
}
```

---

## 🎯 Vision AI Prompt Engineering

Der Monitor fragt die Vision AI:

1. **Trading Signals**:
   - Asset/Symbol erkannt?
   - BUY/SELL/CLOSE Signal?
   - Entry, SL, TP sichtbar?

2. **Chart Analysis**:
   - Aktueller Preis
   - Trend-Richtung
   - Support/Resistance Levels
   - Sichtbare Indikatoren

3. **Text Overlays**:
   - Trading-Empfehlungen
   - Alerts/Warnings
   - Target-Levels

---

## ⚡ Performance & Kosten

### Capture Interval Empfehlungen:

- **30 Sekunden**: Real-time Signale, hohe Kosten (~$30-60/Tag)
- **60 Sekunden**: Guter Kompromiss (~$15-30/Tag)
- **120 Sekunden**: Günstig, für langsame Signale (~$8-15/Tag)
- **300 Sekunden (5 Min)**: Sehr günstig, nur für Major-Updates (~$3-6/Tag)

### Kosten-Optimierung:

1. **Frame Quality reduzieren**: 720p statt 1080p
2. **Nur bei Änderung analysieren**: Screenshot-Vergleich
3. **OCR für Text-Overlays**: Günstiger als Vision AI
4. **Scheduled Monitoring**: Nur während aktiven Trading-Zeiten

---

## 🔍 Troubleshooting

### "Frame capture failed"

**Problem:** streamlink oder yt-dlp kann Stream nicht abrufen

**Lösung:**
```bash
# Test streamlink
streamlink --stream-url "YOUR_YOUTUBE_URL" best

# Falls Fehler, update:
pip install --upgrade streamlink yt-dlp

# Test ob FFmpeg funktioniert:
ffmpeg -version
```

### "Vision API error 401"

**Problem:** API Key ungültig oder fehlt

**Lösung:**
```bash
# Check .env
cat .env | grep API_KEY

# Test API Key:
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### "No signals detected"

**Mögliche Gründe:**
1. Stream zeigt gerade keine Signale
2. Vision AI kann Signale nicht erkennen (zu klein, schlecht lesbar)
3. Prompt muss angepasst werden für diesen speziellen Stream

**Debug:**
```bash
# Check captured frames:
ls -lh data/livestream_captures/

# Manually inspect:
open data/livestream_captures/frame_latest.jpg

# Check Vision AI response:
tail -f logs/trading_bot.log | grep "Vision"
```

---

## 🎨 Channel-spezifische Anpassungen

Jeder Trading-Signal-Channel ist anders. Du musst evtl. den **Vision Prompt** anpassen:

### Beispiel: Channel mit Text-Overlays

```python
prompt = """
This is a crypto trading livestream with text overlays.

Extract EXACTLY:
- Top-left corner: Current Asset (BTC, ETH, etc.)
- Center screen: BUY/SELL indicator (green/red)
- Bottom: Entry Price, Stop Loss, Take Profit

Return as JSON:
{"asset": "BTC", "action": "BUY", "entry": 111500, "sl": 110800, "tp": [112500]}
"""
```

### Beispiel: Channel mit Chart-Markierungen

```python
prompt = """
Analyze the trading chart visible on screen.

Look for:
- Drawn lines/arrows indicating entry points
- Support/Resistance levels marked
- Green/Red zones for TP/SL
- Text annotations with price levels

Extract and structure the trading setup.
"""
```

---

## 🚨 Wichtige Hinweise

1. **Latency**:
   - Screenshot: ~1-3s
   - Vision Analysis: ~2-5s
   - **Total Delay: ~3-8s** gegenüber Live-Stream

2. **Accuracy**:
   - Vision AI ist nicht 100% perfekt
   - IMMER mit eigenem Analysis kombinieren
   - Als **zusätzlicher Faktor**, nicht als alleinige Entscheidung

3. **Legal**:
   - Prüfe Terms of Service des YouTube-Kanals
   - Automatisches Scraping kann gegen TOS verstoßen
   - Am besten: Offizielle API/Discord/Telegram nutzen

4. **Rate Limits**:
   - YouTube: Max 1 request/s für Streams
   - Vision APIs: Je nach Provider (GPT-4V: 100/min, Gemini: 60/min)

---

## 📝 Nächste Schritte

1. ✅ **Teste Frame Capture**:
   ```bash
   streamlink YOUR_YOUTUBE_URL best -o test_frame.mp4 --hls-duration 00:00:01
   ```

2. ✅ **Teste Vision API** mit einem Screenshot

3. ✅ **Monitor Loop** für 5-10 Minuten laufen lassen

4. ✅ **Signale reviewen** in `data/livestream_signals.json`

5. ✅ **Integration** in Trading Bot aktivieren

---

## 📞 Support

Wenn du Hilfe brauchst bei:
- Einrichtung für einen spezifischen Channel
- Prompt-Optimierung für bessere Signal-Extraktion
- Integration in deinen Bot

→ Sag mir einfach Bescheid! Ich kann:
- Den Vision Prompt anpassen
- OCR statt Vision AI verwenden (günstiger für Text)
- Alternative Lösungen vorschlagen

**Welcher Livestream-Channel ist es?** Link oder Channel-Name würde helfen um die beste Lösung zu finden! 🎯
