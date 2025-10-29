# 🚀 BOT STARTEN - Schritt für Schritt

## ✅ Status: Dependencies installiert!

Jetzt fehlen nur noch die API Keys!

---

## 📝 Schritt 1: API Keys besorgen

### 1a) Hyperliquid Testnet API Key

1. Gehe zu: **https://app.hyperliquid-testnet.xyz/**
2. Erstelle einen Account (oder login)
3. Gehe zu **Settings** → **API Keys**
4. Klicke **"Create New API Key"**
5. **WICHTIG**: Speichere sowohl:
   - API Key
   - Secret Key

   ⚠️ Secret Key wird nur EINMAL angezeigt!

### 1b) DeepSeek API Key

1. Gehe zu: **https://platform.deepseek.com/**
2. Registriere dich / Login
3. Gehe zu **API Keys** im Dashboard
4. Erstelle einen neuen API Key
5. Kopiere den Key

---

## 📝 Schritt 2: .env Datei konfigurieren

Die `.env` Datei ist bereits erstellt. Du musst nur deine Keys eintragen:

```bash
# Öffne die .env Datei mit einem Editor deiner Wahl:
code .env       # Visual Studio Code
# oder
nano .env       # Terminal Editor
# oder
vim .env        # Vim
# oder
open -e .env    # Mac TextEdit
```

### Trage deine Keys ein:

```env
# Hyperliquid API (TESTNET!)
HYPERLIQUID_API_KEY=dein_hyperliquid_api_key_hier
HYPERLIQUID_SECRET=dein_hyperliquid_secret_hier
HYPERLIQUID_TESTNET=true  # ⚠️ WICHTIG: Erst auf true lassen!

# DeepSeek API
DEEPSEEK_API_KEY=dein_deepseek_api_key_hier
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Trading Configuration (Start KLEIN!)
# MULTI-ASSET MODE: Mehrere Assets gleichzeitig handeln
TRADING_ASSETS=BTC,ETH,SOL
# ODER Single-Asset: Nur Bitcoin
# TRADING_ASSETS=
# DEFAULT_ASSET=BTC

MAX_POSITION_SIZE=500      # Start mit $500 max pro Asset
RISK_PER_TRADE=0.01        # 1% Risk pro Trade
MAX_EXPOSURE=0.5           # Max 50% Exposure (über alle Assets)
TRADING_INTERVAL=300       # 5 Minuten

# Risk Management
STOP_LOSS_PERCENT=0.03     # 3% Stop Loss
TAKE_PROFIT_PERCENT=0.06   # 6% Take Profit
MIN_CONFIDENCE=0.65        # Minimum 65% AI Confidence
MIN_LIQUIDITY=1000000      # Min $1M 24h Volume

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trading_bot.log
```

**Speichern nicht vergessen!**

---

## 📝 Schritt 3: Bot starten (TESTNET)

### Terminal öffnen und:

```bash
# 1. In das Projektverzeichnis wechseln
cd /Users/benjaminjeschke/Documents/apps/hyper-bot/hyper-bot

# 2. Virtual Environment aktivieren
source venv/bin/activate

# 3. Bot starten
python run_bot.py
```

### Was du sehen solltest:

```
==========================================
HYPERLIQUID TRADING BOT STARTING
==========================================

Initial Portfolio: $10,000.00
Available Balance: $10,000.00
Trading loop interval: 300s
Bot is running. Press Ctrl+C to stop.
==========================================

--- Trading Loop: 2025-10-29 12:00:00 ---
Fetching market data for BTC...
Calculating technical indicators...
Requesting AI trading decision...
AI Decision: HOLD
Setup Quality: B | Confidence: 0.58
Confluence Score: 3/10
Market Regime: RANGING
Reasoning: Insufficient confluence...
Decision validation failed: Confluence score too low
--- Trading Loop Complete ---
```

---

## 🎯 Was der Bot macht

### Alle 5 Minuten:

1. ✅ **Holt Marktdaten** von Hyperliquid
2. ✅ **Berechnet 15+ technische Indikatoren**
3. ✅ **Fragt DeepSeek** nach Trading-Entscheidung
4. ✅ **Validiert Entscheidung** (Confluence, Confidence)
5. ✅ **Prüft Risiko-Regeln**
6. ✅ **Führt Trade aus** (nur wenn alles passt)
7. ✅ **Überwacht Positionen** (Stop-Loss, Take-Profit)

