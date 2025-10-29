# Hyperliquid Trading Bot - Quickstart

Schnellster Weg um den Bot zum Laufen zu bringen.

## 🚀 In 5 Minuten zum ersten Trade

### 1️⃣ Dependencies installieren (2 Minuten)

```bash
# Virtual Environment aktivieren
source venv/bin/activate

# Falls noch nicht geschehen, alle Dependencies installieren
pip install -r requirements.txt
```

### 2️⃣ Wallet erstellen (2 Minuten)

**Option A: Neues Wallet erstellen (EMPFOHLEN)**

```bash
# Erstelle ein neues Wallet mit Python
python3 << 'EOF'
from eth_account import Account
account = Account.create()
print(f"\n=== DEIN NEUES TRADING WALLET ===")
print(f"Address:     {account.address}")
print(f"Private Key: {account.key.hex()}")
print(f"\n⚠️  WICHTIG: Private Key sicher aufbewahren!")
EOF
```

Kopiere die ausgegeben Werte!

**Option B: Existierendes Wallet nutzen**

1. Öffne MetaMask
2. Klicke auf ⋮ → Account Details
3. "Show Private Key" → Passwort eingeben
4. Private Key kopieren

### 3️⃣ .env konfigurieren (1 Minute)

```bash
# Bearbeite .env Datei
nano .env  # oder dein bevorzugter Editor
```

**Minimale Konfiguration:**

```env
# Hyperliquid Wallet (von Schritt 2)
HYPERLIQUID_WALLET_ADDRESS=0xdeine_wallet_address_hier
HYPERLIQUID_PRIVATE_KEY=0xdein_private_key_hier
HYPERLIQUID_TESTNET=true

# DeepSeek API
DEEPSEEK_API_KEY=sk-dein_deepseek_key_hier

# Trading Assets (optional)
TRADING_ASSETS=BTC,ETH,SOL
```

Speichern mit: `Ctrl+O`, `Enter`, `Ctrl+X`

### 4️⃣ Testnet Funds bekommen

**Option A: Faucet (schnellste Methode)**

1. Gehe zu: https://testnet.hyperliquid.xyz/faucet
2. Gib deine Wallet Address ein
3. Klicke "Request Funds"
4. Warte 1-2 Minuten

**Option B: Discord**

1. Discord: https://discord.gg/hyperliquid
2. Gehe zu #testnet-faucet
3. Poste: `!faucet 0xdeine_wallet_address`

### 5️⃣ Wallet testen

```bash
python test_wallet.py
```

**Erwartete Ausgabe:**
```
✅ Private Key loaded
✅ Addresses match! Setup correct!
✅ Successfully connected to Hyperliquid Testnet
✅ Account Value: $1,000.00
```

### 6️⃣ Bot starten! 🎉

```bash
python run_bot.py
```

**Du solltest sehen:**
```
Initialized Hyperliquid client for wallet: 0x742d35Cc...
Hyperliquid API health check passed
Initial Portfolio: $1,000.00
Trading Assets: BTC, ETH, SOL
Starting trading loop...
```

---

## ✅ Checkliste

Bevor du den Bot startest:

- [ ] Python Virtual Environment aktiviert
- [ ] Dependencies installiert (`pip install -r requirements.txt`)
- [ ] Wallet erstellt oder Private Key exportiert
- [ ] `.env` Datei konfiguriert
- [ ] Testnet Funds erhalten
- [ ] `test_wallet.py` erfolgreich durchgelaufen
- [ ] Testnet (nicht Mainnet!)

---

## 🔍 Troubleshooting

### "HYPERLIQUID_PRIVATE_KEY is required"

→ Deine `.env` Datei ist nicht korrekt konfiguriert.
→ Stelle sicher dass die Werte keine Platzhalter mehr sind (`0x...`)

### "Addresses don't match"

→ Wallet Address in `.env` stimmt nicht mit Private Key überein
→ Führe aus: `python test_wallet.py` um die korrekte Address zu sehen

### "Insufficient balance"

→ Keine Testnet Funds im Wallet
→ Besorge Funds vom Faucet oder Discord (siehe Schritt 4)

### "Connection timeout"

→ Internet Verbindung prüfen
→ Prüfe ob Hyperliquid erreichbar ist: https://app.hyperliquid-testnet.xyz/

---

## 📚 Nächste Schritte

Sobald der Bot läuft:

1. **Monitor Logs**: `tail -f logs/trading_bot.log`
2. **Verstehe die Entscheidungen**: Lese die Log-Ausgaben
3. **Anpasse Konfiguration**: Siehe [MULTI_ASSET_GUIDE.md](MULTI_ASSET_GUIDE.md)
4. **Lerne die Architektur**: Siehe [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🔐 Sicherheit

### DO:
✅ Separates Trading-Wallet für Bot
✅ Nur Testnet-Funds
✅ `.env` in `.gitignore`
✅ Private Key geheim halten

### DON'T:
❌ Haupt-Wallet verwenden
❌ Private Key teilen oder posten
❌ Mainnet ohne gründliches Testing
❌ `.env` committen

---

## 💡 Tipps

**Für Anfänger:**
- Starte mit nur 1 Asset: `TRADING_ASSETS=BTC`
- Nutze konservative Settings:
  ```env
  RISK_PER_TRADE=0.01  # 1% statt 2%
  MIN_CONFIDENCE=0.7   # 70% statt 60%
  ```

**Für Fortgeschrittene:**
- Multi-Asset Trading: `TRADING_ASSETS=BTC,ETH,SOL,ARB,AVAX`
- Schnellere Updates: `TRADING_INTERVAL=60`
- Höhere Exposure: `MAX_EXPOSURE=0.8`

**Performance Monitoring:**
```bash
# Logs in Echtzeit
tail -f logs/trading_bot.log

# Suche nach Trades
grep "Placing" logs/trading_bot.log

# Fehler finden
grep "ERROR" logs/trading_bot.log
```

---

## ❓ Hilfe

- **Wallet Setup**: Siehe [HYPERLIQUID_SETUP.md](HYPERLIQUID_SETUP.md)
- **Multi-Asset**: Siehe [MULTI_ASSET_GUIDE.md](MULTI_ASSET_GUIDE.md)
- **Architektur**: Siehe [ARCHITECTURE.md](ARCHITECTURE.md)
- **GitHub Issues**: https://github.com/your-repo/issues

---

**Viel Erfolg! 🚀**
