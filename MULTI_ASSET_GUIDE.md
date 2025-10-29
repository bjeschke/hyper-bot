# Multi-Asset Trading Guide

## 🚀 Übersicht

Der Bot unterstützt jetzt **Multi-Asset Trading** - er kann mehrere Kryptowährungen gleichzeitig überwachen und handeln!

## 📊 Wie es funktioniert

### Single-Asset Mode (Original)
```env
# Nur ein Asset
TRADING_ASSETS=
DEFAULT_ASSET=BTC
```

Der Bot handelt **nur Bitcoin**.

### Multi-Asset Mode (NEU!)
```env
# Mehrere Assets
TRADING_ASSETS=BTC,ETH,SOL,ARB,AVAX
```

Der Bot handelt **alle diese Assets gleichzeitig**!

---

## ⚙️ Konfiguration

### 1. Assets auswählen

In der `.env` Datei, setze `TRADING_ASSETS`:

```env
# Beispiel 1: Top 5 Cryptos
TRADING_ASSETS=BTC,ETH,SOL,ARB,AVAX

# Beispiel 2: DeFi Coins
TRADING_ASSETS=UNI,AAVE,CRV,SUSHI,COMP

# Beispiel 3: Layer 1s
TRADING_ASSETS=BTC,ETH,SOL,AVAX,NEAR

# Beispiel 4: Conservative (nur Majors)
TRADING_ASSETS=BTC,ETH

# Beispiel 5: Aggressive (mehr Assets)
TRADING_ASSETS=BTC,ETH,SOL,ARB,AVAX,MATIC,LINK,UNI,AAVE,CRV
```

### 2. Verfügbare Assets auf Hyperliquid

Hyperliquid unterstützt viele Assets. Häufige:

**Major:**
- BTC, ETH, SOL, AVAX

**Layer 2 / Altcoins:**
- ARB (Arbitrum)
- OP (Optimism)
- MATIC (Polygon)
- LINK (Chainlink)

**DeFi:**
- UNI (Uniswap)
- AAVE
- CRV (Curve)
- SUSHI
- COMP (Compound)

**Others:**
- DOGE, SHIB, PEPE (Meme coins)
- APT, SUI (Newer L1s)

**Prüfe die aktuell verfügbaren Assets auf Hyperliquid:**
https://app.hyperliquid.xyz/

---

## 💡 Trading-Logik

### Wie der Bot mit mehreren Assets umgeht:

1. **Jeder Trading-Loop:**
   ```
   Loop Start → Hole Portfolio Status
   ├─ Analysiere BTC
   ├─ Analysiere ETH
   ├─ Analysiere SOL
   ├─ Analysiere ARB
   └─ Analysiere AVAX
   Loop Ende → Warte 5 Minuten
   ```

2. **Für jedes Asset:**
   - Hole Marktdaten
   - Berechne technische Indikatoren
   - Frage DeepSeek nach Entscheidung
   - Validiere Entscheidung
   - Prüfe Risk Management
   - Führe Trade aus (falls alles passt)

3. **Unabhängige Entscheidungen:**
   - Jedes Asset wird **separat analysiert**
   - BTC kann BUY Signal haben
   - ETH kann HOLD Signal haben
   - SOL kann SELL Signal haben
   - **Alle zur gleichen Zeit!**

---

## 🛡️ Risk Management

### Wichtig: Portfolio-weites Risk Management

```env
MAX_POSITION_SIZE=10000  # Pro Asset
MAX_EXPOSURE=0.7         # 70% TOTAL (alle Assets zusammen)
```

**Beispiel:**
- Portfolio: $100,000
- MAX_EXPOSURE: 70% = $70,000 max
- 5 Assets: BTC, ETH, SOL, ARB, AVAX

**Mögliche Verteilung:**
- BTC: $20,000 (20%)
- ETH: $15,000 (15%)
- SOL: $15,000 (15%)
- ARB: $10,000 (10%)
- AVAX: $10,000 (10%)
- **Total: $70,000 (70% ✅)**

### Risk Limits werden geprüft:

1. **Pro Asset:**
   - Max $10,000 Position Size
   - Dynamisches Sizing (Confidence, Volatility)

