# YouTube Livestream Integration - Quick Start

## 🎯 XRPGEN Livestream ist jetzt integriert!

Der Bot kann jetzt **visuelle Trading-Signale** vom XRPGEN YouTube Livestream analysieren und in seine Entscheidungen einbeziehen.

---

## ⚡ Schnellstart (3 Schritte)

### Schritt 1: OpenAI API Key erstellen

1. Gehe zu: https://platform.openai.com/api-keys
2. Erstelle einen neuen API Key
3. **Wichtig**: Du brauchst Guthaben (~$5-10 für Testzweck)
   - GPT-4 Vision kostet ~$0.01 pro Screenshot
   - Bei 60s Interval = ~$15-20/Tag

### Schritt 2: API Key in .env eintragen

Öffne `.env` und setze:

```bash
# YouTube Livestream aktivieren
YOUTUBE_LIVESTREAM_ENABLED=true

# OpenAI API Key eintragen
OPENAI_API_KEY=sk-proj-...  # Dein Key hier einfügen
```

### Schritt 3: Bot neu starten

```bash
# Stoppe den aktuellen Bot (Ctrl+C)
# Dann neu starten:
./venv/bin/python run_bot.py
```

Das war's! Der Bot läuft jetzt und analysiert alle 60 Sekunden den XRPGEN Livestream.

---

## 📊 Was passiert im Hintergrund?

```
XRPGEN Stream → Screenshot (alle 60s) → GPT-4 Vision → Signal Extraktion → DeepSeek Reasoning
```

### Der Bot erkennt automatisch:
- ✅ **Trading Signale** für BTC, ETH, DOGE, SOL, BNB
- ✅ **Entry Prices** aus Text-Overlays oder Charts
- ✅ **Stop Loss** und **Take Profit** Levels
- ✅ **Buy/Sell Zones** aus Chart-Markierungen
- ❌ **XRP Signale** werden ignoriert (nicht auf Hyperliquid)

### Signale werden gespeichert in:
```
data/livestream_signals.json
```

### Screenshots werden gespeichert in:
```
data/livestream_captures/frame_YYYYMMDD_HHMMSS.jpg
```

---

## 🎛️ Erweiterte Einstellungen

### Capture Interval anpassen:

In `.env`:
```bash
YOUTUBE_CAPTURE_INTERVAL=60  # Sekunden zwischen Screenshots
```

**Empfehlungen:**
- **30s** = Real-time, hohe Kosten (~$30-60/Tag)
- **60s** = Guter Kompromiss (~$15-30/Tag) ⭐ **Empfohlen**
- **120s** = Günstig (~$8-15/Tag)
- **300s** = Sehr günstig (~$3-6/Tag)

### Signal Weight anpassen:

Der Bot kombiniert Livestream-Signale mit eigener Analyse.

Aktuell: **30% Livestream + 70% Eigene Analyse**

Um das anzupassen, bearbeite `src/config.py`:
```python
signal_weight: float = 0.3  # 0.3 = 30%, 0.5 = 50%, etc.
```

---

## 🔍 Monitoring

### Livestream-Signale ansehen:

```bash
# Aktuelle Signale
cat data/livestream_signals.json

# Live-Monitoring
watch -n 5 'cat data/livestream_signals.json | tail -20'
```

### Screenshots ansehen:

```bash
# Neueste Screenshots
ls -lht data/livestream_captures/ | head -10

# Letzten Screenshot öffnen
open data/livestream_captures/$(ls -t data/livestream_captures/ | head -1)
```

### Logs überprüfen:

```bash
# Nach Livestream-Aktivität suchen
tail -f logs/trading_bot.log | grep -i "livestream\|vision\|signal"
```

---

## ⚠️ Troubleshooting

### "No signals detected"

**Problem**: Vision AI findet keine Signale im Stream

**Lösungen:**
1. Check ob Stream gerade aktiv ist: https://www.youtube.com/@XRPGEN/streams
2. Schaue dir letzten Screenshot an um zu sehen was GPT-4V sieht
3. Stream zeigt evtl. gerade nur XRP (wird ignoriert)

