# Hyperliquid Wallet Setup Guide

## 🔑 Wichtig: Hyperliquid nutzt Wallet-basierte Authentifizierung!

Hyperliquid verwendet **keine traditionellen API Keys** (wie Binance/Coinbase).
Stattdessen nutzt es **Ethereum-Wallet-basierte Authentifizierung**.

Du brauchst:
1. ✅ **Wallet Address** (deine öffentliche Adresse)
2. ✅ **Private Key** (dein geheimer Schlüssel)

---

## 📝 Option 1: Neues Wallet für Trading erstellen (EMPFOHLEN)

### Warum ein separates Wallet?

🔒 **Sicherheit!** Erstelle ein dediziertes Trading-Wallet:
- Nutze NICHT dein Haupt-Wallet
- Nur Trading-Funds dort halten
- Private Key nur für diesen Bot

### Schritt 1: Erstelle neues Wallet

**Mit MetaMask:**

1. Öffne MetaMask
2. Klicke auf Account-Icon → "Create Account"
3. Name: "Hyperliquid Trading Bot"
4. Bestätige

**Oder nutze ein Tool:**

```bash
# Mit Python (eth-account)
python3 << 'EOF'
from eth_account import Account
account = Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
EOF
```

### Schritt 2: Exportiere Private Key aus MetaMask

1. **MetaMask öffnen**
2. **Klicke auf die 3 Punkte** (⋮) neben dem Account
3. **"Account Details"** auswählen
4. **"Show Private Key"** klicken
5. **Passwort eingeben**
6. **Private Key kopieren** (beginnt mit `0x...`)

⚠️ **WICHTIG**: Private Key niemals teilen oder online posten!

### Schritt 3: Funds auf Testnet übertragen

Für Hyperliquid **Testnet**:

1. Gehe zu: **https://app.hyperliquid-testnet.xyz/**
2. Verbinde dein neues Wallet
3. Beantrage Testnet Funds:
   - **Faucet**: https://testnet.hyperliquid.xyz/faucet
   - Oder frage im Discord: https://discord.gg/hyperliquid

---

## 📝 Option 2: Bestehendes Wallet nutzen (Vorsichtig!)

### ⚠️ Nur wenn du weißt was du tust!

**Risiken:**
- Private Key wird im Bot gespeichert
- Bei Hack: Wallet kompromittiert
- Empfohlen nur für Testnet!

### Private Key exportieren:

#### Aus MetaMask:

1. MetaMask öffnen
2. Account auswählen
3. ⋮ → Account Details
4. "Show Private Key"
5. Passwort eingeben
6. Private Key kopieren

#### Aus anderen Wallets:

- **Trust Wallet**: Settings → Wallets → [Wallet] → Show Recovery Phrase → Private Key
- **Coinbase Wallet**: Settings → Security → Show Private Key
- **Ledger/Hardware Wallet**: ❌ NICHT empfohlen für Bots!

---

## ⚙️ Bot konfigurieren

### In `.env` Datei:

```env
# Hyperliquid Configuration
HYPERLIQUID_WALLET_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
HYPERLIQUID_PRIVATE_KEY=0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
HYPERLIQUID_TESTNET=true
```

### Private Key Format:

- ✅ **Richtig**: `0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890` (66 Zeichen mit `0x`)
- ✅ **Auch OK**: `abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890` (64 Zeichen ohne `0x`)
- ❌ **Falsch**: Kürzer oder länger

### Wallet Address Format:

- ✅ **Richtig**: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb` (42 Zeichen mit `0x`)
- ❌ **Falsch**: Ohne `0x` oder andere Länge

---

## 🔒 Sicherheits-Checkliste

### ✅ Vor dem Start:

- [ ] Separates Trading-Wallet erstellt
- [ ] Nur Testnet-Funds (kein echtes Geld)
- [ ] Private Key in `.env` gespeichert
- [ ] `.env` ist in `.gitignore` (wird nicht committed)
- [ ] Kein Haupt-Wallet verwendet
- [ ] Private Key nirgendwo anders gespeichert

### 🚨 Niemals:

- ❌ Private Key teilen oder posten
- ❌ Private Key in Git committen
- ❌ Private Key per Email/Chat senden
- ❌ Haupt-Wallet für Bot nutzen
- ❌ Private Key auf Screenshots
- ❌ Mainnet ohne gründliches Testing

---

## 🧪 Testnet Setup

### 1. Verbinde Wallet mit Hyperliquid Testnet

```
URL: https://app.hyperliquid-testnet.xyz/
```

1. Öffne die URL
2. "Connect Wallet" klicken
3. MetaMask auswählen
4. Wallet verbinden
5. Netzwerk wechseln zu "Hyperliquid Testnet" (MetaMask fragt automatisch)

### 2. Testnet Funds bekommen

**Option A: Faucet**
```
https://testnet.hyperliquid.xyz/faucet
```
- Wallet Address eingeben
- "Request Funds" klicken
- Warte 1-2 Minuten

**Option B: Discord**
```
https://discord.gg/hyperliquid
```
- #testnet-faucet channel
- Poste deine Wallet Address
- Community/Bot gibt dir Funds

### 3. Verifiziere Funds

In MetaMask:
- Netzwerk: Hyperliquid Testnet
- Balance sollte sichtbar sein (z.B. 1000 USDC)

Oder auf Hyperliquid App:
- Gehe zu https://app.hyperliquid-testnet.xyz/
- Oben rechts: Dein Balance

---

## 🔧 Troubleshooting

### "Invalid private key format"

**Problem**: Private Key falsch formatiert

**Lösung**:
- Prüfe ob 64 Zeichen (ohne `0x`) oder 66 Zeichen (mit `0x`)
- Keine Leerzeichen
- Nur hexadezimale Zeichen (0-9, a-f)

```env
# Richtig:
HYPERLIQUID_PRIVATE_KEY=0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890

