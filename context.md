# Hyper-Bot - Project Context Documentation

**Last Updated**: 2025-10-29
**Version**: 1.0
**Status**: Fully Operational on Testnet

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Key Components](#key-components)
4. [File Structure](#file-structure)
5. [Configuration](#configuration)
6. [Data Flow](#data-flow)
7. [Features](#features)
8. [Technical Stack](#technical-stack)
9. [Current Status](#current-status)
10. [Important Files](#important-files)
11. [Development History](#development-history)

---

## 🎯 Project Overview

**Hyper-Bot** is an AI-powered autonomous trading bot for the **Hyperliquid DEX** that uses **DeepSeek Reasoner** for intelligent trading decisions.

### Purpose
- Automated cryptocurrency trading on Hyperliquid testnet (and mainnet-ready)
- AI-driven decision making using DeepSeek's reasoning capabilities
- Multi-asset portfolio management (currently: BTC, ETH, DOGE, SOL, BNB)
- Optional YouTube livestream signal integration (XRPGEN channel)

### Core Philosophy
- **AI-First**: DeepSeek analyzes markets with deep chain-of-thought reasoning
- **Confluence-Based**: Requires minimum 4/10 confirming factors across trend/momentum/volume/microstructure
- **Risk-Aware**: Conservative position sizing, portfolio-wide exposure limits
- **Transparent**: All AI reasoning is logged to markdown files for review

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MAIN BOT (src/main.py)                 │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Portfolio  │    │   Position   │    │     Risk     │ │
│  │   Manager    │◄───┤   Manager    │◄───┤   Manager    │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         ▲                    ▲                    ▲         │
└─────────┼────────────────────┼────────────────────┼─────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Hyperliquid    │  │    DeepSeek     │  │   Technical     │
│  API Client     │  │   AI Engine     │  │   Analysis      │
│                 │  │                 │  │                 │
│ • Wallet Auth   │  │ • Reasoning     │  │ • 15+ Indics    │
│ • Order Exec    │  │ • Confluence    │  │ • Multi-TF      │
│ • Data Fetch    │  │ • Risk Assess   │  │ • Pattern Rec   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────┐
│              OPTIONAL: YouTube Livestream                │
│                                                          │
│   XRPGEN Stream → yt-dlp → GPT-4 Vision → Signals       │
└──────────────────────────────────────────────────────────┘
```

### Trading Loop Flow

```
Every 300 seconds (5 minutes):

1. Get Portfolio State (Hyperliquid API)
   └─→ Update peak equity for drawdown tracking

2. Monitor Existing Positions
   ├─→ Check Stop Loss hits
   ├─→ Check Take Profit levels
   ├─→ Update trailing stops
   └─→ Time-based exits (24h max)

3. For Each Asset (BTC, ETH, DOGE, SOL, BNB):
   │
   ├─→ Fetch Market Data (3 timeframes: 5m, 1h, 4h)
   │   ├─→ OHLCV candles
   │   ├─→ Orderbook depth
   │   └─→ Funding rate / OI
   │
   ├─→ Calculate Technical Indicators (15+ indicators)
   │   ├─→ Trend: EMA 20/50/200, ADX, Supertrend
   │   ├─→ Momentum: RSI, MACD, Stochastic
   │   ├─→ Volume: OBV, CVD, VWAP
   │   └─→ Volatility: ATR, Bollinger Bands
   │
   ├─→ Request AI Decision (DeepSeek Reasoner)
   │   ├─→ 6-Phase Deep Reasoning Framework
   │   ├─→ Bullish/Bearish/Neutral scenario analysis
   │   ├─→ Confluence scoring (minimum 4/10 required)
   │   └─→ Risk/Reward calculation
   │
   ├─→ Validate Decision
   │   ├─→ Confidence ≥ 0.6?
   │   ├─→ Setup quality ≥ GOOD?
   │   └─→ Confluence ≥ 4/10?
   │
   ├─→ Risk Management Check
   │   ├─→ Portfolio exposure < 70%?
   │   ├─→ Position size within limits?
   │   ├─→ Daily loss limit not exceeded?
   │   └─→ Emergency stop not triggered?
   │
   └─→ Execute Trade (if all checks pass)
       ├─→ Calculate dynamic position size
       ├─→ Set Stop Loss / Take Profit
       ├─→ Place order via Hyperliquid API
       └─→ Add to Position Manager

4. Save AI Reasoning to logs/ai_thinking/
   └─→ Detailed markdown report with full analysis

5. Sleep until next interval
```

---

## 🔧 Key Components

### 1. Hyperliquid Client (`src/hyperliquid/client.py`)

**Purpose**: Interface with Hyperliquid DEX

**Authentication**: Wallet-based (NOT API keys)
- Uses Ethereum wallet private key
- Signs transactions with EIP-712
- Libraries: `eth-account`, `web3`

**Key Methods**:
```python
- get_ticker(asset) → Current price
- get_candles(asset, timeframe, limit) → OHLCV data
- get_orderbook(asset, depth) → Bids/asks
- get_funding_rate(asset) → Funding rate, OI
- place_order(asset, side, size, order_type, price) → Execute order
- close_position(asset) → Market close position
- get_account_state() → Portfolio balance, positions
```

**Important**: XRP is NOT available on Hyperliquid!

### 2. DeepSeek AI Engine (`src/ai/deepseek_engine.py`)

**Purpose**: AI-powered trading decision making

**Model**: `deepseek-reasoner` (chain-of-thought reasoning model)

**Decision Framework** (6 Phases):
1. **Chart Analysis & Scenario Discussion**
   - Analyze bullish/bearish/neutral scenarios
   - Discuss different entry strategies

2. **Self-Discussion Entry Points**
   - Aggressive vs Conservative entry
   - Optimal entry balance

3. **Stop-Loss Placement**
   - Too tight vs too wide
   - Optimal: Below swing low/high + ATR buffer

4. **Take-Profit Strategy**
   - Multi-level TP (TP1: 30-50%, TP2: 30-40%, TP3: rest)
   - Trailing stop for runner

5. **Risk Assessment**
   - Edge quality scoring
   - R:R ratio calculation
   - Confluence validation

6. **Final Decision**
   - BUY, SELL, CLOSE_LONG, CLOSE_SHORT, HOLD
   - Confidence: 0-1 (min 0.6 required)
   - Confluence: 0-10 (min 4/10 required)

**Output**: Structured JSON with:
- Decision (BUY/SELL/HOLD/etc)
- Confidence & Confluence scores
- Market regime analysis
- Suggested action (entry, SL, TP levels)
- Full reasoning text
- Alternative scenarios

**Logging**: Saves detailed reasoning to `logs/ai_thinking/YYYY-MM-DD_HH-MM-SS_ASSET.md`

### 3. Technical Analysis (`src/analysis/indicators.py`)

**15+ Indicators** calculated across multiple timeframes:

**Trend Indicators**:
- EMA 20, 50, 200
- ADX (Average Directional Index)
- Supertrend
- Market structure (HH/HL for uptrend, LH/LL for downtrend)

**Momentum Indicators**:
- RSI (14-period)
- MACD (12, 26, 9)
- Stochastic Oscillator

**Volume Indicators**:
- OBV (On-Balance Volume)
- CVD (Cumulative Volume Delta)
- VWAP (Volume Weighted Average Price)

**Volatility Indicators**:
- ATR (Average True Range)
- Bollinger Bands (20, 2)

**All calculated for**:
- 5m timeframe (short-term)
- 1h timeframe (medium-term)
- 4h timeframe (long-term)

### 4. Risk Manager (`src/risk/manager.py`)

**Purpose**: Ensure safe trading within risk limits

**Portfolio-Level Limits**:
- Max exposure: 70% across ALL assets
- Daily loss limit: 5%
- Emergency stop: 20% drawdown from peak

**Per-Trade Limits**:
- Risk per trade: 2% of portfolio
- Max position size: $10,000 per asset
- Min confidence: 0.6 (60%)
- Min confluence: 4/10

**Dynamic Position Sizing**:
```python
Base size = Portfolio value × Risk per trade / Stop loss distance
Adjustments:
  × Confidence multiplier (0.5-1.5x)
  × Volatility adjustment (higher vol = smaller size)
  × Confluence bonus (≥6 confluence = larger size)
```

**Leverage Calculation**:
- BTC/ETH: Max 10x
- Large caps (SOL, BNB, etc): Max 5x
- Small caps: Max 3x
- Adjusted down based on volatility

### 5. Position Manager (`src/trading/position_manager.py`)

**Purpose**: Track and manage open positions

**Features**:
- Track entry price, size, leverage
- Monitor unrealized P&L
- Handle multi-level take profits
- Implement trailing stops
- Time-based exits (24h max duration)

**Stop Loss Management**:
- Initial SL set by AI decision
- Moves to breakeven after TP1 hit
- Trailing stop activates after TP2 hit

**Take Profit Levels**:
- TP1: Close 30-50% of position (quick profit)
- TP2: Close 30-40% of position (next resistance)
- TP3: Runner with trailing stop

### 6. YouTube Livestream Monitor (`src/sources/youtube_live_monitor.py`)

**Purpose**: Extract visual trading signals from XRPGEN livestream

**Status**: Implemented but DISABLED by default (requires OpenAI API key)

**How it works**:
1. Capture screenshot from YouTube livestream every 60s (via yt-dlp)
2. Send to GPT-4 Vision API
3. Extract trading signals (BTC, ETH, DOGE, SOL, BNB only - XRP ignored!)
4. Save to `data/livestream_signals.json`
5. Integration with DeepSeek (30% weight)

**Requirements**:
- OpenAI API key (GPT-4 Vision)
- ~$15-20/day for 60s intervals
- Active XRPGEN livestream

**Activation**:
```bash
# In .env:
YOUTUBE_LIVESTREAM_ENABLED=true
OPENAI_API_KEY=sk-proj-...
```

**Costs**:
- 60s interval: ~$14.40/day (1440 screenshots)
- 120s interval: ~$7.20/day (720 screenshots)
- 300s interval: ~$2.88/day (288 screenshots)

---

## 📁 File Structure

```
hyper-bot/
├── .env                          # Environment variables (SECRETS!)
├── .gitignore                    # Git ignore (includes .env)
├── requirements.txt              # Python dependencies
├── run_bot.py                    # Main entry point
│
├── context.md                    # THIS FILE - Project documentation
├── prompt.md                     # 32KB DeepSeek system prompt
├── HYPERLIQUID_SETUP.md         # Wallet setup guide (354 lines)
├── MULTI_ASSET_GUIDE.md         # Multi-asset trading guide
├── YOUTUBE_LIVESTREAM_SETUP.md  # Full YT livestream docs
├── YOUTUBE_QUICKSTART.md        # Quick setup for YT integration
│
├── logs/
│   ├── trading_bot.log          # Main log file
│   └── ai_thinking/             # AI reasoning logs (markdown)
│       ├── YYYY-MM-DD_HH-MM-SS_BTC.md
│       ├── YYYY-MM-DD_HH-MM-SS_ETH.md
│       └── ...
│
├── data/
│   ├── livestream_captures/     # YouTube screenshots (if enabled)
│   └── livestream_signals.json  # Extracted signals (if enabled)
│
├── src/
│   ├── __init__.py
│   ├── config.py                # Configuration management
│   ├── main.py                  # Main bot orchestrator (420 lines)
│   │
│   ├── hyperliquid/
│   │   ├── __init__.py
│   │   └── client.py            # Hyperliquid API client (wallet-based)
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   └── deepseek_engine.py   # DeepSeek reasoning engine (645 lines)
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── indicators.py        # Technical indicators (15+ indicators)
│   │
│   ├── risk/
│   │   ├── __init__.py
│   │   └── manager.py           # Risk management
│   │
│   ├── trading/
│   │   ├── __init__.py
│   │   └── position_manager.py  # Position tracking
│   │
│   ├── sources/
│   │   ├── __init__.py
│   │   └── youtube_live_monitor.py  # YouTube livestream integration
│   │
│   └── utils/
│       ├── __init__.py
│       └── models.py            # Data models (Pydantic)
│
└── venv/                        # Python virtual environment
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

**Critical (Required)**:
```bash
# Hyperliquid Wallet
HYPERLIQUID_WALLET_ADDRESS=0x...     # Public address
HYPERLIQUID_PRIVATE_KEY=xxx...       # KEEP SECRET!
HYPERLIQUID_TESTNET=true             # false for mainnet

# DeepSeek AI
DEEPSEEK_API_KEY=sk-...              # API key
DEEPSEEK_MODEL=deepseek-reasoner     # Reasoning model
```

**Trading Assets**:
```bash
TRADING_ASSETS=BTC,ETH,DOGE,SOL,BNB  # Comma-separated
DEFAULT_ASSET=BTC                     # Fallback
```

**Risk Management**:
```bash
MAX_POSITION_SIZE=10000              # Per asset (USD)
RISK_PER_TRADE=0.02                  # 2% per trade
MAX_EXPOSURE=0.7                     # 70% portfolio max
STOP_LOSS_PERCENT=0.05               # 5% base SL
TAKE_PROFIT_PERCENT=0.08             # 8% base TP
MIN_CONFIDENCE=0.6                   # 60% min to trade
```

**Trading Interval**:
```bash
TRADING_INTERVAL=300                 # Seconds (5 minutes)
```

**Optional - YouTube Livestream**:
```bash
YOUTUBE_LIVESTREAM_ENABLED=false     # Set true to enable
YOUTUBE_LIVESTREAM_URL=https://...   # XRPGEN channel
YOUTUBE_CAPTURE_INTERVAL=60          # Screenshot interval
VISION_PROVIDER=openai               # Vision AI provider
OPENAI_API_KEY=sk-proj-...           # For GPT-4 Vision
```

### Config Classes (`src/config.py`)

**Available Configs**:
- `HyperliquidConfig` - API & wallet settings
- `DeepSeekConfig` - AI model settings
- `TradingConfig` - Trading parameters
- `RiskConfig` - Risk limits
- `DatabaseConfig` - Database (SQLite)
- `LoggingConfig` - Log settings
- `VisionConfig` - Vision AI (YouTube)
- `YouTubeLivestreamConfig` - Livestream settings

**Usage**:
```python
from src.config import config

# Access settings
config.hyperliquid.wallet_address
config.trading.trading_assets
config.deepseek.model
```

---

## 🔄 Data Flow

### 1. Market Data Flow

```
Hyperliquid API
    ↓
get_multi_timeframe_data()
    ↓
{
  "5m": {candles, ticker, orderbook, funding},
  "1h": {candles, ticker, orderbook, funding},
  "4h": {candles, ticker, orderbook, funding}
}
    ↓
TechnicalAnalysis.calculate_all_indicators()
    ↓
{
  "5m": TechnicalIndicators,
  "1h": TechnicalIndicators,
  "4h": TechnicalIndicators
}
    ↓
DeepSeek AI Engine
```

### 2. AI Decision Flow

```
Market Data + Indicators + Portfolio State
    ↓
DeepSeek Prompt (32KB system prompt from prompt.md)
    ↓
DeepSeek Reasoner Model
    ↓
Chain-of-Thought Reasoning (6 phases)
    ↓
Structured JSON Response
    {
      decision: "BUY" | "SELL" | "HOLD" | ...,
      confidence: 0.75,
      confluence_score: 6,
      market_regime: {...},
      suggested_action: {entry, sl, tp},
      reasoning: "Full text explanation...",
      alternative_scenarios: {...}
    }
    ↓
Save to logs/ai_thinking/YYYY-MM-DD_HH-MM-SS_ASSET.md
    ↓
Validate (confidence, confluence, setup quality)
    ↓
Risk Management Check
    ↓
Execute Trade (if all pass)
```

### 3. Trade Execution Flow

```
Decision = BUY/SELL
    ↓
Calculate Position Size
    ├─→ Base: Portfolio × Risk / SL distance
    ├─→ × Confidence multiplier
    ├─→ × Volatility adjustment
    └─→ × Confluence bonus
    ↓
Calculate Leverage
    ├─→ BTC/ETH: Max 10x
    ├─→ Large cap: Max 5x
    ├─→ Adjusted for volatility
    └─→ Adjusted for confidence
    ↓
Place Order (Hyperliquid API)
    {
      asset: "BTC",
      side: "BUY",
      size: 0.15,
      type: "MARKET" | "LIMIT",
      price: 71500 (if LIMIT)
    }
    ↓
Create Position Object
    ↓
Add to Position Manager
    {
      entry_price, size, leverage,
      stop_loss, take_profit_levels,
      trailing_stop_config
    }
    ↓
Monitor in next loops
```

---

## 🎁 Features

### ✅ Implemented & Working

1. **Multi-Asset Trading**
   - Currently: BTC, ETH, DOGE, SOL, BNB
   - Easily extendable to any Hyperliquid asset
   - Portfolio-wide risk management

2. **DeepSeek Reasoning**
   - 6-phase deep analysis framework
   - Confluence-based decisions (min 4/10)
   - Multi-scenario analysis (bullish/bearish/neutral)

3. **Technical Analysis**
   - 15+ indicators
   - 3 timeframes (5m, 1h, 4h)
   - Pattern recognition

4. **Risk Management**
   - Dynamic position sizing
   - Portfolio exposure limits (70%)
   - Emergency stop (20% drawdown)
   - Per-trade risk (2%)

5. **Position Management**
   - Multi-level take profits (3 levels)
   - Trailing stops
   - Time-based exits (24h max)
   - Breakeven after TP1

6. **AI Thinking Logs**
   - Detailed markdown reports
   - Full reasoning exported
   - Confluence analysis
   - Alternative scenarios
   - Raw JSON response

7. **YouTube Livestream Integration**
   - XRPGEN channel support
   - GPT-4 Vision signal extraction
   - Filters for tradeable assets only
   - 30% weight in decisions

### 🚧 Partially Implemented

1. **YouTube Livestream**
   - Code complete
   - Requires OpenAI API key to activate
   - Costs ~$15-20/day

### ❌ Not Implemented

1. **Backtesting** (config exists, no engine)
2. **Database persistence** (SQLite configured, not used)
3. **Telegram notifications** (config exists, no implementation)
4. **Web dashboard** (not planned)
5. **Paper trading mode** (use testnet instead)

---

## 💻 Technical Stack

### Languages & Frameworks
- **Python 3.13** (requires >=3.11 for modern features)
- **AsyncIO** (async/await for concurrent API calls)

### Key Libraries

**Core**:
- `asyncio` - Asynchronous I/O
- `aiohttp` - Async HTTP client
- `loguru` - Beautiful logging
- `python-dotenv` - Environment variables
- `pydantic` - Data validation

**Trading**:
- `pandas>=2.2.0` - Data analysis (2.1.4 NOT compatible with Python 3.13!)
- `numpy>=1.26.0` - Numerical computations
- `ta` - Technical analysis indicators

**Hyperliquid (Wallet Auth)**:
- `eth-account>=0.10.0` - Ethereum wallet signing
- `web3>=6.0.0` - Web3 utilities

**YouTube (Optional)**:
- `yt-dlp` - YouTube video/stream capture
- `Pillow` - Image processing
- `openai` (not in requirements, uses direct API calls)

### APIs Used

1. **Hyperliquid API**
   - Base URL (Mainnet): `https://api.hyperliquid.xyz`
   - Testnet URL: `https://api.hyperliquid-testnet.xyz`
   - Authentication: Wallet-based (EIP-712 signing)
   - Endpoints: `/info`, `/exchange`

2. **DeepSeek API**
   - Base URL: `https://api.deepseek.com`
   - Model: `deepseek-reasoner`
   - Authentication: Bearer token
   - Cost: ~$0.001-0.01 per request

3. **OpenAI API** (Optional)
   - Base URL: `https://api.openai.com/v1`
   - Model: `gpt-4-vision-preview`
   - Authentication: Bearer token
   - Cost: ~$0.01 per image

---

## 📊 Current Status

### Environment
- **Network**: Hyperliquid Testnet
- **Wallet**: `0x97D3CDF5112a9d562b58E5ceEaad3Fdbc4f0a1F6`
- **Balance**: $999.00 USDC (testnet)
- **Open Positions**: 0

### Trading Assets
- ✅ BTC (Bitcoin)
- ✅ ETH (Ethereum)
- ✅ DOGE (Dogecoin)
- ✅ SOL (Solana)
- ✅ BNB (Binance Coin)
- ❌ XRP (NOT available on Hyperliquid!)

### Bot Status
- **Running**: Yes (process ID: 6a7fc6)
- **Loop Interval**: 300 seconds (5 minutes)
- **DeepSeek Model**: `deepseek-reasoner`
- **YouTube Integration**: DISABLED (no OpenAI key)

### Recent Performance
- **Trades Executed**: 0 (all HOLD decisions so far)
- **Reason**: Low market volatility, low volume, confluence <4
- **DeepSeek Confidence**: 0.20-0.30 (below 0.6 threshold)
- **Typical Confluence**: 2-3/10 (below 4/10 threshold)

**Bot is WORKING CORRECTLY** - being conservative due to poor market conditions!

---

## 📄 Important Files

### Must-Read Documentation

1. **`prompt.md`** (32KB)
   - Complete DeepSeek system prompt
   - Trading strategy explained
   - Confluence framework
   - Deep reasoning instructions
   - **READ THIS to understand AI decision-making!**

2. **`HYPERLIQUID_SETUP.md`** (354 lines)
   - Wallet-based authentication explained
   - How to setup wallet
   - Testnet faucet instructions
   - Security best practices

3. **`YOUTUBE_QUICKSTART.md`**
   - Quick setup for livestream integration
   - Cost calculator
   - Troubleshooting

4. **`context.md`** (THIS FILE)
   - Complete project overview
   - For future Claude sessions

### Configuration Files

1. **`.env`**
   - **SECRETS!** Never commit!
   - All environment variables
   - Trading parameters

2. **`requirements.txt`**
   - Python dependencies
   - **Important**: pandas>=2.2.0 for Python 3.13!

### Entry Points

1. **`run_bot.py`**
   - Simple entry point: `asyncio.run(main())`
   - Calls `src/main.py`

2. **`src/main.py`**
   - Main orchestrator
   - TradingBot class
   - Trading loop logic

### AI Components

1. **`src/ai/deepseek_engine.py`**
   - DeepSeek integration
   - Prompt building
   - Response parsing
   - AI thinking log generation

2. **`prompt.md`**
   - System prompt template
   - Injected into every AI request

### Data Models

1. **`src/utils/models.py`**
   - Pydantic data classes
   - `Decision`, `MarketRegime`, `TechnicalIndicators`
   - `SuggestedAction`, `StopLoss`, `TakeProfitLevel`
   - `Position`, `Portfolio`

---

## 📜 Development History

### Session 1: Initial Setup
- Project structure created
- Hyperliquid client (API key based - WRONG!)
- DeepSeek integration
- Basic prompt.md (8KB)

### Session 2: Multi-Asset Support
- User request: "es sollen nicht nur bitcoin sondern auch andere währungen gehandelt werden"
- Added multi-asset configuration
- Modified main.py to loop through assets
- Created MULTI_ASSET_GUIDE.md

### Session 3: Authentication Fix
- Discovery: "bei hyperliquid habe ich den api key erstellt aber da kann ich nur name und wallet address angeben, kein key oder sectret key"
- **MAJOR CHANGE**: Switched from API keys to wallet-based auth
- Implemented EIP-712 signing
- Added eth-account and web3 dependencies
- Created test_wallet.py verification script
- Created HYPERLIQUID_SETUP.md (354 lines)

### Session 4: Testing & Fixes
- Connected to testnet successfully
- Wallet: 0x97D3CDF5112a9d562b58E5ceEaad3Fdbc4f0a1F6
- Fixed candle API 422 errors (wrong endpoint format)
- Fixed HOLD decision parsing bug
- User added DeepSeek credits
- User claimed $999 USDC from testnet faucet

### Session 5: Deep Reasoning Enhancement
- User: "deepseek soll den chart ansehen und mit sich selber diskutieren wo der perfekte einstieg ein soll, der perfekte stoplos und der Take Profit"
- Switched to `deepseek-reasoner` model
- Enhanced prompt.md with 6-phase reasoning framework
- Added deep scenario analysis
- Results: Confidence increased from 0.10 to 0.30, Confluence from 1/10 to 3/10

### Session 6: AI Thinking Logs
- User: "kannst du das thinking des bots in ein log file schreiben damit ich es lesen kann"
- Implemented `_save_reasoning_log()` method
- Creates detailed markdown files in `logs/ai_thinking/`
- Comprehensive logs with reasoning, confluence, risk assessment
- Fixed import error (List not imported)

### Session 7: Asset Update
- User: "der bot soll sich BTC, ETH, XRP, SOL und BNB genau anschauen"
- Discovered XRP NOT available on Hyperliquid
- Replaced XRP with DOGE
- Final assets: BTC, ETH, DOGE, SOL, BNB

### Session 8: YouTube Livestream Integration
- User: "das ist der link zu den lives: https://www.youtube.com/@XRPGEN/streams"
- Created complete YouTube livestream monitoring system
- Implemented GPT-4 Vision integration
- Custom prompt for XRPGEN channel
- Filters for Hyperliquid-compatible assets only
- Created YOUTUBE_LIVESTREAM_SETUP.md
- Created YOUTUBE_QUICKSTART.md
- Status: Implemented but DISABLED (requires OpenAI API key)

### Session 9: Context Documentation
- User: "erstelle jetzt eine context.md file und beschreibe den aufbau den bot und alles was es zu wissen gibt"
- Created comprehensive context.md (THIS FILE)
- Documented entire project for future Claude sessions

---

## 🔐 Security Notes

### Secrets Management
- **NEVER commit `.env` file!**
- `.gitignore` includes `.env`
- Contains:
  - Private key (full wallet access!)
  - DeepSeek API key
  - OpenAI API key (if used)

### Wallet Safety
- **Testnet only** for now (HYPERLIQUID_TESTNET=true)
- Test wallet has $999 testnet USDC (no real value)
- **Before mainnet**:
  - Thoroughly test on testnet
  - Review risk management settings
  - Start with small amounts
  - Never expose private keys

### API Keys
- DeepSeek key: Limited to API access
- OpenAI key: Can incur charges (monitor billing!)

---

## 🚀 Quick Start for New Session

### If bot is already running:
```bash
# Check logs
tail -f logs/trading_bot.log

# Check AI thinking
ls -lht logs/ai_thinking/

# Check latest reasoning
cat logs/ai_thinking/$(ls -t logs/ai_thinking/ | head -1)
```

### If bot needs restart:
```bash
# Activate venv
source venv/bin/activate

# Start bot
./venv/bin/python run_bot.py

# Or in background
nohup ./venv/bin/python run_bot.py > /dev/null 2>&1 &
```

### To modify configuration:
```bash
# Edit environment variables
nano .env

# Then restart bot
```

### To check available assets:
```bash
python -c "
import asyncio, sys
sys.path.insert(0, '.')
from src.hyperliquid.client import HyperliquidClient
from src.config import config

async def check():
    client = HyperliquidClient(config.hyperliquid)
    async with client:
        data = await client._request('POST', '/info', {'type': 'allMids'})
        print('Available:', list(data.keys())[:20])

asyncio.run(check())
"
```

---

## 🐛 Common Issues & Solutions

### Issue: "Asset XYZ not found"
- Check if asset is available on Hyperliquid
- Use asset check script above
- Update TRADING_ASSETS in .env

### Issue: "pandas compatibility error"
- Ensure pandas>=2.2.0 (NOT 2.1.4!)
- Python 3.13 requires pandas 2.2.0+

### Issue: "DeepSeek insufficient balance"
- Add credits to DeepSeek account
- Check: https://platform.deepseek.com

### Issue: "All decisions are HOLD"
- **This is NORMAL in low-volume/low-volatility markets!**
- Bot requires:
  - Confidence ≥ 0.6
  - Confluence ≥ 4/10
  - Setup quality ≥ GOOD
- Check AI thinking logs to see why

### Issue: "YouTube capture failed"
- Check if stream is live
- Check yt-dlp is installed: `pip list | grep yt-dlp`
- Test manually: `yt-dlp --write-thumbnail --skip-download "URL"`

---

## 📈 Performance Expectations

### Realistic Trade Frequency
- **High volatility**: 1-3 trades per asset per day
- **Medium volatility**: 0-1 trade per asset per day
- **Low volatility**: Many HOLD decisions (NORMAL!)

### Bot is Conservative by Design
- Requires 4+ confirming factors (confluence)
- Min 60% confidence
- Dynamic risk management
- **Better to miss opportunity than take bad trade**

---

## 🎯 Future Enhancements (Ideas)

### Potential Features
1. Backtesting engine (config exists)
2. Multiple strategy profiles
3. Machine learning for parameter optimization
4. Correlation-based portfolio balancing
5. News sentiment integration
6. Multiple exchange support (Binance, Bybit)
7. Web dashboard for monitoring
8. Telegram bot for notifications

### Code Improvements
1. Database persistence (SQLite configured but unused)
2. More comprehensive testing
3. Strategy A/B testing framework
4. Performance analytics

---

## 📞 Support & Resources

### Documentation
- This file (`context.md`)
- `prompt.md` - AI strategy
- `HYPERLIQUID_SETUP.md` - Wallet setup
- `YOUTUBE_QUICKSTART.md` - Livestream setup

### External Resources
- Hyperliquid Docs: https://hyperliquid.gitbook.io/
- DeepSeek API: https://platform.deepseek.com/
- OpenAI Vision: https://platform.openai.com/docs/guides/vision

### Debugging
- Logs: `logs/trading_bot.log`
- AI Reasoning: `logs/ai_thinking/*.md`
- Livestream Signals: `data/livestream_signals.json`

---

## ✅ Checklist for New Claude Session

When starting a new session, review:

- [ ] Read `context.md` (THIS FILE) for overview
- [ ] Check bot status: `ps aux | grep run_bot.py`
- [ ] Review recent logs: `tail -100 logs/trading_bot.log`
- [ ] Check AI thinking logs: `ls -lht logs/ai_thinking/ | head -5`
- [ ] Verify .env configuration
- [ ] Check current portfolio: Balance, open positions
- [ ] Review recent decisions: Why HOLD vs BUY/SELL?

---

**Last Updated**: 2025-10-29
**Project Status**: Fully Operational on Testnet
**Next Session**: Ready to continue development or monitoring

---

**END OF CONTEXT DOCUMENTATION**