2. **Portfolio-weit:**
   - Total Exposure max 70%
   - Bei 3+ Positionen: Extra vorsichtig
   - Correlation Checks

3. **Drawdown Protection:**
   - Bei Drawdown: Alle Sizes reduziert
   - Emergency Stop: Alle Positionen schließen

---

## 📊 Logs & Monitoring

### Log Output mit Multi-Assets:

```
==========================================
HYPERLIQUID TRADING BOT STARTING
==========================================
Multi-asset mode: Trading 5 assets: BTC, ETH, SOL, ARB, AVAX
Initial Portfolio: $100,000.00
Available Balance: $100,000.00
Trading Assets: BTC, ETH, SOL, ARB, AVAX
==========================================

--- Trading Loop: 2025-10-29 14:00:00 ---

>>> Analyzing BTC <<<
Fetching market data for BTC...
Calculating technical indicators for BTC...
AI Decision for BTC: HOLD
Confluence Score: 3/10
BTC: Holding - no trade signal

>>> Analyzing ETH <<<
Fetching market data for ETH...
Calculating technical indicators for ETH...
AI Decision for ETH: BUY
Setup Quality: A | Confidence: 0.78
Confluence Score: 8/10
ETH: Order placed successfully

>>> Analyzing SOL <<<
Fetching market data for SOL...
SOL: Decision validation failed: Confluence too low

>>> Analyzing ARB <<<
ARB: Risk check failed: Max concurrent positions reached

>>> Analyzing AVAX <<<
AVAX: Holding - no trade signal

--- Trading Loop Complete ---
```

---

## ⚡ Performance Tipps

### 1. Start mit wenigen Assets

```env
# Anfang: 2-3 Assets
TRADING_ASSETS=BTC,ETH

# Nach Testing: Mehr hinzufügen
TRADING_ASSETS=BTC,ETH,SOL,ARB,AVAX
```

### 2. Wähle unterschiedliche Asset-Typen

**Gut diversifiziert:**
```env
TRADING_ASSETS=BTC,ETH,SOL,LINK,UNI
# Major L1, Major L1, Alt L1, Oracle, DeFi
```

**Schlecht (zu korreliert):**
```env
TRADING_ASSETS=UNI,AAVE,CRV,SUSHI,COMP
# Alles DeFi - stark korreliert!
```

### 3. Beachte Liquidität

Setze höhere Minimum-Liquidität bei vielen Assets:

```env
MIN_LIQUIDITY=2000000  # $2M statt $1M
```

### 4. Trading Interval anpassen

Mit vielen Assets dauert die Analyse länger:

```env
# 5 Assets = ~2-3 Minuten Analysezeit
TRADING_INTERVAL=300  # 5 Minuten OK

# 10 Assets = ~5-6 Minuten Analysezeit
TRADING_INTERVAL=600  # 10 Minuten besser
```

---

## 🎯 Best Practices

### ✅ Empfohlen:

1. **2-5 Assets für Start**
   ```env
   TRADING_ASSETS=BTC,ETH,SOL
   ```

2. **Diverse Asset-Typen**
   - 2x Major (BTC, ETH)
   - 1x Alt L1 (SOL, AVAX)
   - 1x DeFi (UNI, AAVE)
   - 1x Other (LINK, ARB)

3. **Höhere Confluence-Anforderung**
   ```env
   MIN_CONFIDENCE=0.65  # Statt 0.60
   ```

4. **Kleinere Position Sizes**
   ```env
   MAX_POSITION_SIZE=5000  # Statt 10000
   ```

### ❌ Vermeide:

1. **Zu viele Assets (>10)**
   - Schwer zu überwachen
   - Längere Analysezeit
   - Risk Management komplex

2. **Zu ähnliche Assets**
   ```env
   # Schlecht: Alle stark korreliert
   TRADING_ASSETS=BTC,ETH,BNB,LTC,BCH
   ```

3. **Low-Liquidity Assets**
   - Setze MIN_LIQUIDITY hoch
   - Checke 24h Volume auf Hyperliquid

---

## 🔍 Monitoring

### Portfolio Balance checken:

```bash
# Logs live anschauen
tail -f logs/trading_bot.log | grep -E "Portfolio|Position|Decision"
```

### Welche Assets sind aktiv?

