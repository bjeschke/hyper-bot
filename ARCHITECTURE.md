# Hyperliquid Trading Bot - Architektur

## Übersicht

Der Bot besteht aus mehreren Modulen, die zusammenarbeiten, um automatisiertes Trading auf Hyperliquid durchzuführen, wobei DeepSeek für Entscheidungen genutzt wird.

## System-Komponenten

```
┌─────────────────────────────────────────────────────────────┐
│                      Trading Bot Main                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│   Hyperliquid│    │   DeepSeek AI    │    │   Risk      │
│   API Client │    │   Decision Engine│    │   Manager   │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│   Market     │    │   Technical      │    │   Position  │
│   Data       │    │   Analysis       │    │   Manager   │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    ┌──────────────────┐
                    │   Database /     │
                    │   Logging        │
                    └──────────────────┘
```

## Module

### 1. Hyperliquid API Client
**Datei**: `src/hyperliquid/client.py`

**Funktionen**:
- Verbindung zur Hyperliquid API
- Marktdaten abrufen (Preise, Orderbook, Funding Rates)
- Orders platzieren (Market, Limit)
- Portfolio-Status abfragen
- Historische Daten laden

**Wichtige Methoden**:
```python
class HyperliquidClient:
    def get_market_data(asset: str) -> MarketData
    def get_orderbook(asset: str, depth: int) -> Orderbook
    def place_order(order: Order) -> OrderResult
    def get_position(asset: str) -> Position
    def get_account_balance() -> Balance
    def get_funding_rate(asset: str) -> float
```

### 2. Technical Analysis Engine
**Datei**: `src/analysis/indicators.py`

**Funktionen**:
- Berechnung technischer Indikatoren
- RSI, MACD, Bollinger Bands, EMAs
- Volume Profile Analysis
- Trend Detection

**Wichtige Methoden**:
```python
class TechnicalAnalysis:
    def calculate_rsi(prices: List[float], period: int = 14) -> float
    def calculate_macd(prices: List[float]) -> MACD
    def calculate_bollinger_bands(prices: List[float]) -> BollingerBands
    def calculate_ema(prices: List[float], period: int) -> float
    def analyze_volume_profile(volume_data: List) -> VolumeProfile
```

### 3. DeepSeek AI Decision Engine
**Datei**: `src/ai/deepseek_engine.py`

**Funktionen**:
- Prompt-Generierung aus Marktdaten
- API-Kommunikation mit DeepSeek
- Parsing der AI-Entscheidungen
- Confidence-Score Bewertung

**Wichtige Methoden**:
```python
class DeepSeekEngine:
    def __init__(api_key: str, model: str = "deepseek-chat")
    def generate_prompt(market_data: MarketData, indicators: Indicators) -> str
    def get_trading_decision(prompt: str) -> TradingDecision
    def validate_decision(decision: TradingDecision) -> bool
```

### 4. Risk Manager
**Datei**: `src/risk/manager.py`

**Funktionen**:
- Position-Sizing berechnen
- Stop-Loss / Take-Profit setzen
- Portfolio-Exposure überwachen
- Risk-Reward Ratio validieren

**Wichtige Methoden**:
```python
class RiskManager:
    def calculate_position_size(capital: float, risk_percent: float) -> float
    def validate_trade(trade: Trade, portfolio: Portfolio) -> bool
    def calculate_stop_loss(entry_price: float, risk: float) -> float
    def calculate_take_profit(entry_price: float, reward: float) -> float
    def check_exposure(portfolio: Portfolio) -> float
```

### 5. Position Manager
**Datei**: `src/trading/position_manager.py`

**Funktionen**:
- Offene Positionen tracken
- P&L berechnen
- Position-Updates verarbeiten
- Liquidation Risk überwachen

**Wichtige Methoden**:
```python
class PositionManager:
    def open_position(trade: Trade) -> Position
    def close_position(position_id: str, price: float) -> ClosedPosition
    def update_position(position_id: str, market_price: float)
    def get_unrealized_pnl(position: Position) -> float
    def check_liquidation_risk(position: Position) -> float
```

### 6. Main Trading Loop
**Datei**: `src/main.py`

**Funktionen**:
- Orchestrierung aller Module
- Trading-Loop mit festem Interval
- Error Handling
- Logging und Monitoring