```bash
# Letzten Screenshot ansehen:
open data/livestream_captures/$(ls -t data/livestream_captures/ | head -1)
```

### "OpenAI API error 401"

**Problem**: API Key ungültig

**Lösung:**
```bash
# Check Key in .env
grep OPENAI_API_KEY .env

# Test Key:
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $(grep OPENAI_API_KEY .env | cut -d '=' -f2)"
```

### "OpenAI API error 429 - Rate Limit"

**Problem**: Zu viele Requests

**Lösung**: Erhöhe `YOUTUBE_CAPTURE_INTERVAL` in .env (z.B. auf 120 statt 60)

### "Insufficient Balance"

**Problem**: Kein Guthaben mehr auf OpenAI Account

**Lösung**:
1. Gehe zu https://platform.openai.com/settings/organization/billing
2. Füge Guthaben hinzu ($10 reicht für ~1000 Screenshots)

---

## 💰 Kosten-Rechnung

### GPT-4 Vision Preise:
- **$0.01 pro Bild** (1280x720 Screenshot)

### Bei verschiedenen Intervals:
- **60s Interval**: 1440 Bilder/Tag = ~$14.40/Tag
- **120s Interval**: 720 Bilder/Tag = ~$7.20/Tag
- **300s Interval**: 288 Bilder/Tag = ~$2.88/Tag

### Nur während Trading-Zeiten (8h/Tag):
- **60s, 8h**: 480 Bilder = ~$4.80/Tag
- **120s, 8h**: 240 Bilder = ~$2.40/Tag

**Tipp**: Aktiviere nur während wichtigen Trading-Sessions!

---

## 🎚️ Integration mit DeepSeek

Der Bot kombiniert Livestream-Signale mit seiner eigenen technischen Analyse:

### Wenn Livestream-Signal vorhanden:
1. GPT-4V extrahiert Signal (z.B. "BTC LONG @ 71500")
2. DeepSeek macht eigene Multi-Timeframe Analyse
3. Beide werden kombiniert:
   - **Agreement** (beide bullish) → Höhere Confidence
   - **Conflict** (einer bullish, einer bearish) → DeepSeek entscheidet
   - **Partial** (Livestream zeigt Signal, DeepSeek neutral) → Moderate Confidence

### Aktuelles Weight-System:
- **Livestream Signal**: 30% Einfluss
- **DeepSeek Analysis**: 70% Einfluss

Das bedeutet: DeepSeek hat immer das letzte Wort, aber Livestream-Signale fließen mit ein.

---

## 🧪 Testen ohne zu traden

Teste die Integration ohne echte Trades:

1. Setze in .env:
```bash
MIN_CONFIDENCE=0.95  # Sehr hoch → kein Trade wird ausgeführt
```

2. Beobachte Logs um zu sehen welche Signale erkannt werden:
```bash
tail -f logs/trading_bot.log
```

3. Check AI Thinking Logs:
```bash
ls -lht logs/ai_thinking/
cat logs/ai_thinking/[neueste_datei].md
```

---

## 🎯 Nächste Schritte

1. ✅ **Aktiviere Integration** mit OpenAI API Key
2. ✅ **Teste 1-2 Stunden** und beobachte Logs
3. ✅ **Review erkannte Signale** in `data/livestream_signals.json`
4. ✅ **Adjustiere Interval** falls nötig (Kosten vs. Latency)
5. ✅ **Experimentiere mit Signal Weight** (mehr/weniger Einfluss)

---

## 📞 Support

Falls Probleme auftreten:

1. Check Logs: `tail -f logs/trading_bot.log`
2. Check Screenshots: Sind sie lesbar?
3. Check OpenAI API: Hat Account Guthaben?
4. Check Stream: Ist XRPGEN gerade live?

**Fragen?** Schreib mir einfach!

---

## 🔐 Sicherheit

**Wichtig:**
- OpenAI API Key ist GEHEIM! (wie Wallet Private Key)
- Teile niemals deinen `.env` File
- OpenAI sieht die Screenshots (kein Privacy)
- Verwende nur auf Testnet zum Testen!

---

Viel Erfolg! 🚀