### Wichtig:

- **HOLD ist NORMAL!** Der Bot ist sehr selektiv
- **Nur 1-3 A+ Setups pro Tag**
- **Meiste Zeit: HOLD** (wartet auf perfekte Gelegenheit)

---

## 🛑 Bot stoppen

Drücke **Ctrl+C** im Terminal

Der Bot wird alle offenen Positionen beibehalten (nicht automatisch schließen).

---

## 📊 Logs checken

Alle Aktivitäten werden geloggt:

```bash
# Terminal Logs (Echtzeit)
# Siehst du während Bot läuft

# File Logs (Persistent)
tail -f logs/trading_bot.log

# oder mit less
less logs/trading_bot.log
```

---

## ⚠️ WICHTIGE SICHERHEITS-CHECKS

Bevor du startest, checke:

- [ ] `HYPERLIQUID_TESTNET=true` in .env
- [ ] Alle API Keys eingetragen
- [ ] `MAX_POSITION_SIZE=500` (klein anfangen!)
- [ ] `RISK_PER_TRADE=0.01` (1% max)
- [ ] Du verstehst was der Bot macht
- [ ] Du kannst die Logs lesen
- [ ] Du weißt wie man stoppt (Ctrl+C)

---

## 📈 Was erwarten?

### Erste Stunden:

- Bot wird **viel HOLD entscheiden** ✅ (Normal!)
- Vielleicht **0-2 Trades pro Tag** ✅ (Normal!)
- Logs zeigen **detaillierte Reasoning** ✅
- Confluence Scores meist **3-6** ✅

### Warum so wenig Trades?

Der Bot wartet auf **A+ Setups**:
- ✅ Minimum 4 Confluence Faktoren
- ✅ Confidence > 65%
- ✅ Gutes Risk/Reward (>2:1)
- ✅ Passende Markt-Bedingungen

**Das ist gut so!** Quality over Quantity.

---

## 🔧 Troubleshooting

### "Configuration validation failed"

```bash
# Checke .env Datei
cat .env

# Stelle sicher alle Keys sind gesetzt
# Keine leeren Werte
```

### "Hyperliquid API health check failed"

- Check Internet
- Check API Keys korrekt
- Check Hyperliquid Testnet erreichbar

### "Failed to get AI decision"

- Check DeepSeek API Key
- Check DeepSeek API Quota
- Check Internet

### Bot macht keine Trades

**Das ist NORMAL!** Check Logs:

```bash
tail -f logs/trading_bot.log | grep "Decision"
```

Meistens siehst du:
- "Decision validation failed: Confluence score too low"
- "Risk check failed: ..."
- "Decision is HOLD"

→ **Das ist das Risk Management in Action!**

---

## 📚 Weitere Infos

- **QUICKSTART.md** - Ausführliche Anleitung
- **ARCHITECTURE.md** - Wie der Bot funktioniert
- **prompt.md** - Die AI Strategie
- **PROJECT_SUMMARY.md** - Vollständige Übersicht

---

## 🚀 Los geht's!

```bash
cd /Users/benjaminjeschke/Documents/apps/hyper-bot/hyper-bot
source venv/bin/activate
python run_bot.py
```

**Viel Erfolg! 🎉📈**

---

## 💡 Tipps

1. **Lass den Bot 24h laufen** - Beobachte was er macht
2. **Check die Logs** - Verstehe seine Entscheidungen
3. **Sei geduldig** - A+ Setups sind selten
4. **Hab Vertrauen** - Der Bot hat strenges Risk Management
5. **Start klein** - Erst testen, dann erhöhen

---

## ⏭️ Nach erfolgreichen Tests auf Testnet

Wenn nach 24-48h alles gut läuft:

1. Setze `HYPERLIQUID_TESTNET=false` in .env
2. **REDUZE MAX_POSITION_SIZE** auf $100-200
3. Starte Bot auf Mainnet
4. **Überwache eng** erste Woche
5. Erhöhe graduell wenn performt

**Aber: Erst gründlich Testnet testen!**

---

**Fragen? Check die Logs! Die Antworten stehen dort. 📖**