## Datenmodelle

### MarketData
```python
@dataclass
class MarketData:
    asset: str
    timestamp: datetime
    price: float
    volume_24h: float
    high_24h: float
    low_24h: float
    price_change_24h: float
    funding_rate: float
    open_interest: float
    long_short_ratio: float
```

### Indicators
```python
@dataclass
class Indicators:
    rsi: float
    macd: MACD
    bollinger_bands: BollingerBands
    ema_20: float
    ema_50: float
    volume_profile: VolumeProfile
```

### TradingDecision
```python
@dataclass
class TradingDecision:
    decision: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    reasoning: str
    indicators_summary: dict
    suggested_action: Order
    risk_assessment: RiskAssessment
```

## Technologie-Stack

### Backend
- **Python 3.11+**
- **asyncio**: Für asynchrone API-Calls
- **aiohttp**: HTTP Client für Hyperliquid API
- **pandas**: Datenverarbeitung und technische Analyse
- **ta-lib**: Technische Indikatoren (optional)
- **python-dotenv**: Environment Variables

### AI Integration
- **DeepSeek API**: Chat Completion API
- **openai**: Python SDK (kompatibel mit DeepSeek)

### Datenbank
- **SQLite**: Lokale Datenbank für Trades und Logs
- **PostgreSQL**: Optional für Production

### Monitoring
- **loguru**: Enhanced Logging
- **prometheus-client**: Metrics (optional)

## Installation & Setup

### 1. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
```env
# .env
HYPERLIQUID_API_KEY=your_api_key
HYPERLIQUID_SECRET=your_secret
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Trading Config
DEFAULT_ASSET=BTC
MAX_POSITION_SIZE=10000
RISK_PER_TRADE=0.02
MAX_EXPOSURE=0.7
TRADING_INTERVAL=300  # seconds

# Risk Management
STOP_LOSS_PERCENT=0.05
TAKE_PROFIT_PERCENT=0.08
MIN_CONFIDENCE=0.6
```

### 3. Projekt-Struktur
```
hyper-bot/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── hyperliquid/
│   │   ├── __init__.py
│   │   └── client.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── indicators.py
│   ├── ai/
│   │   ├── __init__.py
│   │   └── deepseek_engine.py
│   ├── risk/
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── trading/
│   │   ├── __init__.py
│   │   └── position_manager.py
│   └── database/
│       ├── __init__.py
│       └── models.py
├── tests/
│   └── ...
├── prompt.md
├── ARCHITECTURE.md
├── requirements.txt
├── .env.example
└── README.md
```

## Trading Flow

1. **Daten sammeln**: Market Data von Hyperliquid abrufen
2. **Analyse**: Technische Indikatoren berechnen
3. **Prompt erstellen**: Daten in Prompt für DeepSeek formatieren
4. **AI Entscheidung**: DeepSeek analysiert und gibt Empfehlung
5. **Risk Check**: Risk Manager validiert Entscheidung
6. **Execution**: Falls validiert, Order platzieren
7. **Monitoring**: Position überwachen und bei Bedarf anpassen
8. **Logging**: Alle Aktionen in Datenbank speichern

## Sicherheitsüberlegungen

1. **API Keys**: Niemals in Code committen, immer .env nutzen
2. **Rate Limiting**: API-Calls limitieren um Bans zu vermeiden
3. **Error Handling**: Robuste Fehlerbehandlung für alle API-Calls
4. **Position Limits**: Harte Grenzen für maximale Positionen
5. **Emergency Stop**: Kill-Switch für sofortigen Trading-Stop
6. **Testnet**: Erst auf Testnet testen vor Mainnet
7. **Monitoring**: Alerts bei unerwarteten Verlusten

## Nächste Schritte

1. Hyperliquid API Client implementieren
2. Technical Analysis Module entwickeln
3. DeepSeek Integration aufbauen
4. Risk Management implementieren
5. Backtesting-Framework erstellen
6. Paper Trading (Simulation) durchführen
7. Schrittweise auf Testnet deployen
8. Nach gründlichem Testing auf Mainnet wechseln

## Weiterführende Ressourcen

- **Hyperliquid Docs**: https://hyperliquid.gitbook.io/
- **DeepSeek API**: https://platform.deepseek.com/
- **TA-Lib Documentation**: https://ta-lib.org/