# Auch richtig:
HYPERLIQUID_PRIVATE_KEY=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890

# Falsch:
HYPERLIQUID_PRIVATE_KEY=0x abcdef...  # Leerzeichen!
HYPERLIQUID_PRIVATE_KEY=abcdef       # Zu kurz!
```

### "Wallet address mismatch"

**Problem**: Address in .env stimmt nicht mit Private Key überein

**Lösung**:
```python
# Prüfe welche Address zu deinem Private Key gehört:
python3 << 'EOF'
from eth_account import Account
private_key = "0xyour_private_key_here"
account = Account.from_key(private_key)
print(f"Correct address: {account.address}")
EOF
```

### "Insufficient balance"

**Problem**: Keine Funds im Wallet

**Lösung**:
1. Prüfe Balance auf https://app.hyperliquid-testnet.xyz/
2. Besorge Testnet Funds (siehe oben)
3. Warte ein paar Minuten nach Faucet-Request

### "Network error"

**Problem**: Bot kann nicht mit Hyperliquid verbinden

**Lösung**:
- Check Internet
- Prüfe ob Testnet erreichbar: https://app.hyperliquid-testnet.xyz/
- Firewall/VPN Einstellungen

---

## 📦 Dependencies installieren

Der Bot braucht zusätzliche Packages für Wallet-Authentifizierung:

```bash
source venv/bin/activate
pip install eth-account web3
```

Oder komplett neu:

```bash
pip install -r requirements.txt
```

---

## ✅ Verify Setup

### Test ob alles funktioniert:

```python
# test_wallet.py
from eth_account import Account
import os
from dotenv import load_dotenv

load_dotenv()

# Load from .env
private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
wallet_address = os.getenv("HYPERLIQUID_WALLET_ADDRESS")

# Create account from private key
account = Account.from_key(private_key)

print(f"✅ Private Key loaded")
print(f"📍 Configured Address: {wallet_address}")
print(f"📍 Derived Address:    {account.address}")

if account.address.lower() == wallet_address.lower():
    print("✅ Addresses match! Setup correct!")
else:
    print("❌ Addresses don't match! Check your .env")
```

Run:
```bash
python test_wallet.py
```

---

## 🚀 Ready to Start!

Wenn alles OK:

```bash
python run_bot.py
```

Du solltest sehen:
```
Initialized Hyperliquid client for wallet: 0x742d35Cc...
Hyperliquid API health check passed
Initial Portfolio: $1,000.00
Trading Assets: BTC, ETH, SOL
```

---

## 🔐 Security Best Practices

### Do's:
✅ Separates Trading-Wallet
✅ Nur Testnet-Funds
✅ `.env` in `.gitignore`
✅ Regelmäßig Private Key rotieren
✅ Bot auf sicherem Server laufen lassen

### Don'ts:
❌ Private Key teilen
❌ Haupt-Wallet nutzen
❌ Private Key committen
❌ Große Beträge auf Testnet
❌ Unverschlüsselte Backups

---

## 📚 Weiterführende Links

- **Hyperliquid Docs**: https://hyperliquid.gitbook.io/
- **Hyperliquid Discord**: https://discord.gg/hyperliquid
- **Testnet App**: https://app.hyperliquid-testnet.xyz/
- **eth-account Docs**: https://eth-account.readthedocs.io/

---

## 💬 Support

Bei Problemen:
1. Check dieses Guide nochmal
2. Prüfe Logs: `tail -f logs/trading_bot.log`
3. Frage im Hyperliquid Discord
4. Check GitHub Issues

**Wichtig**: Teile NIEMALS deinen Private Key!

---

**Happy Trading! 🚀**
