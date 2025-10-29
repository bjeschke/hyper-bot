# Hyperliquid Trading Bot mit DeepSeek AI

Ein automatisierter Trading-Bot für Hyperliquid DEX, der DeepSeek AI für intelligente Trading-Entscheidungen nutzt.

## Features

- **AI-gestützte Entscheidungen**: Nutzt DeepSeek für Marktanalyse und Trading-Signale
- **Multi-Asset Trading**: Handelt mehrere Kryptowährungen gleichzeitig
- **Technische Analyse**: 15+ Indikatoren (RSI, MACD, Bollinger Bands, EMAs, ADX, Supertrend, VWAP, etc.)
- **Confluence-Based Signals**: Mindestens 4 bestätigende Faktoren für Trade-Execution
- **Risk Management**: Automatische Stop-Loss und Take-Profit Orders
- **Real-time Monitoring**: Kontinuierliche Überwachung von Positionen und Märkten
- **Wallet-basierte Authentifizierung**: Sichere Hyperliquid-Integration via Ethereum Wallet
- **Umfassendes Logging**: Alle Trades und Entscheidungen werden protokolliert

## Schnellstart

### 1. Installation

```bash
# Repository klonen
git clone <your-repo-url>
cd hyper-bot

# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt
```

### 2. Wallet Setup

**⚠️ WICHTIG: Hyperliquid nutzt Wallet-basierte Authentifizierung (nicht API Keys)!**

Du benötigst ein Ethereum Wallet mit Private Key. Siehe [HYPERLIQUID_SETUP.md](HYPERLIQUID_SETUP.md) für detaillierte Anleitung.

**Kurzversion:**
1. Erstelle ein separates Trading-Wallet (z.B. via MetaMask)
2. Exportiere den Private Key
3. Besorge Testnet Funds: https://testnet.hyperliquid.xyz/faucet

### 3. Konfiguration

Erstelle eine `.env` Datei mit deinen Credentials:

```env
# Hyperliquid Wallet Configuration
HYPERLIQUID_WALLET_ADDRESS=0x...  # Deine Wallet Address
HYPERLIQUID_PRIVATE_KEY=0x...     # Private Key (GEHEIM!)
HYPERLIQUID_TESTNET=true          # true für Testnet, false für Mainnet

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Trading Configuration (Multi-Asset)
TRADING_ASSETS=BTC,ETH,SOL,ARB,AVAX  # Comma-separated list
DEFAULT_ASSET=BTC
MAX_POSITION_SIZE=10000
RISK_PER_TRADE=0.02
MAX_EXPOSURE=0.7
TRADING_INTERVAL=300

# Risk Management
STOP_LOSS_PERCENT=0.05
TAKE_PROFIT_PERCENT=0.08
MIN_CONFIDENCE=0.6
MIN_LIQUIDITY=1000000
```

### 4. Wallet Verifizierung

Teste dein Wallet Setup:

```bash
python test_wallet.py
```

Dieser Test verifiziert:
- ✅ Private Key ist valide
- ✅ Wallet Address passt zum Private Key
- ✅ Verbindung zu Hyperliquid funktioniert
- ✅ Account Balance wird angezeigt

### 5. Bot starten

```bash
python run_bot.py
```

Monitor logs:
```bash
tail -f logs/trading_bot.log
```

## Projekt-Struktur

```
hyper-bot/
├── src/                    # Source Code
│   ├── main.py            # Haupteinstiegspunkt
│   ├── config.py          # Konfiguration
│   ├── hyperliquid/       # Hyperliquid API Client
│   ├── analysis/          # Technische Analyse
│   ├── ai/                # DeepSeek Integration
│   ├── risk/              # Risk Management
│   ├── trading/           # Position Management
│   └── database/          # Datenbank Modelle
├── tests/                 # Unit Tests
├── prompt.md             # DeepSeek Prompt Template
├── ARCHITECTURE.md       # Ausführliche Architektur-Dokumentation
├── requirements.txt      # Python Dependencies
└── README.md            # Diese Datei
```

## Architektur

Der Bot besteht aus mehreren Modulen:

1. **Hyperliquid API Client**: Verbindung zur Exchange
2. **Technical Analysis Engine**: Berechnung von Indikatoren
3. **DeepSeek AI Engine**: AI-basierte Entscheidungsfindung
4. **Risk Manager**: Risikokontrolle und Positionsgrößen
5. **Position Manager**: Verwaltung offener Positionen
6. **Database Layer**: Persistierung von Trades und Logs

Siehe [ARCHITECTURE.md](ARCHITECTURE.md) für Details.

## DeepSeek Prompt

Der Bot nutzt einen strukturierten Prompt für DeepSeek. Siehe [prompt.md](prompt.md) für das vollständige Template.

Der Prompt enthält:
- Aktuelle Marktdaten (Preis, Volumen, etc.)
- Technische Indikatoren (RSI, MACD, etc.)
- Portfolio-Status
- Risk Management Regeln
- Trading-Strategie Richtlinien
- Strukturiertes JSON-Ausgabeformat

## Beispiel Trading-Entscheidung

DeepSeek gibt Entscheidungen in folgendem Format zurück:

```json
{
  "decision": "BUY",
  "confidence": 0.75,
  "reasoning": "RSI zeigt überverkaufte Bedingungen...",
  "indicators_summary": {
    "rsi_signal": "bullish",
    "macd_signal": "bullish",
    "trend_signal": "bullish",
    "volume_signal": "strong"
  },
  "suggested_action": {
    "type": "LIMIT",
    "side": "BUY",
    "quantity": 0.1,
    "price": 44950,
    "stop_loss": 42700,
    "take_profit": 48600
  },
  "risk_assessment": {
    "risk_level": "MEDIUM",
    "risk_reward_ratio": 1.6,
    "notes": "Gute R:R Ratio"
  }
}
```

## Risk Management

Der Bot implementiert mehrere Sicherheitsmechanismen:

- **Maximales Risiko**: 2% pro Trade
- **Position Limits**: Maximale Exposure von 70%
- **Stop-Loss**: Automatisch bei -5%
- **Take-Profit**: Ziel bei +8%
- **Confidence Threshold**: Nur Trades mit > 60% Confidence
- **Liquidität Check**: Minimum 24h Volumen

## Development

### Tests ausführen

```bash
pytest tests/
```

### Backtesting

```bash
python src/backtest.py --start 2024-01-01 --end 2024-12-31 --asset BTC
```

### Linting

```bash
flake8 src/
black src/
```

## Sicherheitshinweise

⚠️ **WICHTIG**:

1. **Nie mit echtem Geld starten**: Erst gründlich auf Testnet testen
2. **API Keys schützen**: Niemals in Git committen
3. **Kleine Beträge**: Starte mit minimalen Positionsgrößen
4. **Monitoring**: Bot regelmäßig überwachen
5. **Stop-Loss**: Immer aktiv haben
6. **Risiko verstehen**: Nur investieren, was du bereit bist zu verlieren

## Dokumentation

- **[HYPERLIQUID_SETUP.md](HYPERLIQUID_SETUP.md)**: Detaillierte Wallet-Setup Anleitung
- **[MULTI_ASSET_GUIDE.md](MULTI_ASSET_GUIDE.md)**: Multi-Asset Trading Konfiguration
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System-Architektur Details
- **[prompt.md](prompt.md)**: DeepSeek AI Prompt Template

## Roadmap

- [x] Grundlegende Architektur
- [x] DeepSeek Prompt Template (32KB Production-Grade)
- [x] Hyperliquid API Client (Wallet-basiert)
- [x] Technical Analysis Module (15+ Indikatoren)
- [x] DeepSeek Integration
- [x] Risk Management System
- [x] Position Manager
- [x] Multi-Asset Support
- [x] Wallet-basierte Authentifizierung
- [ ] Backtesting Framework
- [ ] Paper Trading Mode
- [ ] Web Dashboard
- [ ] Telegram Notifications
- [ ] Performance Analytics

## Contributing

Contributions sind willkommen! Bitte erstelle ein Issue oder Pull Request.

## Lizenz

MIT License

## Disclaimer

Dieser Bot ist für Bildungszwecke. Trading birgt erhebliche Risiken. Nutze ihn auf eigene Gefahr. Die Entwickler übernehmen keine Haftung für finanzielle Verluste.

## Support

Bei Fragen oder Problemen erstelle ein Issue auf GitHub.

---

**Viel Erfolg beim Trading! 📈🤖**
