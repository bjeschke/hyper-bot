"""Test script to check available assets on Hyperliquid."""
import requests
import json

# Get all available assets
url = "https://api.hyperliquid.xyz/info"
data = {"type": "allMids"}

response = requests.post(url, json=data)
assets = response.json()

print("Available assets on Hyperliquid:")
print(f"Total assets: {len(assets)}")
print()

# Check for our assets
our_assets = ["BTC", "ETH", "XRP", "TRUMP", "DOGE", "ENA", "SUI"]

for asset in our_assets:
    if asset in assets:
        print(f"✅ {asset:10s} - Price: ${assets[asset]}")
    else:
        print(f"❌ {asset:10s} - NOT FOUND")
        # Try to find similar names
        similar = [a for a in assets.keys() if asset.lower() in a.lower()]
        if similar:
            print(f"   Similar: {similar}")

print()
print("All XRP-related assets:")
xrp_assets = {k: v for k, v in assets.items() if 'xrp' in k.lower()}
for k, v in xrp_assets.items():
    print(f"  {k}: ${v}")
