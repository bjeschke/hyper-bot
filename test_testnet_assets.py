"""Test script to check available assets on Hyperliquid TESTNET."""
import requests
import json

# Get all available assets from TESTNET
url = "https://api.hyperliquid-testnet.xyz/info"
data = {"type": "allMids"}

try:
    response = requests.post(url, json=data)
    assets = response.json()

    print("Available assets on Hyperliquid TESTNET:")
    print(f"Total assets: {len(assets)}")
    print()

    # Check for our assets
    our_assets = ["BTC", "ETH", "XRP", "TRUMP", "DOGE", "ENA", "SUI"]

    for asset in our_assets:
        if asset in assets:
            print(f"✅ {asset:10s} - Price: ${assets[asset]}")
        else:
            print(f"❌ {asset:10s} - NOT FOUND IN TESTNET")

    print()
    print("All XRP-related assets in testnet:")
    xrp_assets = {k: v for k, v in assets.items() if 'xrp' in k.lower()}
    for k, v in xrp_assets.items():
        print(f"  {k}: ${v}")
except Exception as e:
    print(f"Error: {e}")