```bash
grep "Analyzing" logs/trading_bot.log | tail -20
```

### Wie viele Positionen offen?

```bash
grep "Existing Positions:" logs/trading_bot.log | tail -1
```

---

## 🚨 Wichtige Hinweise

### 1. DeepSeek API Calls

**Mehr Assets = Mehr API Calls:**
- 1 Asset: 1 Call pro Loop
- 5 Assets: 5 Calls pro Loop
- 10 Assets: 10 Calls pro Loop

**Bei 5 Assets & 5min Interval:**
- Calls/Stunde: 60
- Calls/Tag: 1440
- Kosten: ~$1-2/Tag (je nach DeepSeek Pricing)

**Tipp:** Erhöhe TRADING_INTERVAL bei vielen Assets!

### 2. Hyperliquid Rate Limits

Hyperliquid hat API Rate Limits:
- Zu viele gleichzeitige Requests = Fehler
- Der Bot macht Requests sequentiell (kein Problem)

### 3. Correlation Risk

Assets können korreliert sein:
- Alle Altcoins folgen oft BTC
- Bei BTC Dump: Alles dumped
- Bot hat Correlation Checks eingebaut

---

## 📈 Beispiel-Szenarien

### Szenario 1: Conservative Trader

```env
TRADING_ASSETS=BTC,ETH
MAX_POSITION_SIZE=5000
RISK_PER_TRADE=0.01  # 1%
MAX_EXPOSURE=0.5     # 50%
MIN_CONFIDENCE=0.70
```

- Nur Majors
- Kleine Sizes
- Hohe Confidence
- **Wenig aber sicher**

### Szenario 2: Balanced Trader

```env
TRADING_ASSETS=BTC,ETH,SOL,AVAX
MAX_POSITION_SIZE=7500
RISK_PER_TRADE=0.015  # 1.5%
MAX_EXPOSURE=0.65     # 65%
MIN_CONFIDENCE=0.65
```

- Mix aus Majors + Alts
- Mittlere Sizes
- Standard Confidence
- **Ausgewogen**

### Szenario 3: Aggressive Trader

```env
TRADING_ASSETS=BTC,ETH,SOL,ARB,AVAX,MATIC,LINK
MAX_POSITION_SIZE=10000
RISK_PER_TRADE=0.02  # 2%
MAX_EXPOSURE=0.70    # 70%
MIN_CONFIDENCE=0.60
```

- Viele Assets
- Volle Sizes
- Standard Confidence
- **Maximale Opportunities**

---

## 🛠️ Troubleshooting

### "Too many API requests"

**Lösung:** Erhöhe TRADING_INTERVAL
```env
TRADING_INTERVAL=600  # 10 Minuten
```

### "Max concurrent positions reached"

**Normal!** Risk Management funktioniert.

**Ändern:**
```env
MAX_CONCURRENT_POSITIONS=5  # Statt 3
```

### "Portfolio exposure limit exceeded"

**Normal!** Risk Management schützt dich.

**Mehr Exposure erlauben:**
```env
MAX_EXPOSURE=0.80  # 80% statt 70%
```

### Assets werden nicht analysiert

**Prüfe:**
1. Sind Assets auf Hyperliquid verfügbar?
2. Haben Assets genug Liquidität?
3. Check Logs für Fehler

---

## 📚 Weitere Infos

- **Hyperliquid Assets:** https://app.hyperliquid.xyz/
- **Trading Config:** Siehe `.env` Datei
- **Risk Management:** Siehe `src/risk/manager.py`
- **Main Loop:** Siehe `src/main.py`

---

## ✅ Quick Start Multi-Asset

1. **Edit .env:**
   ```env
   TRADING_ASSETS=BTC,ETH,SOL
   ```

2. **Start Bot:**
   ```bash
   python run_bot.py
   ```

3. **Watch Logs:**
   ```bash
   tail -f logs/trading_bot.log
   ```

4. **Beobachte:**
   - Werden alle Assets analysiert?
   - Macht der Bot Trades?
   - Ist Exposure OK?

5. **Tuning:**
   - Mehr/weniger Assets
   - Anpasse MAX_POSITION_SIZE
   - Anpasse MIN_CONFIDENCE

---

**Viel Erfolg mit Multi-Asset Trading! 🚀📈**
